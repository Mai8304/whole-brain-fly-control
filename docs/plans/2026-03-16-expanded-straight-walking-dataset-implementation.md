# Expanded Straight-Walking Dataset Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Export a larger real `straight walking（稳定直行）` expert dataset with minimal metadata and run a more meaningful full-brain `IL-only（仅模仿学习）` training pass on it.

**Architecture:** Keep the existing `flybody` expert export contract stable, add only lightweight metadata fields, then generate a larger dataset with `episodes=3` and `max_steps=128`. Reuse the existing full-brain `compiled graph（训练编译图）` path for the next training run.

**Tech Stack:** Python 3.13 core code, dedicated `.venv-flybody` export environment, PyTorch training stack, existing `fruitfly.adapters` and `fruitfly.training` modules, `pytest`

---

### Task 1: Extend the Export Contract Tests for Metadata Fields

**Files:**
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/adapters/test_flybody_export.py`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/training/test_il_dataset_export_contract.py`

**Step 1: Write the failing test**

Add assertions that exported records now also include:

- `episode_id`
- `step_id`
- `task`

Use a fake expert source with at least two records from different steps.

**Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest \
  /Users/zhuangwei/Downloads/coding/Fruitfly/tests/adapters/test_flybody_export.py \
  /Users/zhuangwei/Downloads/coding/Fruitfly/tests/training/test_il_dataset_export_contract.py -q
```

Expected: FAIL because metadata fields are not exported yet.

**Step 3: Write minimal implementation**

- Update the export helpers so each row includes:
  - `episode_id`
  - `step_id`
  - `task="straight_walking"`

**Step 4: Run test to verify it passes**

Run the same test command again and expect PASS.

**Step 5: Commit**

If the repository has been initialized:

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/tests/adapters/test_flybody_export.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/training/test_il_dataset_export_contract.py
git commit -m "test: extend straight walking export contract"
```

### Task 2: Update the Real Exporter to Emit Metadata Without Breaking Training

**Files:**
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/adapters/flybody_export.py`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/scripts/build_il_dataset.py`

**Step 1: Write the failing test**

Add a focused test that asserts:

- exported rows keep the four training fields unchanged
- metadata fields are present
- `task` is `straight_walking`

**Step 2: Run test to verify it fails**

Run the affected adapter tests and expect FAIL.

**Step 3: Write minimal implementation**

- Track episode and step counters during rollout
- Emit metadata fields in each row
- Keep CLI arguments unchanged for this milestone

**Step 4: Run test to verify it passes**

Run the same tests again and expect PASS.

**Step 5: Commit**

If the repository has been initialized:

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/adapters/flybody_export.py /Users/zhuangwei/Downloads/coding/Fruitfly/scripts/build_il_dataset.py
git commit -m "feat: add metadata to straight walking export"
```

### Task 3: Export the First Expanded Real Dataset

**Files:**
- Output: `/Users/zhuangwei/Downloads/coding/Fruitfly/data/datasets/walking_il/straight_v1.jsonl`

**Step 1: Run the real export command**

Run from the dedicated `flybody` environment:

```bash
./.venv-flybody/bin/python /Users/zhuangwei/Downloads/coding/Fruitfly/scripts/build_il_dataset.py \
  --output /Users/zhuangwei/Downloads/coding/Fruitfly/data/datasets/walking_il/straight_v1.jsonl \
  --episodes 3 \
  --max-steps 128 \
  --policy-dir /Users/zhuangwei/Downloads/coding/Fruitfly/outputs/flybody-data/trained-fly-policies
```

**Step 2: Verify the exported dataset shape**

Run a small inspection command to report:

- sample count
- first row keys
- unique `episode_id`
- max `step_id`

Expected:

- sample count greater than the smoke dataset
- metadata fields present
- multiple episode IDs visible

**Step 3: Commit**

If the repository has been initialized:

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/data/datasets/walking_il/straight_v1.jsonl
git commit -m "chore: export expanded straight walking dataset"
```

### Task 4: Run a Larger Full-Brain IL Training Pass

**Files:**
- Input dataset: `/Users/zhuangwei/Downloads/coding/Fruitfly/data/datasets/walking_il/straight_v1.jsonl`
- Input graph: `/Users/zhuangwei/Downloads/coding/Fruitfly/outputs/compiled/flywire_public_full_v783/`
- Output: `/Users/zhuangwei/Downloads/coding/Fruitfly/outputs/train/full_graph_straight_v1/`

**Step 1: Run the training command**

Run:

```bash
python3 /Users/zhuangwei/Downloads/coding/Fruitfly/scripts/train_il.py \
  --dataset /Users/zhuangwei/Downloads/coding/Fruitfly/data/datasets/walking_il/straight_v1.jsonl \
  --compiled-graph-dir /Users/zhuangwei/Downloads/coding/Fruitfly/outputs/compiled/flywire_public_full_v783 \
  --output-dir /Users/zhuangwei/Downloads/coding/Fruitfly/outputs/train/full_graph_straight_v1 \
  --epochs 1 \
  --batch-size 1 \
  --hidden-dim 4
```

**Step 2: Verify outputs**

Check:

- finite loss
- checkpoint exists
- no `NaN`
- no OOM

**Step 3: Add or update one narrow integration test if the real run exposes a contract edge case**

- Keep it narrow
- Do not generalize without evidence

**Step 4: Commit**

If the repository has been initialized:

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/outputs/train/full_graph_straight_v1
git commit -m "feat: train on expanded straight walking dataset"
```

### Task 5: Update the README With the New Recommended Dataset Step

**Files:**
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/README.md`

**Step 1: Add a short section**

Document:

- `straight_v1.jsonl` as the next-step dataset after `straight_smoke.jsonl`
- `episodes=3`
- `max_steps=128`
- the fact that metadata fields are included for analysis but training remains backward-compatible

**Step 2: Run the relevant tests**

Run:

```bash
python3 -m pytest \
  /Users/zhuangwei/Downloads/coding/Fruitfly/tests/adapters \
  /Users/zhuangwei/Downloads/coding/Fruitfly/tests/training \
  /Users/zhuangwei/Downloads/coding/Fruitfly/tests/scripts -q
```

Expected: PASS.

**Step 3: Commit**

If the repository has been initialized:

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/README.md
git commit -m "docs: describe expanded straight walking dataset"
```
