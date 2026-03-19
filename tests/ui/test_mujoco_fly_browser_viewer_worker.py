from __future__ import annotations

import io
import json
from typing import Any


class _FakeWorkerBackend:
    def __init__(self) -> None:
        self.started = False
        self.paused = False
        self.reset_called = False
        self.snapshots = 0

    def start(self) -> None:
        self.started = True
        self.paused = False

    def pause(self) -> None:
        self.paused = True

    def reset(self) -> None:
        self.reset_called = True
        self.paused = True

    def current_viewer_state(self) -> dict[str, object]:
        self.snapshots += 1
        return {
            "frame_id": self.snapshots,
            "sim_time": 0.1 * self.snapshots,
            "running_state": "running" if self.started and not self.paused else "paused",
            "current_camera": "track",
            "scene_version": "flybody-walk-imitation-v1",
            "body_poses": [
                {
                    "body_name": "walker/thorax",
                    "position": [0.0, 0.0, 0.1278],
                    "quaternion": [1.0, 0.0, 0.0, 0.0],
                }
            ],
        }


def _build_stream(*payloads: dict[str, Any]) -> io.BytesIO:
    content = b"".join(
        json.dumps(payload, separators=(",", ":")).encode("utf-8") + b"\n" for payload in payloads
    )
    return io.BytesIO(content)


def test_browser_viewer_worker_serves_control_and_snapshot_commands(tmp_path) -> None:
    from fruitfly.ui.mujoco_fly_browser_viewer_worker import serve_mujoco_fly_browser_viewer_requests

    backend = _FakeWorkerBackend()
    input_stream = _build_stream(
        {"command": "snapshot"},
        {"command": "start"},
        {"command": "snapshot"},
        {"command": "pause"},
        {"command": "reset"},
    )
    output_stream = io.BytesIO()

    served = serve_mujoco_fly_browser_viewer_requests(
        checkpoint_path=tmp_path / "walking",
        input_stream=input_stream,
        output_stream=output_stream,
        backend_factory=lambda _path: backend,
    )

    lines = output_stream.getvalue().splitlines()

    assert served == 5
    assert backend.started is True
    assert backend.paused is True
    assert backend.reset_called is True
    first_snapshot = json.loads(lines[0])
    second_snapshot = json.loads(lines[2])
    assert first_snapshot["ok"] is True
    assert first_snapshot["payload"]["running_state"] == "paused"
    assert second_snapshot["payload"]["running_state"] == "running"
