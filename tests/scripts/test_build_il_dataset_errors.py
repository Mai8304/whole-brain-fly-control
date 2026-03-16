def test_build_il_dataset_cli_reports_runtime_error(capsys, monkeypatch, tmp_path) -> None:
    from scripts import build_il_dataset

    monkeypatch.setattr(
        build_il_dataset,
        "export_straight_walking_records",
        lambda **_: (_ for _ in ()).throw(RuntimeError("dedicated flybody environment required")),
    )

    exit_code = build_il_dataset.main(
        ["--output", str(tmp_path / "dataset.jsonl"), "--episodes", "1", "--max-steps", "5"]
    )
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "dedicated flybody environment required" in captured.err
