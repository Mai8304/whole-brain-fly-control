import json
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest


def test_materialize_runtime_activity_artifacts_uses_contract_payload_with_formal_neuropil_metrics(
    tmp_path: Path,
    monkeypatch,
) -> None:
    from fruitfly.evaluation import runtime_activity_artifacts as module

    compiled_graph_dir = tmp_path / "compiled"
    eval_dir = tmp_path / "eval"
    compiled_graph_dir.mkdir()
    eval_dir.mkdir()

    pq.write_table(
        pa.Table.from_pylist(
            [
                {"source_id": 10, "node_idx": 0},
                {"source_id": 20, "node_idx": 1},
            ]
        ),
        compiled_graph_dir / "node_index.parquet",
    )
    pq.write_table(
        pa.Table.from_pylist(
            [
                {
                    "source_id": 10,
                    "node_idx": 0,
                    "neuropil": "AL_L",
                    "occupancy_fraction": 0.25,
                    "synapse_count": 2,
                },
                {
                    "source_id": 10,
                    "node_idx": 0,
                    "neuropil": "LH_R",
                    "occupancy_fraction": 0.75,
                    "synapse_count": 6,
                },
                {
                    "source_id": 20,
                    "node_idx": 1,
                    "neuropil": "FB",
                    "occupancy_fraction": 1.0,
                    "synapse_count": 5,
                },
            ]
        ),
        compiled_graph_dir / "node_neuropil_occupancy.parquet",
    )
    (compiled_graph_dir / "neuropil_truth_validation.json").write_text(
        json.dumps(
            {
                "validation_passed": True,
                "validation_scope": "graph_source_ids",
                "roster_alignment": {"alignment_passed": True},
            }
        ),
        encoding="utf-8",
    )
    (eval_dir / "summary.json").write_text(
        json.dumps(
            {
                "status": "ok",
                "task": "straight_walking",
                "steps_requested": 2,
                "steps_completed": 2,
                "terminated_early": False,
            }
        ),
        encoding="utf-8",
    )
    (eval_dir / "activity_trace.json").write_text(
        json.dumps(
            {
                "steps_requested": 2,
                "steps_completed": 2,
                "snapshots": [
                    {
                        "step_id": 2,
                        "afferent_activity": 0.1,
                        "intrinsic_activity": 0.2,
                        "efferent_activity": 0.3,
                        "top_active_nodes": [
                            {
                                "node_idx": 0,
                                "activity_value": -0.6,
                                "flow_role": "intrinsic",
                            },
                            {
                                "node_idx": 1,
                                "activity_value": 0.4,
                                "flow_role": "efferent",
                            },
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    np.save(
        eval_dir / "final_node_activity.npy",
        np.asarray([-0.6, 0.4], dtype=np.float32),
    )

    captured: dict[str, object] = {}

    def fake_build_brain_view_payload(**kwargs):
        captured.update(kwargs)
        return {"sentinel": True, "region_activity": kwargs["region_activity"], "top_nodes": kwargs["top_nodes"]}

    monkeypatch.setattr(
        module,
        "build_brain_view_payload",
        fake_build_brain_view_payload,
        raising=False,
    )

    brain_payload, _ = module.materialize_runtime_activity_artifacts(
        compiled_graph_dir=compiled_graph_dir,
        eval_dir=eval_dir,
    ) or ({}, {})

    assert brain_payload["sentinel"] is True
    assert captured["activity_metric"] == "activity_mass"
    assert captured["mapping_mode"] == "node_neuropil_occupancy"
    assert captured["mapping_coverage"] == {
        "neuropil_mapped_nodes": 2,
        "total_nodes": 2,
    }
    assert captured["formal_truth"] == {
        "validation_passed": True,
        "graph_scope_validation_passed": True,
        "roster_alignment_passed": True,
    }

    region_by_id = {
        entry["neuropil_id"]: entry
        for entry in captured["region_activity"]
    }
    assert region_by_id["AL_L"]["display_name"] == "AL"
    assert region_by_id["AL_L"]["raw_activity_mass"] == pytest.approx(0.15)
    assert region_by_id["AL_L"]["signed_activity"] == pytest.approx(-0.15)
    assert region_by_id["AL_L"]["covered_weight_sum"] == pytest.approx(0.25)
    assert region_by_id["AL_L"]["node_count"] == 1
    assert region_by_id["AL_L"]["is_display_grouped"] is True

    assert region_by_id["LH_R"]["display_name"] == "LH"
    assert region_by_id["LH_R"]["raw_activity_mass"] == pytest.approx(0.45)
    assert region_by_id["LH_R"]["signed_activity"] == pytest.approx(-0.45)
    assert region_by_id["LH_R"]["covered_weight_sum"] == pytest.approx(0.75)
    assert region_by_id["LH_R"]["node_count"] == 1
    assert region_by_id["LH_R"]["is_display_grouped"] is True

    assert region_by_id["FB"]["display_name"] == "FB"
    assert region_by_id["FB"]["raw_activity_mass"] == pytest.approx(0.4)
    assert region_by_id["FB"]["signed_activity"] == pytest.approx(0.4)
    assert region_by_id["FB"]["covered_weight_sum"] == pytest.approx(1.0)
    assert region_by_id["FB"]["node_count"] == 1
    assert region_by_id["FB"]["is_display_grouped"] is False

    assert region_by_id["LH_R"]["signed_activity"] != pytest.approx(
        region_by_id["LH_R"]["raw_activity_mass"]
    )

    assert captured["top_nodes"] == [
        {
            "node_idx": 0,
            "source_id": "10",
            "activity_value": -0.6,
            "flow_role": "intrinsic",
            "neuropil_memberships": [
                {
                    "neuropil": "AL_L",
                    "occupancy_fraction": 0.25,
                    "synapse_count": 2,
                },
                {
                    "neuropil": "LH_R",
                    "occupancy_fraction": 0.75,
                    "synapse_count": 6,
                },
            ],
            "display_group_hint": "LH",
        },
        {
            "node_idx": 1,
            "source_id": "20",
            "activity_value": 0.4,
            "flow_role": "efferent",
            "neuropil_memberships": [
                {
                    "neuropil": "FB",
                    "occupancy_fraction": 1.0,
                    "synapse_count": 5,
                }
            ],
            "display_group_hint": "FB",
        },
    ]


def test_build_replay_brain_view_payload_defaults_missing_synapse_count_to_zero(
    tmp_path: Path,
) -> None:
    from fruitfly.evaluation.runtime_activity_artifacts import (
        build_replay_brain_view_payload,
    )

    compiled_graph_dir = tmp_path / "compiled"
    compiled_graph_dir.mkdir()

    pq.write_table(
        pa.Table.from_pylist(
            [
                {"source_id": 10, "node_idx": 0},
            ]
        ),
        compiled_graph_dir / "node_index.parquet",
    )
    pq.write_table(
        pa.Table.from_pylist(
            [
                {
                    "source_id": 10,
                    "node_idx": 0,
                    "neuropil": "AL_L",
                    "occupancy_fraction": 1.0,
                }
            ]
        ),
        compiled_graph_dir / "node_neuropil_occupancy.parquet",
    )

    payload = build_replay_brain_view_payload(
        compiled_graph_dir=compiled_graph_dir,
        step_id=3,
        node_activity=np.asarray([0.25], dtype=np.float32),
        afferent_activity=0.1,
        intrinsic_activity=0.2,
        efferent_activity=0.3,
        top_active_nodes=[
            {"node_idx": 0, "activity_value": 0.25, "flow_role": "intrinsic"}
        ],
        formal_truth={
            "validation_passed": True,
            "graph_scope_validation_passed": True,
            "roster_alignment_passed": True,
        },
    )

    assert payload["top_nodes"] == [
        {
            "node_idx": 0,
            "source_id": "10",
            "activity_value": 0.25,
            "flow_role": "intrinsic",
            "neuropil_memberships": [
                {
                    "neuropil": "AL_L",
                    "occupancy_fraction": 1.0,
                    "synapse_count": 0,
                }
            ],
            "display_group_hint": "AL",
        }
    ]


def test_materialize_runtime_activity_artifacts_emits_grouped_display_region_activity(
    tmp_path: Path,
) -> None:
    from fruitfly.evaluation.runtime_activity_artifacts import (
        materialize_runtime_activity_artifacts,
    )

    compiled_graph_dir = tmp_path / "compiled"
    eval_dir = tmp_path / "eval"
    compiled_graph_dir.mkdir()
    eval_dir.mkdir()

    pq.write_table(
        pa.Table.from_pylist(
            [
                {"source_id": 10, "node_idx": 0},
                {"source_id": 20, "node_idx": 1},
            ]
        ),
        compiled_graph_dir / "node_index.parquet",
    )
    pq.write_table(
        pa.Table.from_pylist(
            [
                {
                    "source_id": 10,
                    "node_idx": 0,
                    "neuropil": "AL_L",
                    "occupancy_fraction": 0.25,
                    "synapse_count": 2,
                },
                {
                    "source_id": 10,
                    "node_idx": 0,
                    "neuropil": "AL_R",
                    "occupancy_fraction": 0.75,
                    "synapse_count": 6,
                },
                {
                    "source_id": 20,
                    "node_idx": 1,
                    "neuropil": "FB",
                    "occupancy_fraction": 1.0,
                    "synapse_count": 4,
                },
            ]
        ),
        compiled_graph_dir / "node_neuropil_occupancy.parquet",
    )
    (compiled_graph_dir / "neuropil_truth_validation.json").write_text(
        json.dumps(
            {
                "validation_passed": True,
                "validation_scope": "graph_source_ids",
                "roster_alignment": {"alignment_passed": True},
            }
        ),
        encoding="utf-8",
    )
    (eval_dir / "summary.json").write_text(
        json.dumps(
            {
                "status": "ok",
                "task": "straight_walking",
                "steps_requested": 1,
                "steps_completed": 1,
                "terminated_early": False,
            }
        ),
        encoding="utf-8",
    )
    (eval_dir / "activity_trace.json").write_text(
        json.dumps(
            {
                "steps_requested": 1,
                "steps_completed": 1,
                "snapshots": [
                    {
                        "step_id": 1,
                        "afferent_activity": 0.2,
                        "intrinsic_activity": 0.4,
                        "efferent_activity": 0.1,
                        "top_active_nodes": [],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    np.save(eval_dir / "final_node_activity.npy", np.asarray([-2.0, 0.5], dtype=np.float32))

    payload, _ = materialize_runtime_activity_artifacts(
        compiled_graph_dir=compiled_graph_dir,
        eval_dir=eval_dir,
    ) or ({}, {})

    grouped = {
        entry["group_neuropil_id"]: entry
        for entry in payload["display_region_activity"]
    }

    assert set(grouped) == {"AL", "FB"}
    assert grouped["AL"]["raw_activity_mass"] == pytest.approx(2.0)
    assert grouped["AL"]["signed_activity"] == pytest.approx(-2.0)
    assert grouped["AL"]["member_neuropils"] == ["AL_L", "AL_R"]
    assert grouped["AL"]["view_mode"] == "grouped-neuropil-v1"
    assert grouped["AL"]["is_display_transform"] is True

    assert grouped["FB"]["raw_activity_mass"] == pytest.approx(0.5)
    assert grouped["FB"]["signed_activity"] == pytest.approx(0.5)
    assert grouped["FB"]["member_neuropils"] == ["FB"]
