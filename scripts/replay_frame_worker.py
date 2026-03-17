from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fruitfly.ui.replay_frame_worker import serve_replay_frame_requests


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run a resident replay frame worker for the neural console."
    )
    parser.add_argument(
        "--eval-dir",
        type=Path,
        required=True,
        help="Evaluation artifact directory",
    )
    args = parser.parse_args(argv)

    serve_replay_frame_requests(
        eval_dir=args.eval_dir,
        input_stream=sys.stdin.buffer,
        output_stream=sys.stdout.buffer,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
