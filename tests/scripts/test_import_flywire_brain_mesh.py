import json
import os
from pathlib import Path

import numpy as np


def test_import_flywire_brain_mesh_cli_writes_manifest_and_assets(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    from scripts import import_flywire_brain_mesh

    captured: dict[str, object] = {}

    def fake_import(*, output_dir: Path, cloudpath: str, mesh_segment_id: int) -> dict[str, object]:
        captured["output_dir"] = output_dir
        captured["cloudpath"] = cloudpath
        captured["mesh_segment_id"] = mesh_segment_id
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "brain_shell.glb").write_bytes(b"glb")
        (output_dir / "source_info.json").write_text('{"mesh":"mesh"}', encoding="utf-8")
        manifest = {
            "asset_id": "flywire_brain_v141",
            "shell": {"render_asset_path": "brain_shell.glb", "render_format": "glb"},
            "neuropil_manifest": [
                {
                    "neuropil": "AL",
                    "render_asset_path": "AL.glb",
                    "render_format": "glb",
                }
            ],
        }
        (output_dir / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
        return manifest

    monkeypatch.setattr(import_flywire_brain_mesh, "import_flywire_brain_mesh_asset", fake_import)

    output_dir = tmp_path / "brain_assets"
    exit_code = import_flywire_brain_mesh.main(
        ["--output-dir", str(output_dir), "--mesh-segment-id", "1", "--json"]
    )

    assert exit_code == 0
    assert captured["output_dir"] == output_dir
    assert captured["mesh_segment_id"] == 1
    assert (output_dir / "manifest.json").exists()
    assert (output_dir / "brain_shell.glb").exists()
    assert json.loads(capsys.readouterr().out)["asset_id"] == "flywire_brain_v141"


def test_import_flywire_brain_mesh_asset_uses_custom_output_dir_relative_neuropil_paths(
    tmp_path: Path, monkeypatch
) -> None:
    from scripts import import_flywire_brain_mesh

    class FakeMesh:
        vertices = np.asarray(
            [[0.0, 0.0, 0.0], [1.0, 1.0, 1.0]],
            dtype=np.float64,
        )
        faces = np.asarray([[0, 0, 0]], dtype=np.int64)

    monkeypatch.setattr(
        import_flywire_brain_mesh,
        "fetch_source_info",
        lambda _url: {"mesh": "mesh"},
    )
    monkeypatch.setattr(
        import_flywire_brain_mesh,
        "fetch_shell_mesh",
        lambda **_kwargs: FakeMesh(),
    )
    monkeypatch.setattr(
        import_flywire_brain_mesh,
        "export_shell_glb",
        lambda *, mesh, output_path: output_path.write_bytes(b"glb"),
    )

    output_dir = tmp_path / "custom" / "deep" / "brain_bundle"
    manifest = import_flywire_brain_mesh.import_flywire_brain_mesh_asset(
        output_dir=output_dir,
        mesh_segment_id=1,
    )

    bundle_dir = (
        Path(import_flywire_brain_mesh.__file__).resolve().parents[1]
        / "outputs/ui-assets/flywire_roi_meshes_v1"
    )
    expected_prefix = Path(os.path.relpath(bundle_dir, output_dir)).as_posix().rstrip("/")

    assert manifest["neuropil_manifest"]
    assert manifest["neuropil_manifest"][0]["render_asset_path"].startswith(f"{expected_prefix}/")
