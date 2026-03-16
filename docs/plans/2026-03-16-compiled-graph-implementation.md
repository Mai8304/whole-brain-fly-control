# Compiled Graph Standardization Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a standard compiled-graph artifact directory from the completed full-brain normalized snapshot and make `train_il.py` consume it directly for the first real full-brain `IL-only（仅模仿学习）` smoke test.

**Architecture:** Keep graph compilation as a distinct stage between snapshot export and training. Extend the graph compiler to write a standard artifact directory, add a graph-loader path for training, and keep the existing model largely unchanged for the first integration so that only the input contract changes.

**Tech Stack:** Python 3.13 core code, PyTorch, `pyarrow`/Parquet, existing `fruitfly.graph` and `fruitfly.training` modules, `pytest`

---

### Task 1: Define the Compiled Graph Artifact Contract in Tests

**Files:**
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/graph/test_compiled_graph_artifacts.py`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/README.md`

**Step 1: Write the failing test**

```python
from pathlib import Path


def test_compiled_graph_directory_contains_required_files(tmp_path: Path) -> None:
    compiled_dir = tmp_path / "compiled"
    compiled_dir.mkdir()

    expected = {
        "manifest.json",
        "config.json",
        "node_index.parquet",
        "edge_index.pt",
        "io_masks.pt",
        "graph_stats.json",
    }

    assert expected.issubset({path.name for path in compiled_dir.iterdir()})
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/graph/test_compiled_graph_artifacts.py -q`

Expected: FAIL because no helper exists yet to create or validate a compiled graph directory.

**Step 3: Write minimal implementation**

- Document the compiled graph contract in `README.md`
- Replace the placeholder test with one that calls the future compiler entry point and asserts the six required files are produced

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/graph/test_compiled_graph_artifacts.py -q`

Expected: PASS.

**Step 5: Commit**

If the repository has been initialized:

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/README.md /Users/zhuangwei/Downloads/coding/Fruitfly/tests/graph/test_compiled_graph_artifacts.py
git commit -m "test: define compiled graph artifact contract"
```

### Task 2: Extend Graph Types to Support Artifact Serialization

**Files:**
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/graph/types.py`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/graph/io.py`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/graph/test_graph_io.py`

**Step 1: Write the failing test**

```python
from pathlib import Path


def test_save_and_load_compiled_graph_round_trip(tmp_path: Path) -> None:
    from fruitfly.graph.types import CompiledGraph
    from fruitfly.graph.io import load_compiled_graph, save_compiled_graph

    graph = CompiledGraph(
        node_index={10: 0, 20: 1},
        edge_index=[(0, 1)],
        afferent_mask=[True, False],
        intrinsic_mask=[False, False],
        efferent_mask=[False, True],
    )

    compiled_dir = tmp_path / "compiled"
    save_compiled_graph(graph=graph, compiled_dir=compiled_dir, snapshot_id="test_snapshot")
    loaded = load_compiled_graph(compiled_dir)

    assert loaded.node_index == graph.node_index
    assert loaded.edge_index == graph.edge_index
    assert loaded.afferent_mask == graph.afferent_mask
    assert loaded.efferent_mask == graph.efferent_mask
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/graph/test_graph_io.py -q`

Expected: FAIL because graph save/load helpers do not exist.

**Step 3: Write minimal implementation**

- Extend `CompiledGraph` if needed with lightweight metadata helpers
- Add `save_compiled_graph(...)`
- Add `load_compiled_graph(...)`
- Write:
  - `manifest.json`
  - `config.json`
  - `node_index.parquet`
  - `edge_index.pt`
  - `io_masks.pt`
  - `graph_stats.json`

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/graph/test_graph_io.py -q`

Expected: PASS.

**Step 5: Commit**

If the repository has been initialized:

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/graph/types.py /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/graph/io.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/graph/test_graph_io.py
git commit -m "feat: add compiled graph serialization"
```

### Task 3: Upgrade the Compiler CLI to Emit a Standard Compiled Graph Directory

**Files:**
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/graph/compiler.py`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/scripts/compile_graph.py`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/scripts/test_compile_graph_cli.py`

**Step 1: Write the failing test**

```python
from pathlib import Path
import subprocess
import sys


def test_compile_graph_cli_writes_standard_directory(tmp_path: Path) -> None:
    snapshot_dir = Path("/Users/zhuangwei/Downloads/coding/Fruitfly/outputs/snapshots/flywire_public_smoke_h1b")
    compiled_dir = tmp_path / "compiled"

    result = subprocess.run(
        [
            sys.executable,
            "/Users/zhuangwei/Downloads/coding/Fruitfly/scripts/compile_graph.py",
            "--snapshot-dir",
            str(snapshot_dir),
            "--output-dir",
            str(compiled_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
    assert (compiled_dir / "edge_index.pt").exists()
    assert (compiled_dir / "io_masks.pt").exists()
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/scripts/test_compile_graph_cli.py -q`

Expected: FAIL because the CLI currently expects `--output` for a summary JSON and does not write a compiled directory.

**Step 3: Write minimal implementation**

- Keep `compile_snapshot(...)` focused on in-memory compilation
- Change the CLI to accept `--output-dir`
- Call `save_compiled_graph(...)`
- Print a short JSON summary to stdout for scripting use

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/scripts/test_compile_graph_cli.py -q`

Expected: PASS.

**Step 5: Commit**

If the repository has been initialized:

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/graph/compiler.py /Users/zhuangwei/Downloads/coding/Fruitfly/scripts/compile_graph.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/scripts/test_compile_graph_cli.py
git commit -m "feat: emit standard compiled graph directories"
```

### Task 4: Add a Training-Side Loader for Compiled Graph Directories

**Files:**
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/scripts/train_il.py`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/scripts/test_train_il_compiled_graph.py`

**Step 1: Write the failing test**

```python
from pathlib import Path
import subprocess
import sys


def test_train_il_accepts_compiled_graph_dir(tmp_path: Path) -> None:
    compiled_dir = tmp_path / "compiled"
    dataset = Path("/Users/zhuangwei/Downloads/coding/Fruitfly/data/datasets/walking_il/straight_smoke.jsonl")
    output_dir = tmp_path / "train_out"

    result = subprocess.run(
        [
            sys.executable,
            "/Users/zhuangwei/Downloads/coding/Fruitfly/scripts/train_il.py",
            "--dataset",
            str(dataset),
            "--compiled-graph-dir",
            str(compiled_dir),
            "--output-dir",
            str(output_dir),
        ],
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/scripts/test_train_il_compiled_graph.py -q`

Expected: FAIL because the training CLI does not yet accept `--compiled-graph-dir`.

**Step 3: Write minimal implementation**

- Add `--compiled-graph-dir`
- Load the compiled graph directory
- Derive:
  - `num_nodes`
  - `afferent_indices`
  - `efferent_indices`
  - `edge_index`
- Preserve legacy flags for fallback debugging only

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/scripts/test_train_il_compiled_graph.py -q`

Expected: PASS.

**Step 5: Commit**

If the repository has been initialized:

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/scripts/train_il.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/scripts/test_train_il_compiled_graph.py
git commit -m "feat: load compiled graph in IL trainer"
```

### Task 5: Compile the Real Full-Brain Snapshot

**Files:**
- Input: `/Users/zhuangwei/Downloads/coding/Fruitfly/outputs/snapshots/flywire_public_full_v783/`
- Output: `/Users/zhuangwei/Downloads/coding/Fruitfly/outputs/compiled/flywire_public_full_v783/`

**Step 1: Run the real compiler on the completed full-brain snapshot**

Run:

```bash
python3 /Users/zhuangwei/Downloads/coding/Fruitfly/scripts/compile_graph.py \
  --snapshot-dir /Users/zhuangwei/Downloads/coding/Fruitfly/outputs/snapshots/flywire_public_full_v783 \
  --output-dir /Users/zhuangwei/Downloads/coding/Fruitfly/outputs/compiled/flywire_public_full_v783
```

**Step 2: Verify the compiled artifact set exists**

Run:

```bash
ls -lh /Users/zhuangwei/Downloads/coding/Fruitfly/outputs/compiled/flywire_public_full_v783
```

Expected:

- `manifest.json`
- `config.json`
- `node_index.parquet`
- `edge_index.pt`
- `io_masks.pt`
- `graph_stats.json`

**Step 3: Add a narrow integration test if the real output reveals a schema edge case**

- Create or update a single integration test around the discovered edge case
- Do not generalize pre-emptively

**Step 4: Commit**

If the repository has been initialized:

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/outputs/compiled/flywire_public_full_v783
git commit -m "chore: compile full-brain graph artifacts"
```

### Task 6: Run the First Real Full-Brain IL Smoke Test

**Files:**
- Input dataset: `/Users/zhuangwei/Downloads/coding/Fruitfly/data/datasets/walking_il/straight_smoke.jsonl`
- Input graph: `/Users/zhuangwei/Downloads/coding/Fruitfly/outputs/compiled/flywire_public_full_v783/`
- Output: `/Users/zhuangwei/Downloads/coding/Fruitfly/outputs/train/full_graph_straight_smoke/`
- Modify if needed: `/Users/zhuangwei/Downloads/coding/Fruitfly/README.md`

**Step 1: Run the smoke training command**

Run:

```bash
python3 /Users/zhuangwei/Downloads/coding/Fruitfly/scripts/train_il.py \
  --dataset /Users/zhuangwei/Downloads/coding/Fruitfly/data/datasets/walking_il/straight_smoke.jsonl \
  --compiled-graph-dir /Users/zhuangwei/Downloads/coding/Fruitfly/outputs/compiled/flywire_public_full_v783 \
  --output-dir /Users/zhuangwei/Downloads/coding/Fruitfly/outputs/train/full_graph_straight_smoke \
  --epochs 1 \
  --batch-size 1
```

**Step 2: Verify the smoke-test outputs**

Run:

```bash
ls -R /Users/zhuangwei/Downloads/coding/Fruitfly/outputs/train/full_graph_straight_smoke
```

Expected:

- finite training metrics
- at least one checkpoint file
- no `NaN`
- no OOM

**Step 3: Update README with the new primary training path**

- Add one short section showing:
  - snapshot -> compile -> train
  - `--compiled-graph-dir` as the preferred interface

**Step 4: Run the relevant test set**

Run:

```bash
python3 -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/graph /Users/zhuangwei/Downloads/coding/Fruitfly/tests/scripts -q
```

Expected: PASS.

**Step 5: Commit**

If the repository has been initialized:

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/README.md /Users/zhuangwei/Downloads/coding/Fruitfly/outputs/train/full_graph_straight_smoke
git commit -m "feat: run first full-brain IL smoke test"
```
