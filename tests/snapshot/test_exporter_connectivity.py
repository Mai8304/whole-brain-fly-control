def test_export_dry_run_supports_get_connectivity_fallback(tmp_path) -> None:
    import yaml

    from fruitfly.snapshot.exporter import SnapshotExportRequest, export_snapshot_dry_run

    class FakeConnectivityFlyWire:
        def set_default_dataset(self, dataset):
            self.dataset = dataset

        def get_connectivity(self, roots, **kwargs):
            assert kwargs["dataset"] == "public"
            return [
                {"pre": 1, "post": 2, "weight": 3},
                {"pre": 2, "post": 3, "weight": 5},
            ]

    result = export_snapshot_dry_run(
        request=SnapshotExportRequest(snapshot_id="connectivity_fallback", max_hops=2, max_nodes=10),
        output_root=tmp_path,
        flywire_client=FakeConnectivityFlyWire(),
        seed_root_id=1,
    )

    assert result.status == "ok"
    assert result.node_count == 3
    assert result.edge_count == 2
    manifest = yaml.safe_load((result.snapshot_dir / "manifest.yaml").read_text(encoding="utf-8"))
    assert manifest["flow_label_source"] == "local_degree_heuristic"
