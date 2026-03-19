from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fruitfly.ui.mujoco_fly_official_render_worker import serve_mujoco_fly_official_render_requests


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Run a resident official MuJoCo fly render worker for the neural console."
    )
    parser.add_argument(
        "--checkpoint-path",
        type=Path,
        required=True,
        help="Official flybody walking policy checkpoint directory",
    )
    args = parser.parse_args(argv)

    serve_mujoco_fly_official_render_requests(
        checkpoint_path=args.checkpoint_path,
        input_stream=sys.stdin.buffer,
        output_stream=sys.stdout.buffer,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
