from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from .roi_manifest import build_v1_roi_manifest

V1_ROI_NEUROPIL_SOURCES = {
    "AL": ["AL_L", "AL_R"],
    "LH": ["LH_L", "LH_R"],
    "PB": ["PB"],
    "FB": ["FB"],
    "EB": ["EB"],
    "NO": ["NO"],
    "LAL": ["LAL_L", "LAL_R"],
    "GNG": ["GNG"],
}


def build_v1_roi_neuropil_sources() -> dict[str, list[str]]:
    return {roi_id: list(neuropils) for roi_id, neuropils in V1_ROI_NEUROPIL_SOURCES.items()}


def load_fafbseg_roi_meshes(
    *,
    get_neuropil_volumes: Callable[[str | list[str]], Any] | None = None,
    roi_sources: dict[str, list[str]] | None = None,
) -> dict[str, Any]:
    if get_neuropil_volumes is None:
        from fafbseg import flywire

        get_neuropil_volumes = flywire.get_neuropil_volumes

    compiled_meshes: dict[str, Any] = {}
    for roi_id, source_neuropils in (roi_sources or build_v1_roi_neuropil_sources()).items():
        query: str | list[str]
        if len(source_neuropils) == 1:
            query = source_neuropils[0]
        else:
            query = list(source_neuropils)
        loaded = get_neuropil_volumes(query)
        volumes = _normalize_loaded_volumes(loaded)
        compiled_meshes[roi_id] = _combine_volumes_to_trimesh(volumes=volumes, roi_id=roi_id)
    return compiled_meshes


def export_v1_roi_meshes(
    *,
    output_dir: Path,
    get_neuropil_volumes: Callable[[str | list[str]], Any] | None = None,
    mesh_exporter: Callable[[Any, Path], None] | None = None,
) -> dict[str, Any]:
    output_dir.mkdir(parents=True, exist_ok=True)

    roi_sources = build_v1_roi_neuropil_sources()
    meshes = load_fafbseg_roi_meshes(
        get_neuropil_volumes=get_neuropil_volumes,
        roi_sources=roi_sources,
    )
    exporter = mesh_exporter or _default_mesh_exporter

    mesh_entries: list[dict[str, Any]] = []
    for roi_entry in build_v1_roi_manifest():
        roi_id = str(roi_entry["roi_id"])
        mesh = meshes[roi_id]
        output_path = output_dir / f"{roi_id}.glb"
        exporter(mesh, output_path)
        mesh_entries.append(
            {
                "roi_id": roi_id,
                "source_neuropils": roi_sources[roi_id],
                "render_asset_path": output_path.name,
                "render_format": "glb",
                "vertex_count": int(mesh.vertices.shape[0]),
                "face_count": int(mesh.faces.shape[0]),
            }
        )

    source_info = {
        "provider": "fafbseg.flywire",
        "space": "FlyWire/FAFB14.1",
        "source_function": "fafbseg.flywire.get_neuropil_volumes",
        "source_archive": "JFRC2NP.surf.fw.zip",
        "roi_meshes": mesh_entries,
    }
    (output_dir / "source_info.json").write_text(json.dumps(source_info, indent=2), encoding="utf-8")
    return source_info


def _normalize_loaded_volumes(loaded: Any) -> list[Any]:
    if hasattr(loaded, "vertices") and hasattr(loaded, "faces"):
        return [loaded]
    if isinstance(loaded, (list, tuple)):
        return list(loaded)
    raise TypeError(f"unsupported neuropil volume payload: {type(loaded)!r}")


def _combine_volumes_to_trimesh(*, volumes: list[Any], roi_id: str):
    import numpy as np
    import trimesh

    if not volumes:
        raise ValueError(f"no volumes loaded for ROI {roi_id}")

    parts = [
        trimesh.Trimesh(
            vertices=np.asarray(volume.vertices),
            faces=np.asarray(volume.faces),
            process=False,
        )
        for volume in volumes
    ]
    if len(parts) == 1:
        mesh = parts[0]
    else:
        mesh = trimesh.util.concatenate(parts)
    mesh.metadata["name"] = roi_id
    return mesh


def _default_mesh_exporter(mesh: Any, output_path: Path) -> None:
    mesh.export(output_path)
