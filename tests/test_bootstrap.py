def test_package_imports() -> None:
    import fruitfly

    assert fruitfly.__all__ == []
