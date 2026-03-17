from __future__ import annotations

import io
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from fruitfly.ui.replay_frame_worker import ReplayFrameWorkerClient, serve_replay_frame_requests


class _WritableBytesIO(io.BytesIO):
    def flush(self) -> None:  # pragma: no cover - BytesIO has no side effects
        return None


class _FakeProcess:
    def __init__(self, *, stdout_payload: bytes) -> None:
        self.stdin = _WritableBytesIO()
        self.stdout = io.BytesIO(stdout_payload)
        self.stderr = io.BytesIO()
        self.terminated = False
        self.wait_called = False

    def poll(self) -> int | None:
        return None

    def terminate(self) -> None:
        self.terminated = True

    def wait(self, timeout: float | None = None) -> int:
        self.wait_called = True
        return 0

    def kill(self) -> None:  # pragma: no cover - not needed in the happy path test
        self.terminated = True


def test_replay_frame_worker_client_round_trips_one_render_request() -> None:
    jpeg_bytes = b"\xff\xd8fake-jpeg\xff\xd9"
    header = json.dumps(
        {"ok": True, "content_type": "image/jpeg", "byte_length": len(jpeg_bytes)}
    ).encode("utf-8") + b"\n"
    process = _FakeProcess(stdout_payload=header + jpeg_bytes)

    client = ReplayFrameWorkerClient(process=process)

    result = client.render_frame(step=2, camera="top", width=320, height=240)

    assert result == jpeg_bytes
    request_payload = json.loads(process.stdin.getvalue().decode("utf-8").strip())
    assert request_payload == {
        "step": 2,
        "camera": "top",
        "width": 320,
        "height": 240,
    }


def test_replay_frame_worker_client_raises_on_worker_error() -> None:
    header = json.dumps({"ok": False, "error": "renderer failed"}).encode("utf-8") + b"\n"
    process = _FakeProcess(stdout_payload=header)

    client = ReplayFrameWorkerClient(process=process)

    with pytest.raises(RuntimeError, match="renderer failed"):
        client.render_frame(step=1, camera="follow", width=320, height=240)


def test_replay_frame_worker_server_reuses_one_renderer_instance() -> None:
    created_renderers: list[FakeRenderer] = []

    class FakeRenderer:
        def __init__(self) -> None:
            self.calls: list[tuple[int, str, int, int]] = []
            self.render_width = 0
            self.render_height = 0

        def render_frame(self, *, step: int, camera: str):
            self.calls.append((step, camera, self.render_width, self.render_height))
            payload = f"frame:{step}:{camera}:{self.render_width}:{self.render_height}".encode("utf-8")
            return SimpleNamespace(bytes=payload, content_type="image/jpeg")

    def fake_renderer_factory(eval_dir: Path, *, render_width: int, render_height: int):
        renderer = FakeRenderer()
        renderer.render_width = render_width
        renderer.render_height = render_height
        created_renderers.append(renderer)
        return renderer

    input_stream = io.BytesIO(
        b'{"step":1,"camera":"follow","width":320,"height":240}\n'
        b'{"step":2,"camera":"top","width":640,"height":360}\n'
    )
    output_stream = io.BytesIO()

    served = serve_replay_frame_requests(
        eval_dir=Path("/tmp/eval"),
        input_stream=input_stream,
        output_stream=output_stream,
        renderer_factory=fake_renderer_factory,
    )

    assert served == 2
    assert len(created_renderers) == 1
    assert created_renderers[0].calls == [
        (1, "follow", 320, 240),
        (2, "top", 640, 360),
    ]
