from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fruitfly.evaluation.walking_eval import summarize_turning


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a stub walking evaluation.")
    parser.add_argument("--headings", nargs="*", type=float, default=[0.0, 0.0, 0.0])
    args = parser.parse_args()

    summary = summarize_turning(args.headings)
    print(json.dumps(summary))


if __name__ == "__main__":
    main()
