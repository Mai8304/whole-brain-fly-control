from __future__ import annotations

import hashlib
from pathlib import Path

FLYWIRE_783_RELEASE_VERSION = "783"
FLYWIRE_783_DATASET = "public"
FLYWIRE_783_SOURCE = "FlyWire official release"

REQUIRED_FLYWIRE_783_RELEASE_FILES = (
    "flywire_synapses_783.feather",
    "per_neuron_neuropil_count_pre_783.feather",
    "per_neuron_neuropil_count_post_783.feather",
    "proofread_connections_783.feather",
    "proofread_root_ids_783.npy",
)


def validate_raw_release_dir(path: Path) -> None:
    missing = [
        filename
        for filename in REQUIRED_FLYWIRE_783_RELEASE_FILES
        if not (path / filename).exists()
    ]
    if missing:
        raise ValueError(f"missing required FlyWire 783 files: {sorted(missing)}")


def build_release_manifest(path: Path) -> dict[str, object]:
    validate_raw_release_dir(path)
    return {
        "release_version": FLYWIRE_783_RELEASE_VERSION,
        "dataset": FLYWIRE_783_DATASET,
        "source": FLYWIRE_783_SOURCE,
        "files": {
            filename: {"sha256": _sha256(path / filename)}
            for filename in REQUIRED_FLYWIRE_783_RELEASE_FILES
        },
    }


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
