def test_cli_json_output(capsys, monkeypatch) -> None:
    from fruitfly.snapshot import flywire_verify

    monkeypatch.setattr(
        flywire_verify,
        "verify_flywire_readonly",
        lambda **_: flywire_verify.FlyWireVerificationResult(
            status="ok",
            dataset="public",
            materialization_count=2,
            latest_materialization=783,
            query_points=1,
            resolved_roots=1,
        ),
    )

    exit_code = flywire_verify.main(["--json"])
    captured = capsys.readouterr()

    assert exit_code == 0
    assert '"status": "ok"' in captured.out
