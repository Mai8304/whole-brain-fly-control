from __future__ import annotations

import argparse
import json
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT_DIR = (
    ROOT / "apps" / "neural-console" / "public" / "mujoco-fly" / "flybody-official-walk"
)
ENTRY_XML = "walk_imitation.xml"
SCENE_VERSION = "flybody-walk-imitation-v1"

_export_with_assets = None


def _prepare_runtime_environment(environ: dict[str, str]) -> None:
    environ.setdefault("MUJOCO_GL", "off")

    cache_root = Path(tempfile.gettempdir()) / "fruitfly-export-cache"
    environ.setdefault("MPLCONFIGDIR", str(cache_root / "matplotlib"))
    environ.setdefault("XDG_CACHE_HOME", str(cache_root / "xdg"))


def _build_walk_imitation_environment():
    _prepare_runtime_environment(os.environ)
    try:
        from flybody.fly_envs import walk_imitation
    except ImportError as exc:  # pragma: no cover - exercised through runtime path
        raise RuntimeError("flybody runtime is unavailable") from exc

    return walk_imitation(ref_path=None)


def _ensure_export_with_assets():
    global _export_with_assets
    if _export_with_assets is None:
        try:
            from dm_control.mjcf import export_with_assets as export_with_assets_fn
        except ImportError as exc:  # pragma: no cover - exercised through runtime path
            raise RuntimeError("dm_control mjcf export_with_assets is unavailable") from exc
        _export_with_assets = export_with_assets_fn
    return _export_with_assets


def _initialize_environment(environment) -> None:
    environment.reset()


def _build_manifest(output_dir: Path) -> dict[str, object]:
    exported_files = sorted(
        str(path.relative_to(output_dir))
        for path in output_dir.rglob("*")
        if path.is_file() and path.name != "manifest.json"
    )
    return {
        "entry_xml": ENTRY_XML,
        "scene_version": SCENE_VERSION,
        "asset_count": len(exported_files),
        "files": exported_files,
        "output_dir": str(output_dir),
    }


def export_official_walk_scene(output_dir: Path) -> dict[str, object]:
    environment = _build_walk_imitation_environment()
    _initialize_environment(environment)

    output_dir.mkdir(parents=True, exist_ok=True)
    exporter = _ensure_export_with_assets()
    exporter(environment.task.root_entity.mjcf_model, output_dir, ENTRY_XML)

    manifest = _build_manifest(output_dir)
    (output_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    return manifest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_OUTPUT_DIR,
        help="Directory to write the exported official walk scene bundle.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the export manifest as JSON.",
    )
    args = parser.parse_args(argv)

    manifest = export_official_walk_scene(args.output_dir)

    if args.json:
        print(json.dumps(manifest, indent=2, sort_keys=True))
    else:
        print(f"Exported official walk scene to {args.output_dir}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
