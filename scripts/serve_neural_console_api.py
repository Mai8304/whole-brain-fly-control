from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import uvicorn

from fruitfly.ui import ConsoleApiConfig, create_console_api


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Serve the neural console read-only API.")
    parser.add_argument("--compiled-graph-dir", type=Path, required=True, help="Compiled graph artifact directory")
    parser.add_argument("--eval-dir", type=Path, required=True, help="Closed-loop evaluation artifact directory")
    parser.add_argument("--checkpoint", type=Path, default=None, help="Optional checkpoint used for the displayed run")
    parser.add_argument(
        "--brain-asset-dir",
        type=Path,
        default=None,
        help="Optional directory with FlyWire brain asset manifest and shell asset",
    )
    parser.add_argument(
        "--mujoco-fly-scene-dir",
        type=Path,
        default=None,
        help="Optional directory with the exported official flybody walk scene bundle",
    )
    parser.add_argument(
        "--mujoco-fly-policy-checkpoint",
        type=Path,
        default=None,
        help="Optional official flybody walking policy checkpoint path",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload for local development")
    args = parser.parse_args(argv)

    brain_asset_dir = _resolve_default_asset_dir(
        explicit=args.brain_asset_dir,
        root=ROOT,
        predicate=_looks_like_brain_asset_dir,
    )
    mujoco_fly_scene_dir = _resolve_default_mujoco_fly_scene_dir(
        explicit=args.mujoco_fly_scene_dir,
        root=ROOT,
    )

    app = create_console_api(
        ConsoleApiConfig(
            compiled_graph_dir=args.compiled_graph_dir,
            eval_dir=args.eval_dir,
            checkpoint_path=args.checkpoint,
            brain_asset_dir=brain_asset_dir,
            mujoco_fly_scene_dir=mujoco_fly_scene_dir,
            mujoco_fly_policy_checkpoint_path=args.mujoco_fly_policy_checkpoint,
        )
    )
    uvicorn.run(app, host=args.host, port=args.port, reload=args.reload)
    return 0


def _resolve_default_asset_dir(
    *,
    explicit: Path | None,
    root: Path,
    predicate: Callable[[Path], bool],
) -> Path | None:
    if explicit is not None:
        return explicit

    ui_assets_dir = root / "outputs" / "ui-assets"
    if not ui_assets_dir.exists():
        return None

    candidates = sorted(
        [path for path in ui_assets_dir.iterdir() if path.is_dir() and predicate(path)],
        key=lambda path: path.name,
        reverse=True,
    )
    return candidates[0] if candidates else None


def _looks_like_brain_asset_dir(path: Path) -> bool:
    return (path / "manifest.json").exists() and (path / "brain_shell.glb").exists()


def _resolve_default_mujoco_fly_scene_dir(*, explicit: Path | None, root: Path) -> Path | None:
    if explicit is not None:
        return explicit

    candidate = root / "apps" / "neural-console" / "public" / "mujoco-fly" / "flybody-official-walk"
    if _looks_like_mujoco_fly_scene_dir(candidate):
        return candidate
    return None


def _looks_like_mujoco_fly_scene_dir(path: Path) -> bool:
    manifest_path = path / "manifest.json"
    entry_xml_path = path / "walk_imitation.xml"
    return manifest_path.exists() and entry_xml_path.exists()


if __name__ == "__main__":
    raise SystemExit(main())
