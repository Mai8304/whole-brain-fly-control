from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import math
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import numpy as np

from fruitfly.evaluation.checkpoint_loader import load_checkpoint_bundle
from fruitfly.evaluation.inspector_trace import dump_replay_trace
from fruitfly.evaluation.policy_wrapper import ClosedLoopPolicyWrapper
from fruitfly.evaluation.walking_eval import summarize_closed_loop_rollout


def run_closed_loop_evaluation(
    *,
    checkpoint: Path,
    compiled_graph_dir: Path,
    task: str,
    max_steps: int,
    output_dir: Path,
    save_video: bool = False,
    render_width: int = 320,
    render_height: int = 240,
    render_fps: int = 8,
    env_factory: object | None = None,
    checkpoint_loader: object | None = None,
) -> dict[str, Any]:
    if task != "straight_walking":
        raise ValueError(f"Unsupported closed-loop evaluation task: {task}")

    loader = checkpoint_loader or load_checkpoint_bundle
    bundle = loader(checkpoint_path=checkpoint, compiled_graph_dir=compiled_graph_dir)
    policy = ClosedLoopPolicyWrapper(bundle=bundle)
    environment = (env_factory or _require_walk_imitation_env_factory())()

    output_dir.mkdir(parents=True, exist_ok=True)

    rewards: list[float] = []
    actions: list[list[float]] = []
    activity_snapshots: list[dict[str, Any]] = []
    trace_step_ids: list[int] = []
    sim_time_trace: list[float] = []
    qpos_trace: list[np.ndarray] = []
    qvel_trace: list[np.ndarray] = []
    ctrl_trace: list[np.ndarray] = []
    reward_trace: list[float] = []
    terminated_trace: list[bool] = []
    neural_step_ids: list[int] = []
    node_activity_trace: list[np.ndarray] = []
    afferent_activity_trace: list[float] = []
    intrinsic_activity_trace: list[float] = []
    efferent_activity_trace: list[float] = []
    replay_events: list[dict[str, Any]] = [
        {
            "step_id": 0,
            "event_type": "rollout_started",
            "label": "Recorded rollout start",
        }
    ]
    heading_trace = [0.0]
    forward_velocity_trace: list[float] = []
    upright_trace: list[float] = []
    video_frames: list[np.ndarray] = []
    cumulative_heading = 0.0
    terminated_early = False

    try:
        timestep = environment.reset()
        policy.reset()
        _append_render_frame(
            environment=environment,
            frames=video_frames,
            width=render_width,
            height=render_height,
            enabled=save_video,
        )
        for _ in range(max_steps):
            action = policy.act(timestep.observation)
            actions.append(action)
            step_id = len(actions)
            activity_snapshot = policy.activity_snapshot(top_k=5, include_node_activity=True)
            activity_snapshots.append(
                {
                    "step_id": step_id,
                    "afferent_activity": float(activity_snapshot["afferent_activity"]),
                    "intrinsic_activity": float(activity_snapshot["intrinsic_activity"]),
                    "efferent_activity": float(activity_snapshot["efferent_activity"]),
                    "top_active_nodes": [
                        {
                            "node_idx": int(node["node_idx"]),
                            "activity_value": float(node["activity_value"]),
                            "flow_role": str(node["flow_role"]),
                        }
                        for node in activity_snapshot["top_active_nodes"]
                    ],
                }
            )
            neural_step_ids.append(step_id)
            node_activity_trace.append(
                np.asarray(activity_snapshot.get("node_activity") or [], dtype=np.float32)
            )
            afferent_activity_trace.append(float(activity_snapshot["afferent_activity"]))
            intrinsic_activity_trace.append(float(activity_snapshot["intrinsic_activity"]))
            efferent_activity_trace.append(float(activity_snapshot["efferent_activity"]))
            if any(not math.isfinite(value) for value in action):
                terminated_early = True
                break
            timestep = environment.step(np.asarray(action, dtype=float))
            observation = getattr(timestep, "observation")
            reward = float(getattr(timestep, "reward", 0.0) or 0.0)
            terminal = _is_terminal_timestep(timestep)
            rewards.append(reward)
            cumulative_heading += _extract_heading_increment(observation)
            heading_trace.append(cumulative_heading)
            forward_velocity_trace.append(_extract_forward_velocity(observation))
            upright_trace.append(_extract_body_upright(observation))
            trace_step_ids.append(step_id)
            sim_time_trace.append(_extract_sim_time(environment=environment, step_id=step_id))
            qpos_trace.append(_extract_physics_array(environment=environment, attr_name="qpos"))
            qvel_trace.append(_extract_physics_array(environment=environment, attr_name="qvel"))
            ctrl_trace.append(_extract_control_array(environment=environment, action=action))
            reward_trace.append(reward)
            terminated_trace.append(terminal)
            _append_render_frame(
                environment=environment,
                frames=video_frames,
                width=render_width,
                height=render_height,
                enabled=save_video,
            )
            if terminal:
                terminated_early = True
                break
        summary = summarize_closed_loop_rollout(
            task=task,
            checkpoint=str(checkpoint),
            steps_requested=max_steps,
            steps_completed=len(actions),
            terminated_early=terminated_early,
            actions=actions,
            rewards=rewards,
            heading_trace=heading_trace,
            forward_velocity_trace=forward_velocity_trace,
            upright_trace=upright_trace,
        )
    except Exception as exc:  # noqa: BLE001
        summary = summarize_closed_loop_rollout(
            task=task,
            checkpoint=str(checkpoint),
            steps_requested=max_steps,
            steps_completed=len(actions),
            terminated_early=True,
            actions=actions,
            rewards=rewards,
            heading_trace=heading_trace,
            forward_velocity_trace=forward_velocity_trace,
            upright_trace=upright_trace,
            error=str(exc),
        )

    if terminated_early:
        replay_events.append(
            {
                "step_id": len(actions),
                "event_type": "terminated_early",
                "label": "Recorded early termination",
            }
        )
    replay_events.append(
        {
            "step_id": len(actions),
            "event_type": "rollout_completed",
            "label": "Recorded rollout complete",
        }
    )

    if save_video:
        video_path = output_dir / "rollout.mp4"
        try:
            _write_rollout_video(
                output_path=video_path,
                frames=video_frames,
                fps=render_fps,
            )
            summary["video_path"] = str(video_path)
        except Exception as exc:  # noqa: BLE001
            summary["video_error"] = str(exc)

    state_arrays = {
        "step_id": np.asarray(trace_step_ids, dtype=np.int64),
        "sim_time": np.asarray(sim_time_trace, dtype=np.float64),
        "qpos": _stack_trace_rows(qpos_trace, dtype=np.float64),
        "qvel": _stack_trace_rows(qvel_trace, dtype=np.float64),
        "ctrl": _stack_trace_rows(ctrl_trace, dtype=np.float64),
        "reward": np.asarray(reward_trace, dtype=np.float64),
        "terminated": np.asarray(terminated_trace, dtype=bool),
        "body_upright": np.asarray(upright_trace, dtype=np.float64),
        "forward_velocity": np.asarray(forward_velocity_trace, dtype=np.float64),
    }
    neural_arrays = {
        "step_id": np.asarray(neural_step_ids, dtype=np.int64),
        "node_activity": _stack_trace_rows(node_activity_trace, dtype=np.float32),
        "afferent_activity": np.asarray(afferent_activity_trace, dtype=np.float32),
        "intrinsic_activity": np.asarray(intrinsic_activity_trace, dtype=np.float32),
        "efferent_activity": np.asarray(efferent_activity_trace, dtype=np.float32),
    }
    session_payload = {
        "session_id": output_dir.name,
        "task": task,
        "checkpoint": str(checkpoint),
        "compiled_graph_dir": str(compiled_graph_dir),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "default_camera": "follow",
        "steps_requested": int(max_steps),
        "steps_completed": int(len(actions)),
        "terminated_early": bool(terminated_early),
        "quality": "artifact",
    }
    dump_replay_trace(
        output_dir=output_dir,
        session=session_payload,
        state_arrays=state_arrays,
        neural_arrays=neural_arrays,
        events=replay_events,
    )

    _write_activity_trace(
        output_dir=output_dir,
        task=task,
        steps_requested=max_steps,
        steps_completed=len(actions),
        terminated_early=terminated_early,
        snapshots=activity_snapshots,
    )
    _write_final_node_activity(
        output_dir=output_dir,
        node_activity=node_activity_trace[-1].tolist() if node_activity_trace else [],
    )
    (output_dir / "summary.json").write_text(
        json.dumps(summary, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run a flybody closed-loop checkpoint evaluation.")
    parser.add_argument("--checkpoint", type=Path, required=True, help="Path to the trained checkpoint")
    parser.add_argument("--compiled-graph-dir", type=Path, required=True, help="Compiled graph artifact directory")
    parser.add_argument("--task", default="straight_walking", help="Evaluation task name")
    parser.add_argument("--max-steps", type=int, default=64, help="Maximum rollout steps")
    parser.add_argument("--output-dir", type=Path, required=True, help="Output directory for evaluation artifacts")
    parser.add_argument("--save-video", action="store_true", help="Save rollout.mp4 alongside summary.json")
    parser.add_argument("--render-width", type=int, default=320, help="Rendered video width")
    parser.add_argument("--render-height", type=int, default=240, help="Rendered video height")
    parser.add_argument("--render-fps", type=int, default=8, help="Rendered video FPS")
    args = parser.parse_args(argv)

    try:
        summary = run_closed_loop_evaluation(
            checkpoint=args.checkpoint,
            compiled_graph_dir=args.compiled_graph_dir,
            task=args.task,
            max_steps=args.max_steps,
            output_dir=args.output_dir,
            save_video=args.save_video,
            render_width=args.render_width,
            render_height=args.render_height,
            render_fps=args.render_fps,
        )
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    print(json.dumps(summary))
    return 0


def _require_walk_imitation_env_factory() -> object:
    try:
        from flybody.fly_envs import walk_imitation
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "flybody is not installed in the current environment. Run closed-loop evaluation from the dedicated flybody environment."
        ) from exc
    return walk_imitation


def _extract_heading_increment(observation: Any) -> float:
    gyro = observation.get("walker/gyro") if hasattr(observation, "get") else None
    if gyro is None:
        return 0.0
    values = gyro.tolist() if hasattr(gyro, "tolist") else list(gyro)
    if len(values) < 3:
        return 0.0
    return float(values[2])


def _is_terminal_timestep(timestep: Any) -> bool:
    last = getattr(timestep, "last", None)
    if callable(last):
        return bool(last())
    return False


def _extract_forward_velocity(observation: Any) -> float:
    velocimeter = observation.get("walker/velocimeter") if hasattr(observation, "get") else None
    if velocimeter is None:
        return 0.0
    values = velocimeter.tolist() if hasattr(velocimeter, "tolist") else list(velocimeter)
    if not values:
        return 0.0
    return float(values[0])


def _extract_body_upright(observation: Any) -> float:
    world_zaxis = observation.get("walker/world_zaxis") if hasattr(observation, "get") else None
    if world_zaxis is None:
        return 0.0
    values = world_zaxis.tolist() if hasattr(world_zaxis, "tolist") else list(world_zaxis)
    if len(values) < 3:
        return 0.0
    return float(values[2])


def _extract_sim_time(*, environment: Any, step_id: int) -> float:
    physics_data = _physics_data(environment)
    if physics_data is None:
        return float(step_id)
    value = getattr(physics_data, "time", None)
    if value is None:
        return float(step_id)
    return float(value)


def _extract_physics_array(*, environment: Any, attr_name: str) -> np.ndarray:
    physics_data = _physics_data(environment)
    if physics_data is None:
        return np.zeros((0,), dtype=np.float64)
    value = getattr(physics_data, attr_name, None)
    if value is None:
        return np.zeros((0,), dtype=np.float64)
    return np.asarray(value, dtype=np.float64).reshape(-1)


def _extract_control_array(*, environment: Any, action: list[float]) -> np.ndarray:
    physics_data = _physics_data(environment)
    if physics_data is not None:
        value = getattr(physics_data, "ctrl", None)
        if value is not None:
            return np.asarray(value, dtype=np.float64).reshape(-1)
    return np.asarray(action, dtype=np.float64).reshape(-1)


def _physics_data(environment: Any) -> Any | None:
    physics = getattr(environment, "physics", None)
    if physics is None:
        return None
    return getattr(physics, "data", None)


def _stack_trace_rows(rows: list[np.ndarray], *, dtype: np.dtype[Any]) -> np.ndarray:
    if not rows:
        return np.zeros((0, 0), dtype=dtype)
    return np.stack([np.asarray(row, dtype=dtype) for row in rows], axis=0)


def _append_render_frame(
    *,
    environment: Any,
    frames: list[np.ndarray],
    width: int,
    height: int,
    enabled: bool,
) -> None:
    if not enabled:
        return
    physics = getattr(environment, "physics", None)
    render = getattr(physics, "render", None)
    if not callable(render):
        return
    frame = render(width=width, height=height)
    frames.append(np.asarray(frame, dtype=np.uint8))


def _write_rollout_video(*, output_path: Path, frames: list[np.ndarray], fps: int) -> None:
    if not frames:
        raise ValueError("No rollout frames were captured.")
    try:
        import imageio_ffmpeg
    except ModuleNotFoundError:
        imageio_ffmpeg = None

    if imageio_ffmpeg is not None:
        height, width = frames[0].shape[:2]
        writer = imageio_ffmpeg.write_frames(
            str(output_path),
            (width, height),
            fps=fps,
            pix_fmt_in="rgb24",
        )
        writer.send(None)
        try:
            for frame in frames:
                writer.send(np.ascontiguousarray(frame, dtype=np.uint8))
        finally:
            writer.close()
        return

    import mediapy as media

    media.write_video(output_path, frames, fps=fps)


def _write_activity_trace(
    *,
    output_dir: Path,
    task: str,
    steps_requested: int,
    steps_completed: int,
    terminated_early: bool,
    snapshots: list[dict[str, Any]],
) -> None:
    payload = {
        "task": task,
        "steps_requested": int(steps_requested),
        "steps_completed": int(steps_completed),
        "terminated_early": bool(terminated_early),
        "snapshots": snapshots,
    }
    (output_dir / "activity_trace.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )


def _write_final_node_activity(*, output_dir: Path, node_activity: Any) -> None:
    values = node_activity if isinstance(node_activity, list) else []
    np.save(output_dir / "final_node_activity.npy", np.asarray(values, dtype=np.float32))


if __name__ == "__main__":
    raise SystemExit(main())
