from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from fruitfly.evaluation.roi_manifest import build_v1_roi_manifest
from fruitfly.evaluation.roi_mesh_import import (
    build_v1_roi_neuropil_sources,
    export_v1_roi_meshes,
    load_fafbseg_roi_meshes,
)


class _FakeVolume:
    def __init__(self, vertices: np.ndarray, faces: np.ndarray) -> None:
        self.vertices = vertices
        self.faces = faces


def _triangle(offset: float) -> _FakeVolume:
    return _FakeVolume(
        vertices=np.array(
            [
                [offset + 0.0, 0.0, 0.0],
                [offset + 1.0, 0.0, 0.0],
                [offset + 0.0, 1.0, 0.0],
            ],
            dtype=float,
        ),
        faces=np.array([[0, 1, 2]], dtype=int),
    )


def test_build_v1_roi_neuropil_sources_matches_manifest() -> None:
    sources = build_v1_roi_neuropil_sources()

    assert list(sources) == [entry["roi_id"] for entry in build_v1_roi_manifest()]
    assert sources["AL"] == ["AL_L", "AL_R"]
    assert sources["LAL"] == ["LAL_L", "LAL_R"]
    assert sources["FB"] == ["FB"]


def test_load_fafbseg_roi_meshes_combines_bilateral_sources() -> None:
    def fake_loader(query: str | list[str]):
        if query == ["AL_L", "AL_R"]:
            return [_triangle(0.0), _triangle(10.0)]
        if query == "PB":
            return _triangle(20.0)
        raise AssertionError(f"unexpected query: {query!r}")

    meshes = load_fafbseg_roi_meshes(
        get_neuropil_volumes=fake_loader,
        roi_sources={
            "AL": ["AL_L", "AL_R"],
            "PB": ["PB"],
        },
    )

    assert meshes["AL"].vertices.shape == (6, 3)
    assert meshes["AL"].faces.shape == (2, 3)
    assert meshes["AL"].metadata["name"] == "AL"
    assert meshes["PB"].vertices.shape == (3, 3)
    assert meshes["PB"].faces.shape == (1, 3)


def test_export_v1_roi_meshes_writes_glbs_and_source_info(tmp_path: Path) -> None:
    def fake_loader(query: str | list[str]):
        if isinstance(query, list):
            return [_triangle(float(index) * 10.0) for index, _ in enumerate(query)]
        return _triangle(0.0)

    def fake_exporter(mesh, output_path: Path) -> None:
        output_path.write_text(
            json.dumps(
                {
                    "name": mesh.metadata["name"],
                    "vertex_count": int(mesh.vertices.shape[0]),
                    "face_count": int(mesh.faces.shape[0]),
                }
            ),
            encoding="utf-8",
        )

    source_info = export_v1_roi_meshes(
        output_dir=tmp_path,
        get_neuropil_volumes=fake_loader,
        mesh_exporter=fake_exporter,
    )

    assert (tmp_path / "AL.glb").exists()
    assert (tmp_path / "GNG.glb").exists()
    assert (tmp_path / "source_info.json").exists()
    assert source_info["provider"] == "fafbseg.flywire"
    assert source_info["space"] == "FlyWire/FAFB14.1"

    al_entry = next(entry for entry in source_info["roi_meshes"] if entry["roi_id"] == "AL")
    assert al_entry["source_neuropils"] == ["AL_L", "AL_R"]
    assert al_entry["vertex_count"] == 6
    assert al_entry["face_count"] == 2
