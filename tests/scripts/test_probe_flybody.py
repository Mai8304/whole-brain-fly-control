def test_probe_flybody_cli_reports_runtime_error(capsys, monkeypatch) -> None:
    from scripts import probe_flybody

    monkeypatch.setattr(
        probe_flybody,
        "probe_walk_imitation",
        lambda: (_ for _ in ()).throw(RuntimeError("dedicated flybody environment required")),
    )

    exit_code = probe_flybody.main()
    captured = capsys.readouterr()

    assert exit_code == 2
    assert "dedicated flybody environment required" in captured.err
