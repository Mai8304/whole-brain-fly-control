import json
import subprocess
import sys
from pathlib import Path


def test_compile_graph_script_reads_normalized_snapshot(tmp_path: Path) -> None:
    from fruitfly.snapshot.exporter import SnapshotExportRequest, export_snapshot_dry_run

    class FakeFlyWire:
        def get_neighborhood(self, seed_root_id, max_hops, max_nodes):
            return {
                "nodes": [
                    {
                        "source_id": 1,
                        "dataset_version": "public",
                        "hemisphere": "unknown",
                        "flow_role": "afferent",
                        "is_active": True,
                    },
                    {
                        "source_id": 2,
                        "dataset_version": "public",
                        "hemisphere": "unknown",
                        "flow_role": "efferent",
                        "is_active": True,
                    },
                ],
                "edges": [
                    {"pre_id": 1, "post_id": 2, "synapse_count": 2, "is_active": True},
                ],
                "flow_labels": [
                    {"source_id": 1, "flow_role": "afferent"},
                    {"source_id": 2, "flow_role": "efferent"},
                ],
            }

    result = export_snapshot_dry_run(
        request=SnapshotExportRequest(snapshot_id="compile_script"),
        output_root=tmp_path,
        flywire_client=FakeFlyWire(),
        seed_root_id=1,
    )
    output_dir = tmp_path / "compiled"

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/compile_graph.py",
            "--snapshot-dir",
            str(result.snapshot_dir),
            "--output-dir",
            str(output_dir),
        ],
        check=True,
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
    )

    assert completed.returncode == 0
    payload = json.loads(completed.stdout)
    assert payload["status"] == "ok"
    assert payload["node_count"] == 2
    assert payload["edge_count"] == 1
    assert (output_dir / "edge_index.pt").exists()
    assert (output_dir / "io_masks.pt").exists()
