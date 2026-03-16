from pathlib import Path


def test_smoke_configs_exist() -> None:
    assert Path("configs/model/full_graph_il.yaml").exists()
    assert Path("configs/train/walking_il.yaml").exists()
    assert Path("configs/eval/walking_closed_loop.yaml").exists()
