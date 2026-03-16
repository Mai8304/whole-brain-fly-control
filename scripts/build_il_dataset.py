from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fruitfly.adapters import export_straight_walking_records
from fruitfly.training.il_dataset import write_il_dataset


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export a straight-walking IL dataset.")
    parser.add_argument("--output", type=Path, required=True, help="Output dataset path")
    parser.add_argument("--episodes", type=int, default=1, help="Number of expert episodes to export")
    parser.add_argument("--max-steps", type=int, default=32, help="Maximum steps per episode")
    parser.add_argument(
        "--policy-dir",
        type=Path,
        default=None,
        help="Directory containing walking saved_model.pb or its download root",
    )
    args = parser.parse_args(argv)

    try:
        records = export_straight_walking_records(
            episodes=args.episodes,
            max_steps=args.max_steps,
            policy_dir=args.policy_dir,
        )
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    write_il_dataset(args.output, records)
    print(
        json.dumps(
            {
                "status": "ok",
                "output": str(args.output),
                "episodes": args.episodes,
                "max_steps": args.max_steps,
                "sample_count": len(records),
            }
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
