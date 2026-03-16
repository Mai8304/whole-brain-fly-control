from __future__ import annotations

import torch
from torch import Tensor


def gaussian_kl(
    student_mean: Tensor,
    student_log_std: Tensor,
    target_mean: Tensor,
    target_log_std: Tensor,
) -> Tensor:
    target_var = torch.exp(target_log_std * 2.0)
    student_var = torch.exp(student_log_std * 2.0)
    kl = (
        student_log_std
        - target_log_std
        + (target_var + (target_mean - student_mean).pow(2)) / (2.0 * student_var)
        - 0.5
    )
    return kl.mean()


def mean_mse(student_mean: Tensor, target_mean: Tensor) -> Tensor:
    return torch.mean((student_mean - target_mean).pow(2))


def log_std_mse(student_log_std: Tensor, target_log_std: Tensor) -> Tensor:
    return torch.mean((student_log_std - target_log_std).pow(2))


def anneal_weight(step: int, total_steps: int, *, floor: float = 0.1) -> float:
    if total_steps <= 1:
        return 1.0
    progress = min(max(step, 0), total_steps - 1) / float(total_steps - 1)
    return 1.0 - (1.0 - floor) * progress
