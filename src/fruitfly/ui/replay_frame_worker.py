from __future__ import annotations

import json
import subprocess
import threading
from pathlib import Path
from typing import Any, BinaryIO, Callable


def _default_renderer_factory(eval_dir: Path, *, render_width: int, render_height: int) -> Any:
    from fruitfly.evaluation.replay_renderer import ReplayRenderer

    return ReplayRenderer.from_eval_dir(
        eval_dir,
        render_width=render_width,
        render_height=render_height,
    )


class ReplayFrameWorkerClient:
    def __init__(self, *, process: Any) -> None:
        stdin = getattr(process, "stdin", None)
        stdout = getattr(process, "stdout", None)
        if stdin is None or stdout is None:
            raise ValueError("replay frame worker process must expose stdin and stdout pipes")

        self.process = process
        self._stdin = stdin
        self._stdout = stdout
        self._stderr = getattr(process, "stderr", None)
        self._lock = threading.Lock()
        self._closed = False

    @classmethod
    def start(
        cls,
        *,
        python_executable: Path,
        worker_script: Path,
        eval_dir: Path,
    ) -> "ReplayFrameWorkerClient":
        process = subprocess.Popen(
            [
                str(python_executable),
                str(worker_script),
                "--eval-dir",
                str(eval_dir),
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
        )
        return cls(process=process)

    def render_frame(self, *, step: int, camera: str, width: int, height: int) -> bytes:
        request_payload = {
            "step": int(step),
            "camera": str(camera),
            "width": int(width),
            "height": int(height),
        }

        with self._lock:
            self._ensure_running()
            self._stdin.write(json.dumps(request_payload, separators=(",", ":")).encode("utf-8"))
            self._stdin.write(b"\n")
            self._stdin.flush()

            header = _read_header(self._stdout)
            if not header.get("ok", False):
                raise RuntimeError(str(header.get("error") or "replay frame rendering failed"))

            byte_length = int(header.get("byte_length", 0))
            if byte_length < 0:
                raise RuntimeError("replay frame worker returned an invalid payload length")

            payload = _read_exact(self._stdout, byte_length)
            if len(payload) != byte_length:
                raise RuntimeError("replay frame worker returned a truncated payload")
            return payload

    def close(self) -> None:
        with self._lock:
            if self._closed:
                return
            self._closed = True
            try:
                if not self._stdin.closed:
                    self._stdin.close()
            except Exception:
                pass

            if self.process.poll() is None:
                self.process.terminate()
                try:
                    self.process.wait(timeout=2)
                except Exception:
                    self.process.kill()
                    self.process.wait(timeout=2)

    def _ensure_running(self) -> None:
        if self._closed:
            raise RuntimeError("replay frame worker client is closed")

        return_code = self.process.poll()
        if return_code is None:
            return

        stderr_message = _read_stderr(self._stderr)
        if stderr_message:
            raise RuntimeError(
                f"replay frame worker exited with code {return_code}: {stderr_message}"
            )
        raise RuntimeError(f"replay frame worker exited with code {return_code}")


def serve_replay_frame_requests(
    *,
    eval_dir: Path,
    input_stream: BinaryIO,
    output_stream: BinaryIO,
    renderer_factory: Callable[..., Any] | None = None,
) -> int:
    renderer = (renderer_factory or _default_renderer_factory)(
        eval_dir,
        render_width=320,
        render_height=240,
    )
    served_requests = 0

    while True:
        raw_line = input_stream.readline()
        if raw_line == b"":
            break
        if not raw_line.strip():
            continue

        try:
            request = json.loads(raw_line.decode("utf-8"))
            step = int(request["step"])
            camera = str(request["camera"])
            width = int(request["width"])
            height = int(request["height"])

            renderer.render_width = width
            renderer.render_height = height
            rendered = renderer.render_frame(step=step, camera=camera)
            payload = bytes(getattr(rendered, "bytes"))
            content_type = str(getattr(rendered, "content_type", "image/jpeg"))
            _write_header(
                output_stream,
                {
                    "ok": True,
                    "content_type": content_type,
                    "byte_length": len(payload),
                },
            )
            output_stream.write(payload)
            output_stream.flush()
            served_requests += 1
        except Exception as exc:
            _write_header(output_stream, {"ok": False, "error": str(exc)})

    return served_requests


def _write_header(stream: BinaryIO, payload: dict[str, Any]) -> None:
    stream.write(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    stream.write(b"\n")
    stream.flush()


def _read_header(stream: BinaryIO) -> dict[str, Any]:
    raw_line = stream.readline()
    if raw_line == b"":
        raise RuntimeError("replay frame worker closed its stdout unexpectedly")
    return json.loads(raw_line.decode("utf-8"))


def _read_exact(stream: BinaryIO, byte_length: int) -> bytes:
    remaining = byte_length
    chunks: list[bytes] = []
    while remaining > 0:
        chunk = stream.read(remaining)
        if not chunk:
            break
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


def _read_stderr(stderr_stream: Any) -> str:
    if stderr_stream is None:
        return ""
    try:
        payload = stderr_stream.read()
    except Exception:
        return ""
    if not payload:
        return ""
    if isinstance(payload, bytes):
        return payload.decode("utf-8", errors="ignore").strip()
    return str(payload).strip()
