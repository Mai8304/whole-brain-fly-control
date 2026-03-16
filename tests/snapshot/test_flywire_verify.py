def test_verification_result_to_dict() -> None:
    from fruitfly.snapshot.flywire_verify import FlyWireVerificationResult

    result = FlyWireVerificationResult(
        status="ok",
        dataset="public",
        materialization_count=3,
        latest_materialization=783,
        query_points=1,
        resolved_roots=1,
    )

    assert result.to_dict()["status"] == "ok"


def test_verify_flywire_readonly_returns_ok_summary() -> None:
    from fruitfly.snapshot.flywire_verify import verify_flywire_readonly

    class FakeFlyWire:
        def __init__(self) -> None:
            self.dataset = None

        def set_default_dataset(self, dataset: str) -> None:
            self.dataset = dataset

        def get_materialization_versions(self) -> list[int]:
            return [630, 783]

        def locs_to_segments(self, coords: list[list[int]]) -> list[int]:
            assert coords == [[75350, 60162, 3162]]
            return [720575940000000001]

    result = verify_flywire_readonly(
        flywire_client=FakeFlyWire(),
        coords=[[75350, 60162, 3162]],
        dataset="public",
    )

    assert result.status == "ok"
    assert result.dataset == "public"
    assert result.latest_materialization == 783
    assert result.resolved_roots == 1


def test_verify_flywire_readonly_suppresses_client_stdout(capsys) -> None:
    from fruitfly.snapshot.flywire_verify import verify_flywire_readonly

    class NoisyFlyWire:
        def set_default_dataset(self, dataset: str) -> None:
            print(f'Default dataset set to "{dataset}".')

        def get_materialization_versions(self) -> list[int]:
            return [783]

        def locs_to_segments(self, coords: list[list[int]]) -> list[int]:
            return [720575940000000001]

    result = verify_flywire_readonly(
        flywire_client=NoisyFlyWire(),
        coords=[[75350, 60162, 3162]],
        dataset="public",
    )
    captured = capsys.readouterr()

    assert result.status == "ok"
    assert captured.out == ""
