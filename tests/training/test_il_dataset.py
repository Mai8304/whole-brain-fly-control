from pathlib import Path


def test_il_dataset_roundtrip(tmp_path: Path) -> None:
    from fruitfly.training.il_dataset import ILDataset, write_il_dataset

    records = [
        {
            "observation": [1.0, 2.0],
            "command": [3.0],
            "expert_mean": [0.1, 0.2],
            "expert_log_std": [-1.0, -1.0],
        }
    ]
    path = tmp_path / "dataset.jsonl"
    write_il_dataset(path, records)

    dataset = ILDataset(path)
    sample = dataset[0]
    assert sample["observation"].shape[0] == 2
    assert sample["command"].shape[0] == 1
