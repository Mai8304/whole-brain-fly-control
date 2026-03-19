from __future__ import annotations

import io
import json
from typing import Any


class _FakeWorkerBackend:
    def __init__(self) -> None:
        self.started = False
        self.paused = False
        self.reset_called = False
        self.camera_id = "walker/track1"

    def start(self) -> None:
        self.started = True
        self.paused = False

    def pause(self) -> None:
        self.paused = True

    def reset(self) -> None:
        self.reset_called = True
        self.paused = True

    def set_camera_preset(self, camera_id: str) -> None:
        self.camera_id = camera_id

    def render_frame(self, *, width: int, height: int, camera_id: str) -> bytes:
        return f"{camera_id}:{width}x{height}".encode("utf-8")


def _build_stream(*payloads: dict[str, Any]) -> io.BytesIO:
    content = b"".join(json.dumps(payload, separators=(",", ":")).encode("utf-8") + b"\n" for payload in payloads)
    return io.BytesIO(content)


def test_official_render_worker_serves_control_and_frame_commands(tmp_path) -> None:
    from fruitfly.ui.mujoco_fly_official_render_worker import serve_mujoco_fly_official_render_requests

    backend = _FakeWorkerBackend()
    input_stream = _build_stream(
        {"command": "start"},
        {"command": "camera", "camera_id": "walker/side"},
        {"command": "render", "width": 320, "height": 240, "camera_id": "walker/side"},
        {"command": "pause"},
        {"command": "reset"},
    )
    output_stream = io.BytesIO()

    served = serve_mujoco_fly_official_render_requests(
        checkpoint_path=tmp_path / "walking",
        input_stream=input_stream,
        output_stream=output_stream,
        backend_factory=lambda _path: backend,
    )

    payload = output_stream.getvalue()
    lines = payload.splitlines()

    assert served == 5
    assert backend.started is True
    assert backend.paused is True
    assert backend.reset_called is True
    assert backend.camera_id == "walker/side"
    assert json.loads(lines[0]) == {"ok": True}
    assert json.loads(lines[1]) == {"ok": True}
    frame_header = json.loads(lines[2])
    assert frame_header["ok"] is True
    assert frame_header["content_type"] == "image/jpeg"
    assert frame_header["byte_length"] == len(b"walker/side:320x240")
