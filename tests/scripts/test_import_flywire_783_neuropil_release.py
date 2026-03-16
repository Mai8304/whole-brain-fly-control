from __future__ import annotations

import json
from pathlib import Path

import pytest


def _write_required_release_files(path: Path) -> None:
    for filename in (
        "flywire_synapses_783.feather",
        "per_neuron_neuropil_count_pre_783.feather",
        "per_neuron_neuropil_count_post_783.feather",
        "proofread_connections_783.feather",
        "proofread_root_ids_783.npy",
    ):
        (path / filename).write_bytes(filename.encode("utf-8"))


def test_import_release_copies_required_files_and_writes_manifest(tmp_path: Path) -> None:
    from scripts.import_flywire_783_neuropil_release import import_release_files

    source_dir = tmp_path / "source"
    source_dir.mkdir()
    _write_required_release_files(source_dir)

    output_dir = tmp_path / "raw"
    manifest = import_release_files(source_dir=source_dir, output_dir=output_dir)

    for filename in (
        "flywire_synapses_783.feather",
        "per_neuron_neuropil_count_pre_783.feather",
        "per_neuron_neuropil_count_post_783.feather",
        "proofread_connections_783.feather",
        "proofread_root_ids_783.npy",
    ):
        assert (output_dir / filename).exists()

    assert (output_dir / "release_manifest.json").exists()
    assert manifest["release_version"] == "783"
    assert manifest["files"]["flywire_synapses_783.feather"]["sha256"]


def test_import_release_rejects_missing_required_files(tmp_path: Path) -> None:
    from scripts.import_flywire_783_neuropil_release import import_release_files

    source_dir = tmp_path / "source"
    source_dir.mkdir()
    (source_dir / "flywire_synapses_783.feather").write_bytes(b"stub")

    with pytest.raises(ValueError, match="missing required FlyWire 783 files"):
        import_release_files(source_dir=source_dir, output_dir=tmp_path / "raw")


def test_cli_prints_manifest_path(tmp_path: Path, capsys) -> None:
    from scripts import import_flywire_783_neuropil_release

    source_dir = tmp_path / "source"
    source_dir.mkdir()
    _write_required_release_files(source_dir)
    output_dir = tmp_path / "raw"

    exit_code = import_flywire_783_neuropil_release.main(
        ["--source-dir", str(source_dir), "--output-dir", str(output_dir)]
    )

    assert exit_code == 0
    assert capsys.readouterr().out.strip() == str(output_dir / "release_manifest.json")
    assert json.loads((output_dir / "release_manifest.json").read_text(encoding="utf-8"))["release_version"] == "783"
