import subprocess
import sys
from pathlib import Path


def test_train_il_accepts_compiled_graph_dir(tmp_path: Path) -> None:
    from fruitfly.graph import CompiledGraph, save_compiled_graph
    from fruitfly.training import write_il_dataset

    compiled_dir = tmp_path / "compiled"
    dataset = tmp_path / "dataset.jsonl"
    output_dir = tmp_path / "train_out"

    save_compiled_graph(
        graph=CompiledGraph(
            node_index={10: 0, 20: 1, 30: 2},
            edge_index=[(0, 1), (1, 2)],
            afferent_mask=[True, False, False],
            intrinsic_mask=[False, True, False],
            efferent_mask=[False, False, True],
        ),
        compiled_dir=compiled_dir,
        snapshot_id="test_snapshot",
    )
    write_il_dataset(
        dataset,
        [
            {
                "observation": [0.1, 0.2, 0.3],
                "command": [0.0, 0.1],
                "expert_mean": [0.5, 0.6, 0.7],
                "expert_log_std": [0.0, 0.0, 0.0],
            }
        ],
    )

    result = subprocess.run(
        [
            sys.executable,
            "scripts/train_il.py",
            "--dataset",
            str(dataset),
            "--compiled-graph-dir",
            str(compiled_dir),
            "--output-dir",
            str(output_dir),
            "--epochs",
            "1",
            "--batch-size",
            "1",
            "--action-dim",
            "3",
            "--hidden-dim",
            "4",
        ],
        capture_output=True,
        text=True,
        check=False,
        cwd=Path(__file__).resolve().parents[2],
    )

    assert result.returncode == 0
    assert (output_dir / "checkpoints" / "epoch_0001.pt").exists()
