from pathlib import Path


def test_write_il_dataset_persists_real_contract_fields(tmp_path: Path) -> None:
    from fruitfly.training.il_dataset import ILDataset, write_il_dataset

    dataset_path = tmp_path / "dataset.jsonl"
    write_il_dataset(
        dataset_path,
        [
            {
                "observation": [1.0, 2.0],
                "command": [0.5],
                "expert_mean": [0.1, 0.2],
                "expert_log_std": [-1.0, -1.0],
                "episode_id": 1,
                "step_id": 2,
                "task": "straight_walking",
            }
        ],
    )

    dataset = ILDataset(dataset_path)
    sample = dataset[0]

    assert len(dataset) == 1
    assert list(sample["observation"]) == [1.0, 2.0]
    assert list(sample["command"]) == [0.5]
    assert list(sample["expert_mean"]) == [0.1, 0.2]
    assert list(sample["expert_log_std"]) == [-1.0, -1.0]
    assert sample["episode_id"] == 1
    assert sample["step_id"] == 2
    assert sample["task"] == "straight_walking"
