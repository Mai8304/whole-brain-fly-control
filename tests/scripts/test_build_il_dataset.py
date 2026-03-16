from pathlib import Path


def test_build_il_dataset_cli_writes_nonempty_dataset(tmp_path: Path, monkeypatch) -> None:
    from scripts import build_il_dataset

    captured = {}

    monkeypatch.setattr(
        build_il_dataset,
        "export_straight_walking_records",
        lambda **kwargs: _capture_export_kwargs(captured, kwargs),
    )

    output_path = tmp_path / "dataset.jsonl"
    policy_dir = tmp_path / "walking"
    build_il_dataset.main(
        [
            "--output",
            str(output_path),
            "--episodes",
            "1",
            "--max-steps",
            "5",
            "--policy-dir",
            str(policy_dir),
        ]
    )

    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8").strip()
    assert captured["kwargs"]["policy_dir"] == policy_dir


def _capture_export_kwargs(captured: dict[str, object], kwargs: dict[str, object]) -> list[dict[str, list[float]]]:
    captured["kwargs"] = kwargs
    return [
        {
            "observation": [1.0],
            "command": [0.2],
            "expert_mean": [0.1],
            "expert_log_std": [-1.0],
        }
    ]
