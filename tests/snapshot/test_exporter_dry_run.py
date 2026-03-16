from pathlib import Path


def test_export_dry_run_writes_required_files(tmp_path: Path) -> None:
    from fruitfly.snapshot.exporter import SnapshotExportRequest, export_snapshot_dry_run

    class FakeFlyWire:
        def get_neighborhood(self, seed_root_id, max_hops, max_nodes):
            return {
                "nodes": [
                    {
                        "source_id": 1,
                        "dataset_version": "public",
                        "hemisphere": "unknown",
                        "flow_role": "intrinsic",
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
                    {"pre_id": 1, "post_id": 2, "synapse_count": 3, "is_active": True},
                ],
                "flow_labels": [
                    {"source_id": 1, "flow_role": "intrinsic"},
                    {"source_id": 2, "flow_role": "efferent"},
                ],
            }

    request = SnapshotExportRequest(snapshot_id="dry_run_test")
    result = export_snapshot_dry_run(
        request=request,
        output_root=tmp_path,
        flywire_client=FakeFlyWire(),
        seed_root_id=1,
    )

    assert result.status == "ok"
    assert (result.snapshot_dir / "manifest.yaml").exists()
    assert (result.snapshot_dir / "raw" / "nodes.parquet").exists()
    assert (result.snapshot_dir / "raw" / "edges.parquet").exists()
    assert (result.snapshot_dir / "raw" / "flow_labels.parquet").exists()
