# Flybody Straight-Walking IL Dataset Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the first real `flybody（果蝇身体与 MuJoCo 物理环境）` expert-data slice by exporting a small `straight walking（稳定直行）` dataset and proving it can drive one minimal `IL smoke test（模仿学习烟测）`.

**Architecture:** Keep `flybody` in a dedicated environment and use file-based handoff into the main project environment. Replace the current dataset-builder stub with a real expert rollout exporter, keep the dataset contract unchanged, and validate the handoff by running the existing `train_il.py` pipeline on the exported data.

**Tech Stack:** Python 3.11+ main project env, dedicated `flybody` env, `jsonl`, `pytest`, existing `fruitfly` adapters and trainer

---

### Task 1: Add flybody Slice Design Notes to the README and Dependency Placeholder

**Files:**
- Modify: `README.md`
- Modify: `pyproject.toml`
- Create: `tests/project/test_embodiment_dependency_group.py`

**Step 1: Write the failing test**

```python
def test_embodiment_dependency_group_exists() -> None:
    import tomllib
    from pathlib import Path

    payload = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    optional = payload["project"]["optional-dependencies"]

    assert "embodiment" in optional
```

**Step 2: Run test to verify it fails or captures the current placeholder state**

Run: `python3 -m pytest tests/project/test_embodiment_dependency_group.py -q`
Expected: PASS or FAIL depending on current file state; if it already passes, keep the test and tighten README assertions instead.

**Step 3: Write minimal implementation**

- keep or refine the `embodiment` extras group
- document the new slice in `README.md`
- explain that `flybody` export runs in a separate environment and writes dataset files back into this repo

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/project/test_embodiment_dependency_group.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add README.md pyproject.toml tests/project/test_embodiment_dependency_group.py
git commit -m "docs: describe flybody straight-walking slice"
```

### Task 2: Extend the IL Dataset Contract Tests for Real Export Records

**Files:**
- Modify: `src/fruitfly/training/il_dataset.py`
- Create: `tests/training/test_il_dataset_export_contract.py`

**Step 1: Write the failing test**

```python
from pathlib import Path


def test_write_il_dataset_persists_real_contract_fields(tmp_path: Path) -> None:
    from fruitfly.training.il_dataset import ILDataset, write_il_dataset

    dataset_path = tmp_path / "dataset.jsonl"
    write_il_dataset(
        dataset_path,
        [
            {
                "observation": [1.0, 2.0],
                "command": [0.5],
                "expert_mean": [0.1, 0.2],
                "expert_log_std": [-1.0, -1.0],
            }
        ],
    )

    dataset = ILDataset(dataset_path)
    sample = dataset[0]

    assert len(dataset) == 1
    assert list(sample["observation"]) == [1.0, 2.0]
    assert list(sample["command"]) == [0.5]
```

**Step 2: Run test to verify current behavior**

Run: `python3 -m pytest tests/training/test_il_dataset_export_contract.py -q`
Expected: PASS or expose missing assumptions that need to be stabilized before `flybody` export is added.

**Step 3: Write minimal implementation**

- tighten dataset writer/reader behavior if necessary
- ensure the exported contract remains exactly:
  - `observation`
  - `command`
  - `expert_mean`
  - `expert_log_std`

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/training/test_il_dataset_export_contract.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add src/fruitfly/training/il_dataset.py tests/training/test_il_dataset_export_contract.py
git commit -m "test: lock IL dataset export contract"
```

### Task 3: Add a flybody Export Module Contract with Injectable Expert Source

**Files:**
- Create: `src/fruitfly/adapters/flybody_export.py`
- Create: `tests/adapters/test_flybody_export.py`

**Step 1: Write the failing test**

```python
def test_export_straight_walking_records_from_injected_source() -> None:
    from fruitfly.adapters.flybody_export import export_straight_walking_records

    class FakeExpertSource:
        def rollout(self, episodes, max_steps):
            return [
                {
                    "observation": {"proprio": [1.0], "command": [0.2]},
                    "command": [0.2],
                    "expert_mean": [0.1, 0.2],
                    "expert_log_std": [-1.0, -1.0],
                }
            ]

    records = export_straight_walking_records(
        expert_source=FakeExpertSource(),
        episodes=1,
        max_steps=10,
    )

    assert len(records) == 1
    assert records[0]["expert_mean"] == [0.1, 0.2]
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/adapters/test_flybody_export.py -q`
Expected: FAIL because the exporter module does not exist yet.

**Step 3: Write minimal implementation**

Implement:

- `export_straight_walking_records(...)`
- support for an injected `expert_source`
- observation flattening through the existing adapter
- output records in the current IL contract

Keep the first version independent from the real `flybody` import so unit tests stay network- and simulator-free.

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/adapters/test_flybody_export.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add src/fruitfly/adapters/flybody_export.py tests/adapters/test_flybody_export.py
git commit -m "feat: add flybody expert export contract"
```

### Task 4: Replace build_il_dataset.py Stub with a Real Export CLI

**Files:**
- Modify: `scripts/build_il_dataset.py`
- Modify: `src/fruitfly/adapters/flybody_export.py`
- Create: `tests/scripts/test_build_il_dataset.py`

**Step 1: Write the failing test**

```python
from pathlib import Path


def test_build_il_dataset_cli_writes_nonempty_dataset(tmp_path: Path, monkeypatch) -> None:
    from scripts import build_il_dataset

    monkeypatch.setattr(
        build_il_dataset,
        "export_straight_walking_records",
        lambda **_: [
            {
                "observation": [1.0],
                "command": [0.2],
                "expert_mean": [0.1],
                "expert_log_std": [-1.0],
            }
        ],
    )

    output_path = tmp_path / "dataset.jsonl"
    build_il_dataset.main(["--output", str(output_path), "--episodes", "1", "--max-steps", "5"])

    assert output_path.exists()
    assert output_path.read_text(encoding="utf-8").strip()
```

**Step 2: Run test to verify it fails**

Run: `python3 -m pytest tests/scripts/test_build_il_dataset.py -q`
Expected: FAIL because the CLI is still a stub and does not accept the new arguments.

**Step 3: Write minimal implementation**

Add CLI options:

- `--output`
- `--episodes`
- `--max-steps`
- optional environment or backend hint if needed later

Implementation should:

- call the export helper
- write a non-empty dataset
- print a small summary

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/scripts/test_build_il_dataset.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add scripts/build_il_dataset.py src/fruitfly/adapters/flybody_export.py tests/scripts/test_build_il_dataset.py
git commit -m "feat: add real IL dataset export CLI"
```

### Task 5: Add a Minimal Training Smoke Test Against a Real-Shaped Dataset

**Files:**
- Create: `tests/integration/test_straight_walking_il_smoke.py`
- Modify: `scripts/train_il.py` only if required for tighter smoke control

**Step 1: Write the failing test**

```python
from pathlib import Path


def test_train_il_runs_on_exported_straight_walking_dataset(tmp_path: Path) -> None:
    from fruitfly.training.il_dataset import write_il_dataset
    from fruitfly.training.trainer import train_il_epoch
    from fruitfly.models.rate_model import WholeBrainRateModel

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
    metrics = train_il_epoch(model=model, dataset_path=dataset_path, batch_size=1)

    assert metrics["loss"] == metrics["loss"]
```

**Step 2: Run test to verify it fails or exposes missing API glue**

Run: `python3 -m pytest tests/integration/test_straight_walking_il_smoke.py -q`
Expected: FAIL or force clarification of the current training entrypoints.

**Step 3: Write minimal implementation**

- adapt the smoke test to the real trainer API
- only change production code if the current API blocks a minimal real-dataset run
- keep the smoke tiny and deterministic

**Step 4: Run test to verify it passes**

Run: `python3 -m pytest tests/integration/test_straight_walking_il_smoke.py -q`
Expected: PASS

**Step 5: Commit**

```bash
git add tests/integration/test_straight_walking_il_smoke.py scripts/train_il.py
git commit -m "test: add straight-walking IL smoke coverage"
```

### Task 6: Document the Dedicated flybody Export Environment and Manual Smoke Run

**Files:**
- Modify: `README.md`
- Create: `docs/plans/2026-03-12-flybody-straight-walking-il-design.md`

**Step 1: Write the docs delta**

Document:

- the separate `flybody` environment requirement
- the command to export a small straight-walking dataset
- the command to train on it in the main environment
- the expected success signals

**Step 2: Run a manual smoke sequence**

Run, in order:

```bash
python3 scripts/build_il_dataset.py --output data/datasets/walking_il/straight_smoke.jsonl --episodes 1 --max-steps 32
python3 scripts/train_il.py --dataset data/datasets/walking_il/straight_smoke.jsonl --output-dir outputs/train/straight_smoke --num-nodes 139246
```

Expected:

- dataset file is non-empty
- training completes
- loss is finite
- checkpoint exists

**Step 3: Commit**

```bash
git add README.md docs/plans/2026-03-12-flybody-straight-walking-il-design.md
git commit -m "docs: add flybody straight-walking runbook"
```
