from __future__ import annotations

import json
import subprocess
import threading
from pathlib import Path
from typing import Any, BinaryIO, Callable

from fruitfly.ui.mujoco_fly_official_render_backend import MujocoFlyOfficialRenderBackend


def _default_backend_factory(checkpoint_path: Path) -> Any:
    return MujocoFlyOfficialRenderBackend(checkpoint_path=checkpoint_path)


class MujocoFlyOfficialRenderWorkerClient:
    def __init__(self, *, process: Any) -> None:
        stdin = getattr(process, "stdin", None)
        stdout = getattr(process, "stdout", None)
        if stdin is None or stdout is None:
            raise ValueError("official render worker process must expose stdin and stdout pipes")

        self.process = process
        self._stdin = stdin
        self._stdout = stdout
        self._stderr = getattr(process, "stderr", None)
        self._lock = threading.Lock()
        self._closed = False

    @classmethod
    def launch(
        cls,
        *,
        python_executable: Path,
        worker_script: Path,
        checkpoint_path: Path,
    ) -> "MujocoFlyOfficialRenderWorkerClient":
        process = subprocess.Popen(
            [
                str(python_executable),
                str(worker_script),
                "--checkpoint-path",
                str(checkpoint_path),
            ],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
        )
        return cls(process=process)

    def start(self) -> None:
        self._request_control("start")

    def pause(self) -> None:
        self._request_control("pause")

    def reset(self) -> None:
        self._request_control("reset")

    def set_camera_preset(self, camera_id: str) -> None:
        self._request_control("camera", camera_id=str(camera_id))

    def render_frame(self, *, width: int, height: int, camera_id: str) -> bytes:
        header = self._request(
            {
                "command": "render",
                "width": int(width),
                "height": int(height),
                "camera_id": str(camera_id),
            }
        )
        byte_length = int(header.get("byte_length", 0))
        if byte_length < 0:
            raise RuntimeError("official render worker returned an invalid payload length")
        payload = _read_exact(self._stdout, byte_length)
        if len(payload) != byte_length:
            raise RuntimeError("official render worker returned a truncated payload")
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

    def _request_control(self, command: str, **payload: Any) -> None:
        self._request({"command": command, **payload})

    def _request(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            self._ensure_running()
            self._stdin.write(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
            self._stdin.write(b"\n")
            self._stdin.flush()
            header = _read_header(self._stdout)
            if not header.get("ok", False):
                raise RuntimeError(str(header.get("error") or "official render request failed"))
            return header

    def _ensure_running(self) -> None:
        if self._closed:
            raise RuntimeError("official render worker client is closed")
        return_code = self.process.poll()
        if return_code is None:
            return
        stderr_message = _read_stderr(self._stderr)
        if stderr_message:
            raise RuntimeError(
                f"official render worker exited with code {return_code}: {stderr_message}"
            )
        raise RuntimeError(f"official render worker exited with code {return_code}")


def serve_mujoco_fly_official_render_requests(
    *,
    checkpoint_path: Path,
    input_stream: BinaryIO,
    output_stream: BinaryIO,
    backend_factory: Callable[[Path], Any] | None = None,
) -> int:
    backend = (backend_factory or _default_backend_factory)(checkpoint_path)
    served_requests = 0

    while True:
        raw_line = input_stream.readline()
        if raw_line == b"":
            break
        if not raw_line.strip():
            continue

        try:
            request = json.loads(raw_line.decode("utf-8"))
            command = str(request["command"])

            if command == "start":
                backend.start()
                _write_header(output_stream, {"ok": True})
            elif command == "pause":
                backend.pause()
                _write_header(output_stream, {"ok": True})
            elif command == "reset":
                backend.reset()
                _write_header(output_stream, {"ok": True})
            elif command == "camera":
                backend.set_camera_preset(str(request["camera_id"]))
                _write_header(output_stream, {"ok": True})
            elif command == "render":
                payload = bytes(
                    backend.render_frame(
                        width=int(request["width"]),
                        height=int(request["height"]),
                        camera_id=str(request["camera_id"]),
                    )
                )
                _write_header(
                    output_stream,
                    {
                        "ok": True,
                        "content_type": "image/jpeg",
                        "byte_length": len(payload),
                    },
                )
                output_stream.write(payload)
                output_stream.flush()
            else:
                raise ValueError(f"Unsupported official render command: {command}")
            served_requests += 1
        except Exception as exc:
            _write_header(output_stream, {"ok": False, "error": str(exc)})

    close = getattr(backend, "close", None)
    if callable(close):
        close()
    return served_requests


def _write_header(stream: BinaryIO, payload: dict[str, Any]) -> None:
    stream.write(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    stream.write(b"\n")
    stream.flush()


def _read_header(stream: BinaryIO) -> dict[str, Any]:
    raw_line = stream.readline()
    if raw_line == b"":
        raise RuntimeError("official render worker closed its stdout unexpectedly")
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
