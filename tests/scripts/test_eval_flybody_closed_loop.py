import json
import importlib
import importlib.util
import sys
from pathlib import Path
import types
import datetime as real_datetime

import numpy as np


def _load_eval_flybody_closed_loop():
    module_name = "scripts.eval_flybody_closed_loop"
    script_path = Path(__file__).resolve().parents[2] / "scripts" / "eval_flybody_closed_loop.py"
    spec = importlib.util.spec_from_file_location(module_name, script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def test_eval_flybody_closed_loop_cli_writes_summary_and_video(tmp_path, monkeypatch, capsys) -> None:
    eval_flybody_closed_loop = _load_eval_flybody_closed_loop()

    class FakeTimestep:
        def __init__(self, reward=0.0, done=False):
            self.reward = reward
            self._done = done
            self.observation = {
                "walker/gyro": [0.0, 0.0, 0.1],
                "walker/velocimeter": [0.25, 0.0, 0.0],
                "walker/world_zaxis": [0.0, 0.0, 1.0],
            }

        def last(self):
            return self._done

    class FakePhysics:
        def render(self, **kwargs):
            return [[[0, 0, 0] for _ in range(2)] for _ in range(2)]

    class FakeEnv:
        physics = FakePhysics()

        def reset(self):
            return FakeTimestep()

        def step(self, action):
            return FakeTimestep(reward=1.0, done=True)

    class FakePolicy:
        def reset(self):
            return None

        def act(self, observation):
            return [0.1, 0.2]

        def activity_snapshot(self, *, top_k=20, include_node_activity=False):
            payload = {
                "afferent_activity": 0.1,
                "intrinsic_activity": 0.2,
                "efferent_activity": 0.3,
                "top_active_nodes": [
                    {"node_idx": 1, "activity_value": 0.4, "flow_role": "intrinsic"},
                ],
            }
            if include_node_activity:
                payload["node_activity"] = [0.1, 0.4]
            return payload

    monkeypatch.setattr(
        eval_flybody_closed_loop,
        "load_checkpoint_bundle",
        lambda **kwargs: object(),
    )
    monkeypatch.setattr(
        eval_flybody_closed_loop,
        "ClosedLoopPolicyWrapper",
        lambda bundle: FakePolicy(),
    )
    monkeypatch.setattr(
        eval_flybody_closed_loop,
        "_require_walk_imitation_env_factory",
        lambda: FakeEnv,
    )
    monkeypatch.setattr(
        eval_flybody_closed_loop,
        "_write_rollout_video",
        lambda *, output_path, frames, fps: Path(output_path).write_bytes(b"fake-mp4"),
    )

    exit_code = eval_flybody_closed_loop.main(
        [
            "--checkpoint",
            str(tmp_path / "epoch_0001.pt"),
            "--compiled-graph-dir",
            str(tmp_path / "compiled"),
            "--task",
            "straight_walking",
            "--max-steps",
            "4",
            "--save-video",
            "--output-dir",
            str(tmp_path / "eval"),
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["status"] == "ok"
    assert payload["task"] == "straight_walking"
    assert payload["reward_mean"] == 1.0
    assert payload["forward_velocity_mean"] == 0.25
    assert payload["forward_velocity_std"] == 0.0
    assert payload["body_upright_mean"] == 1.0
    assert payload["video_path"] == str(tmp_path / "eval" / "rollout.mp4")
    assert (tmp_path / "eval" / "summary.json").exists()
    assert (tmp_path / "eval" / "rollout.mp4").exists()
    assert (tmp_path / "eval" / "session.json").exists()
    assert (tmp_path / "eval" / "state_traces.npz").exists()
    assert (tmp_path / "eval" / "neural_traces.npz").exists()
    assert (tmp_path / "eval" / "events.jsonl").exists()
    session_payload = json.loads((tmp_path / "eval" / "session.json").read_text(encoding="utf-8"))
    assert session_payload["steps_completed"] == 1
    state_traces = np.load(tmp_path / "eval" / "state_traces.npz")
    neural_traces = np.load(tmp_path / "eval" / "neural_traces.npz")
    event_lines = (tmp_path / "eval" / "events.jsonl").read_text(encoding="utf-8").splitlines()
    event_payloads = [json.loads(line) for line in event_lines if line.strip()]
    assert state_traces["step_id"].tolist() == [1]
    assert neural_traces["step_id"].tolist() == [1]
    assert np.allclose(neural_traces["node_activity"], np.asarray([[0.1, 0.4]], dtype=np.float32))
    assert all("label" in event for event in event_payloads)


def test_eval_flybody_closed_loop_failure_preserves_summary(tmp_path, monkeypatch, capsys) -> None:
    eval_flybody_closed_loop = _load_eval_flybody_closed_loop()

    class FakeTimestep:
        def __init__(self):
            self.reward = 0.0
            self.observation = {"walker/gyro": [0.0, 0.0, 0.0]}

        def last(self):
            return False

    class FakeEnv:
        def reset(self):
            return FakeTimestep()

        def step(self, action):
            raise RuntimeError("step failed")

    class FakePolicy:
        def reset(self):
            return None

        def act(self, observation):
            return [0.1, 0.2]

        def activity_snapshot(self, *, top_k=20, include_node_activity=False):
            payload = {
                "afferent_activity": 0.1,
                "intrinsic_activity": 0.2,
                "efferent_activity": 0.3,
                "top_active_nodes": [],
            }
            if include_node_activity:
                payload["node_activity"] = [0.1, 0.2]
            return payload

    monkeypatch.setattr(
        eval_flybody_closed_loop,
        "load_checkpoint_bundle",
        lambda **kwargs: object(),
    )
    monkeypatch.setattr(
        eval_flybody_closed_loop,
        "ClosedLoopPolicyWrapper",
        lambda bundle: FakePolicy(),
    )
    monkeypatch.setattr(
        eval_flybody_closed_loop,
        "_require_walk_imitation_env_factory",
        lambda: FakeEnv,
    )

    exit_code = eval_flybody_closed_loop.main(
        [
            "--checkpoint",
            str(tmp_path / "epoch_0001.pt"),
            "--compiled-graph-dir",
            str(tmp_path / "compiled"),
            "--task",
            "straight_walking",
            "--max-steps",
            "4",
            "--output-dir",
            str(tmp_path / "eval"),
        ]
    )

    captured = capsys.readouterr()
    payload = json.loads(captured.out)

    assert exit_code == 0
    assert payload["status"] == "failed"
    assert payload["error"] == "step failed"
    assert (tmp_path / "eval" / "summary.json").exists()
    assert (tmp_path / "eval" / "session.json").exists()
    assert (tmp_path / "eval" / "state_traces.npz").exists()
    assert (tmp_path / "eval" / "neural_traces.npz").exists()
    assert (tmp_path / "eval" / "events.jsonl").exists()


def test_eval_flybody_closed_loop_imports_without_pyarrow(monkeypatch) -> None:
    original_import = __import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "pyarrow" or name.startswith("pyarrow."):
            raise ModuleNotFoundError("No module named 'pyarrow'")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.delitem(sys.modules, "scripts.eval_flybody_closed_loop", raising=False)
    monkeypatch.delitem(sys.modules, "fruitfly.evaluation", raising=False)
    monkeypatch.delitem(sys.modules, "pyarrow", raising=False)
    monkeypatch.delitem(sys.modules, "pyarrow.parquet", raising=False)
    monkeypatch.setattr("builtins.__import__", guarded_import)

    module = _load_eval_flybody_closed_loop()

    assert module.summarize_closed_loop_rollout is not None


def test_evaluation_package_exposes_rollout_summary_without_pyarrow(monkeypatch) -> None:
    original_import = __import__

    def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
        if name == "pyarrow" or name.startswith("pyarrow."):
            raise ModuleNotFoundError("No module named 'pyarrow'")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.delitem(sys.modules, "fruitfly.evaluation", raising=False)
    monkeypatch.delitem(sys.modules, "pyarrow", raising=False)
    monkeypatch.delitem(sys.modules, "pyarrow.parquet", raising=False)
    monkeypatch.setattr("builtins.__import__", guarded_import)

    from fruitfly.evaluation import summarize_closed_loop_rollout

    assert summarize_closed_loop_rollout is not None


def test_eval_flybody_closed_loop_imports_when_datetime_module_lacks_utc(monkeypatch) -> None:
    fake_datetime = types.ModuleType("datetime")
    fake_datetime.datetime = real_datetime.datetime
    fake_datetime.timezone = real_datetime.timezone

    monkeypatch.delitem(sys.modules, "scripts.eval_flybody_closed_loop", raising=False)
    monkeypatch.setitem(sys.modules, "datetime", fake_datetime)

    module = _load_eval_flybody_closed_loop()

    assert module.run_closed_loop_evaluation is not None
