from __future__ import annotations

import argparse
import json
from pathlib import Path

from fruitfly.evaluation.roi_mesh_import import export_v1_roi_meshes

DEFAULT_OUTPUT_DIR = Path("outputs/ui-assets/flywire_roi_meshes_v1")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Export the V1 FlyWire ROI mesh set from fafbseg.flywire.get_neuropil_volumes."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory where <ROI_ID>.glb files and source_info.json are written.",
    )
    parser.add_argument("--json", action="store_true", help="Print source_info.json as JSON.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    source_info = export_v1_roi_meshes(output_dir=args.output_dir)
    if args.json:
        print(json.dumps(source_info))
    else:
        print(args.output_dir / "source_info.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
