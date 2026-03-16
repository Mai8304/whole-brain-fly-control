from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fruitfly.evaluation.replay_renderer import ReplayRenderer


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Render one replay frame from saved flybody rollout state.")
    parser.add_argument("--eval-dir", type=Path, required=True, help="Evaluation artifact directory")
    parser.add_argument("--step", type=int, required=True, help="Replay step id")
    parser.add_argument("--camera", required=True, help="Replay camera preset")
    parser.add_argument("--width", type=int, default=320, help="Rendered frame width")
    parser.add_argument("--height", type=int, default=240, help="Rendered frame height")
    args = parser.parse_args(argv)

    renderer = ReplayRenderer.from_eval_dir(
        args.eval_dir,
        render_width=args.width,
        render_height=args.height,
    )
    frame = renderer.render_frame(step=args.step, camera=args.camera)
    sys.stdout.buffer.write(frame.bytes)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
