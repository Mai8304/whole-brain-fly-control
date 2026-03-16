from __future__ import annotations

from pathlib import Path
from unittest.mock import ANY

import pytest


def test_required_release_files_match_flywire_783_contract() -> None:
    from fruitfly.evaluation.flywire_neuropil_raw import (
        FLYWIRE_783_RELEASE_VERSION,
        REQUIRED_FLYWIRE_783_RELEASE_FILES,
    )

    assert FLYWIRE_783_RELEASE_VERSION == "783"
    assert REQUIRED_FLYWIRE_783_RELEASE_FILES == (
        "flywire_synapses_783.feather",
        "per_neuron_neuropil_count_pre_783.feather",
        "per_neuron_neuropil_count_post_783.feather",
        "proofread_connections_783.feather",
        "proofread_root_ids_783.npy",
    )


def test_build_release_manifest_uses_required_metadata_keys(tmp_path: Path) -> None:
    from fruitfly.evaluation.flywire_neuropil_raw import build_release_manifest

    for filename in (
        "flywire_synapses_783.feather",
        "per_neuron_neuropil_count_pre_783.feather",
        "per_neuron_neuropil_count_post_783.feather",
        "proofread_connections_783.feather",
        "proofread_root_ids_783.npy",
    ):
        (tmp_path / filename).write_bytes(filename.encode("utf-8"))

    manifest = build_release_manifest(tmp_path)

    assert manifest["release_version"] == "783"
    assert manifest["dataset"] == "public"
    assert manifest["source"] == "FlyWire official release"
    assert manifest["files"] == {
        "flywire_synapses_783.feather": {"sha256": ANY},
        "per_neuron_neuropil_count_pre_783.feather": {"sha256": ANY},
        "per_neuron_neuropil_count_post_783.feather": {"sha256": ANY},
        "proofread_connections_783.feather": {"sha256": ANY},
        "proofread_root_ids_783.npy": {"sha256": ANY},
    }


def test_validate_raw_release_dir_rejects_missing_required_files(tmp_path: Path) -> None:
    from fruitfly.evaluation.flywire_neuropil_raw import validate_raw_release_dir

    (tmp_path / "flywire_synapses_783.feather").write_bytes(b"stub")

    with pytest.raises(ValueError, match="missing required FlyWire 783 files"):
        validate_raw_release_dir(tmp_path)
