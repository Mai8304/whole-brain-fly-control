def test_seed_resolution_uses_first_nonzero_root() -> None:
    from fruitfly.snapshot.exporter import resolve_seed_root_id

    class FakeFlyWire:
        def locs_to_segments(self, coords):
            return [0, 720575940000000123]

    root_id = resolve_seed_root_id(
        flywire_client=FakeFlyWire(),
        coords=[[1, 2, 3], [4, 5, 6]],
    )

    assert root_id == 720575940000000123
