def test_snapshot_export_request_defaults() -> None:
    from fruitfly.snapshot.exporter import SnapshotExportRequest

    request = SnapshotExportRequest(snapshot_id="dry_run")

    assert request.dataset == "public"
    assert request.max_hops == 2
    assert request.max_nodes == 5000
