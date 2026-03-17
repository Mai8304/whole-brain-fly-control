def test_build_v1_neuropil_manifest_freezes_the_approved_eight_neuropils() -> None:
    from fruitfly.evaluation.neuropil_manifest import build_v1_neuropil_manifest

    neuropil_manifest = build_v1_neuropil_manifest()

    assert [entry["neuropil"] for entry in neuropil_manifest] == [
        "AL",
        "LH",
        "PB",
        "FB",
        "EB",
        "NO",
        "LAL",
        "GNG",
    ]
    assert {entry["group"] for entry in neuropil_manifest} == {
        "input-associated",
        "core-processing",
        "output-associated",
    }


def test_build_v1_neuropil_manifest_includes_required_fields() -> None:
    from fruitfly.evaluation.neuropil_manifest import (
        REQUIRED_NEUROPIL_MANIFEST_KEYS,
        build_v1_neuropil_manifest,
    )

    neuropil_manifest = build_v1_neuropil_manifest()

    for entry in neuropil_manifest:
        assert set(entry) == REQUIRED_NEUROPIL_MANIFEST_KEYS
        assert entry["short_label"]
        assert entry["display_name"]
        assert entry["display_name_zh"]
        assert entry["description_zh"]
        assert isinstance(entry["priority"], int)
        assert str(entry["render_asset_path"]).endswith(".glb")
        assert entry["render_format"] == "glb"


def test_build_v1_neuropil_manifest_uses_information_flow_grouping() -> None:
    from fruitfly.evaluation.neuropil_manifest import build_v1_neuropil_manifest

    groups = {entry["neuropil"]: entry["group"] for entry in build_v1_neuropil_manifest()}

    assert groups["AL"] == "input-associated"
    assert groups["LH"] == "input-associated"
    assert groups["PB"] == "core-processing"
    assert groups["FB"] == "core-processing"
    assert groups["EB"] == "core-processing"
    assert groups["NO"] == "core-processing"
    assert groups["LAL"] == "output-associated"
    assert groups["GNG"] == "output-associated"
