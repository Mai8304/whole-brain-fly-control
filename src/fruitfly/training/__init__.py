from .il_dataset import ILDataset, write_il_dataset

__all__ = ["ILDataset", "write_il_dataset"]

try:
    from .losses import anneal_weight, gaussian_kl, log_std_mse, mean_mse
    from .trainer import ILTrainingConfig, OfflineILTrainer
except ModuleNotFoundError as exc:
    if exc.name != "torch":
        raise
else:
    __all__.extend(
        [
            "ILTrainingConfig",
            "OfflineILTrainer",
            "anneal_weight",
            "gaussian_kl",
            "log_std_mse",
            "mean_mse",
        ]
    )
