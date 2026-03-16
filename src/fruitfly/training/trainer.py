from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import torch
from torch import Tensor

from fruitfly.training.il_dataset import ILDataset
from fruitfly.training.losses import anneal_weight, gaussian_kl, log_std_mse, mean_mse


@dataclass(slots=True)
class ILTrainingConfig:
    epochs: int = 1
    batch_size: int = 8
    learning_rate: float = 1e-3
    log_std_mse_weight: float = 0.1


class OfflineILTrainer:
    def __init__(
        self,
        *,
        model: torch.nn.Module,
        dataset: ILDataset,
        output_dir: Path,
        config: ILTrainingConfig,
        device: torch.device | str = "cpu",
    ) -> None:
        self.model = model
        self.dataset = dataset
        self.output_dir = output_dir
        self.config = config
        self.device = torch.device(device)
        self.model.to(self.device)

    def train(self) -> dict[str, float]:
        if len(self.dataset) == 0:
            raise ValueError("ILDataset is empty")

        self._initialize_model()
        optimizer = torch.optim.Adam(self.model.parameters(), lr=self.config.learning_rate)
        total_steps = max(1, self.config.epochs * self._num_batches())
        step = 0
        last_loss = torch.tensor(0.0)

        for epoch in range(1, self.config.epochs + 1):
            for batch in self._iter_batches():
                optimizer.zero_grad()
                obs = self._stack_batch(batch, "observation")
                command = self._stack_batch(batch, "command")
                expert_mean = self._stack_batch(batch, "expert_mean")
                expert_log_std = self._stack_batch(batch, "expert_log_std")

                model_input = torch.cat([obs, command], dim=-1)
                state = self.model.initial_state(batch_size=model_input.shape[0], device=self.device)
                mean, log_std, _ = self.model(model_input, state)

                kl = gaussian_kl(mean, log_std, expert_mean, expert_log_std)
                aux_weight = anneal_weight(step, total_steps)
                mse = mean_mse(mean, expert_mean)
                std_mse = log_std_mse(log_std, expert_log_std)
                loss = kl + aux_weight * (mse + self.config.log_std_mse_weight * std_mse)
                loss.backward()
                optimizer.step()

                last_loss = loss.detach()
                step += 1

            self._write_checkpoint(epoch, optimizer)

        return {"loss": float(last_loss.item()), "steps": float(step)}

    def _num_batches(self) -> int:
        return max(1, (len(self.dataset) + self.config.batch_size - 1) // self.config.batch_size)

    def _initialize_model(self) -> None:
        sample = self.dataset[0]
        obs = torch.tensor(
            [list(sample["observation"]) + list(sample["command"])],
            dtype=torch.float32,
            device=self.device,
        )
        state = self.model.initial_state(batch_size=1, device=self.device)
        with torch.no_grad():
            self.model(obs, state)

    def _iter_batches(self) -> list[list[dict[str, object]]]:
        batches: list[list[dict[str, object]]] = []
        current: list[dict[str, object]] = []
        for index in range(len(self.dataset)):
            current.append(self.dataset[index])
            if len(current) == self.config.batch_size:
                batches.append(current)
                current = []
        if current:
            batches.append(current)
        return batches

    def _stack_batch(self, batch: list[dict[str, object]], key: str) -> Tensor:
        values = [list(batch_item[key]) for batch_item in batch]
        return torch.tensor(values, dtype=torch.float32, device=self.device)

    def _write_checkpoint(self, epoch: int, optimizer: torch.optim.Optimizer) -> None:
        checkpoint_dir = self.output_dir / "checkpoints"
        checkpoint_dir.mkdir(parents=True, exist_ok=True)
        torch.save(
            {
                "epoch": epoch,
                "model": self.model.state_dict(),
                "optimizer": optimizer.state_dict(),
            },
            checkpoint_dir / f"epoch_{epoch:04d}.pt",
        )
