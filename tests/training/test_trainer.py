from pathlib import Path


def test_offline_trainer_writes_checkpoint(tmp_path: Path) -> None:
    import torch

    from fruitfly.models.rate_model import WholeBrainRateModel
    from fruitfly.training import ILDataset, write_il_dataset
    from fruitfly.training.trainer import ILTrainingConfig, OfflineILTrainer

    dataset_path = tmp_path / "dataset.jsonl"
    write_il_dataset(
        dataset_path,
        [
            {
                "observation": [0.1, 0.2, 0.3, 0.4],
                "command": [0.0, 0.1],
                "expert_mean": [0.5, 0.6, 0.7],
                "expert_log_std": [0.0, 0.0, 0.0],
            },
            {
                "observation": [0.3, 0.2, 0.1, 0.0],
                "command": [0.1, 0.0],
                "expert_mean": [0.4, 0.3, 0.2],
                "expert_log_std": [0.0, 0.0, 0.0],
            },
        ],
    )
    dataset = ILDataset(dataset_path)
    model = WholeBrainRateModel(
        num_nodes=4,
        hidden_dim=8,
        action_dim=3,
        afferent_indices=[0],
        efferent_indices=[3],
        edge_index=[(0, 1), (1, 2), (2, 3)],
    )
    trainer = OfflineILTrainer(
        model=model,
        dataset=dataset,
        output_dir=tmp_path / "run",
        config=ILTrainingConfig(epochs=1, batch_size=2, learning_rate=1e-3),
    )

    metrics = trainer.train()
    checkpoint = tmp_path / "run" / "checkpoints" / "epoch_0001.pt"

    assert checkpoint.exists()
    assert metrics["loss"] >= 0.0

    payload = torch.load(checkpoint, map_location="cpu")
    assert "model" in payload
