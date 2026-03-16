def test_readonly_contract_fields_are_stable() -> None:
    from fruitfly.snapshot.flywire_verify import FlyWireVerificationResult

    payload = FlyWireVerificationResult(
        status="ok",
        dataset="public",
        materialization_count=1,
        latest_materialization=783,
        query_points=1,
        resolved_roots=1,
    ).to_dict()

    assert list(payload)[:6] == [
        "status",
        "dataset",
        "materialization_count",
        "latest_materialization",
        "query_points",
        "resolved_roots",
    ]
