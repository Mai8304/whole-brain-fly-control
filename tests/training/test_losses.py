def test_kl_loss_is_zero_for_identical_distributions() -> None:
    import torch

    from fruitfly.training.losses import gaussian_kl

    mean = torch.zeros(2, 3)
    log_std = torch.zeros(2, 3)

    assert torch.isclose(
        gaussian_kl(mean, log_std, mean, log_std),
        torch.tensor(0.0),
    )
