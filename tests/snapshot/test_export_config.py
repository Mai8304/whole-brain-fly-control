from pathlib import Path

import yaml


def test_dry_run_snapshot_config_defaults() -> None:
    payload = yaml.safe_load(Path("configs/snapshot/flywire_dry_run.yaml").read_text(encoding="utf-8"))

    assert payload["dataset"] == "public"
    assert payload["max_hops"] == 2
    assert payload["max_nodes"] == 5000
    assert payload["seed_strategy"] == "readonly_coords"
