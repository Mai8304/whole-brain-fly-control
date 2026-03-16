def test_build_v1_roi_manifest_freezes_the_approved_eight_rois() -> None:
    from fruitfly.evaluation.roi_manifest import build_v1_roi_manifest

    roi_manifest = build_v1_roi_manifest()

    assert [entry["roi_id"] for entry in roi_manifest] == [
        "AL",
        "LH",
        "PB",
        "FB",
        "EB",
        "NO",
        "LAL",
        "GNG",
    ]
    assert {entry["group"] for entry in roi_manifest} == {
        "input-associated",
        "core-processing",
        "output-associated",
    }


def test_build_v1_roi_manifest_includes_required_fields() -> None:
    from fruitfly.evaluation.roi_manifest import REQUIRED_ROI_MANIFEST_KEYS, build_v1_roi_manifest

    roi_manifest = build_v1_roi_manifest()

    for entry in roi_manifest:
        assert set(entry) == REQUIRED_ROI_MANIFEST_KEYS
        assert entry["short_label"]
        assert entry["display_name"]
        assert entry["display_name_zh"]
        assert entry["description_zh"]
        assert isinstance(entry["priority"], int)


def test_build_v1_roi_manifest_uses_information_flow_grouping() -> None:
    from fruitfly.evaluation.roi_manifest import build_v1_roi_manifest

    groups = {entry["roi_id"]: entry["group"] for entry in build_v1_roi_manifest()}

    assert groups["AL"] == "input-associated"
    assert groups["LH"] == "input-associated"
    assert groups["PB"] == "core-processing"
    assert groups["FB"] == "core-processing"
    assert groups["EB"] == "core-processing"
    assert groups["NO"] == "core-processing"
    assert groups["LAL"] == "output-associated"
    assert groups["GNG"] == "output-associated"
