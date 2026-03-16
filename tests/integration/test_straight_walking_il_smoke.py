from pathlib import Path


def test_train_il_runs_on_exported_straight_walking_dataset(tmp_path: Path) -> None:
    from fruitfly.models import WholeBrainRateModel
    from fruitfly.training import ILDataset, ILTrainingConfig, OfflineILTrainer, write_il_dataset

    dataset_path = tmp_path / "dataset.jsonl"
    write_il_dataset(
        dataset_path,
        [
            {
                "observation": [1.0, 2.0],
                "command": [0.2],
                "expert_mean": [0.1] * 59,
                "expert_log_std": [-1.0] * 59,
            }
        ],
    )

    model = WholeBrainRateModel(num_nodes=8, hidden_dim=4, action_dim=59)
    trainer = OfflineILTrainer(
        model=model,
        dataset=ILDataset(dataset_path),
        output_dir=tmp_path / "outputs",
        config=ILTrainingConfig(epochs=1, batch_size=1),
    )
    metrics = trainer.train()

    assert metrics["loss"] == metrics["loss"]
    assert (tmp_path / "outputs" / "checkpoints" / "epoch_0001.pt").exists()
