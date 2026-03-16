def test_export_snapshot_cli_json_output(capsys, monkeypatch, tmp_path) -> None:
    from fruitfly.snapshot import exporter

    monkeypatch.setattr(
        exporter,
        "export_snapshot",
        lambda **_: exporter.SnapshotExportResult(
            snapshot_dir=tmp_path / "dry_run",
            seed_root_id=123,
            node_count=5,
            edge_count=4,
            status="ok",
        ),
    )

    exit_code = exporter.main(
        [
            "--snapshot-id",
            "dry_run",
            "--output-root",
            str(tmp_path),
            "--json",
        ]
    )
    captured = capsys.readouterr()

    assert exit_code == 0
    assert '"status": "ok"' in captured.out
