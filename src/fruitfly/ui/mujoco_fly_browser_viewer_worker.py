from __future__ import annotations

import json
import subprocess
import threading
from pathlib import Path
from typing import Any, BinaryIO, Callable

from fruitfly.ui.mujoco_fly_browser_viewer_backend import MujocoFlyBrowserViewerBackend


def _default_backend_factory(checkpoint_path: Path | None) -> Any:
    return MujocoFlyBrowserViewerBackend(checkpoint_path=checkpoint_path)


class MujocoFlyBrowserViewerWorkerClient:
    def __init__(self, *, process: Any) -> None:
        stdin = getattr(process, "stdin", None)
        stdout = getattr(process, "stdout", None)
        if stdin is None or stdout is None:
            raise ValueError("browser viewer worker process must expose stdin and stdout pipes")

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
        checkpoint_path: Path | None,
    ) -> "MujocoFlyBrowserViewerWorkerClient":
        command = [
            str(python_executable),
            str(worker_script),
        ]
        if checkpoint_path is not None:
            command.extend(["--checkpoint-path", str(checkpoint_path)])
        process = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0,
        )
        return cls(process=process)

    def start(self) -> None:
        self._request({"command": "start"})

    def pause(self) -> None:
        self._request({"command": "pause"})

    def reset(self) -> None:
        self._request({"command": "reset"})

    def current_viewer_state(self) -> dict[str, Any]:
        header = self._request({"command": "snapshot"})
        payload = header.get("payload")
        if not isinstance(payload, dict):
            raise RuntimeError("browser viewer worker returned an invalid snapshot payload")
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

    def _request(self, payload: dict[str, Any]) -> dict[str, Any]:
        with self._lock:
            self._ensure_running()
            self._stdin.write(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
            self._stdin.write(b"\n")
            self._stdin.flush()
            header = _read_header(self._stdout)
            if not header.get("ok", False):
                raise RuntimeError(str(header.get("error") or "browser viewer worker request failed"))
            return header

    def _ensure_running(self) -> None:
        if self._closed:
            raise RuntimeError("browser viewer worker client is closed")
        return_code = self.process.poll()
        if return_code is None:
            return
        stderr_message = _read_stderr(self._stderr)
        if stderr_message:
            raise RuntimeError(
                f"browser viewer worker exited with code {return_code}: {stderr_message}"
            )
        raise RuntimeError(f"browser viewer worker exited with code {return_code}")


def serve_mujoco_fly_browser_viewer_requests(
    *,
    checkpoint_path: Path | None,
    input_stream: BinaryIO,
    output_stream: BinaryIO,
    backend_factory: Callable[[Path | None], Any] | None = None,
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
            elif command == "snapshot":
                _write_header(
                    output_stream,
                    {
                        "ok": True,
                        "payload": backend.current_viewer_state(),
                    },
                )
            else:
                raise ValueError(f"Unsupported browser viewer command: {command}")
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
        raise RuntimeError("browser viewer worker closed its stdout unexpectedly")
    return json.loads(raw_line.decode("utf-8"))


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
