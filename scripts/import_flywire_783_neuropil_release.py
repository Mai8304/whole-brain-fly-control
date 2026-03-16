from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from fruitfly.evaluation.flywire_neuropil_raw import (
    REQUIRED_FLYWIRE_783_RELEASE_FILES,
    build_release_manifest,
    validate_raw_release_dir,
)


def import_release_files(*, source_dir: Path, output_dir: Path) -> dict[str, object]:
    validate_raw_release_dir(source_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for filename in REQUIRED_FLYWIRE_783_RELEASE_FILES:
        shutil.copy2(source_dir / filename, output_dir / filename)

    manifest = build_release_manifest(output_dir)
    (output_dir / "release_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Freeze FlyWire 783 official neuropil release files into a local raw-source directory.")
    parser.add_argument("--source-dir", type=Path, required=True, help="Directory containing the official FlyWire 783 release files.")
    parser.add_argument("--output-dir", type=Path, required=True, help="Destination raw-source directory.")
    parser.add_argument("--json", action="store_true", help="Print the release manifest as JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    manifest = import_release_files(source_dir=args.source_dir, output_dir=args.output_dir)
    if args.json:
        print(json.dumps(manifest))
    else:
        print(args.output_dir / "release_manifest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
