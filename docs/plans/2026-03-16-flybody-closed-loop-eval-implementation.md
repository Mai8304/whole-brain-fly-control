# Flybody Closed-Loop Evaluation Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add the first real closed-loop evaluation path that loads a trained full-brain checkpoint, runs a short `straight walking（稳定直行）` rollout in `flybody（果蝇身体与 MuJoCo 物理环境）`, and writes an engineering-focused summary.

**Architecture:** Reuse the compiled-graph and checkpoint artifacts already produced by the training path. Add a dedicated model loader and rollout wrapper for inference, then run the evaluation inside `.venv-flybody` through a new script that emits both stdout JSON and `summary.json`.

**Tech Stack:** Python 3.13 core code, dedicated `.venv-flybody` environment for rollout, PyTorch inference, existing `fruitfly.models`, `fruitfly.graph`, and `fruitfly.adapters` modules, `pytest`

---

### Task 1: Add Closed-Loop Summary Contract Tests

**Files:**
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_closed_loop_summary.py`

**Step 1: Write the failing test**

Add a test that validates the required summary fields:

- `status`
- `task`
- `checkpoint`
- `steps_requested`
- `steps_completed`
- `terminated_early`
- `has_nan_action`
- `mean_action_norm`
- `final_reward`
- `final_heading_delta`

**Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_closed_loop_summary.py -q
```

Expected: FAIL because no closed-loop summary builder exists yet.

**Step 3: Write minimal implementation**

- Add a tiny summary helper in the evaluation package
- Keep it pure and independent from `flybody`

**Step 4: Run test to verify it passes**

Run the same command and expect PASS.

**Step 5: Commit**

If the repository has been initialized:

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_closed_loop_summary.py
git commit -m "test: define closed-loop evaluation summary contract"
```

### Task 2: Add a Checkpoint + Compiled-Graph Inference Loader

**Files:**
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/checkpoint_loader.py`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_checkpoint_loader.py`

**Step 1: Write the failing test**

Add a test that:

- creates a tiny `WholeBrainRateModel`
- saves a checkpoint
- creates a tiny compiled graph directory
- reloads them together
- confirms the reconstructed model can run inference

**Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_checkpoint_loader.py -q
```

Expected: FAIL because no loader exists yet.

**Step 3: Write minimal implementation**

- load checkpoint metadata
- load compiled graph tensors
- rebuild `WholeBrainRateModel`
- restore weights

Keep the loader intentionally narrow: first version only needs the current model family.

**Step 4: Run test to verify it passes**

Run the same command and expect PASS.

**Step 5: Commit**

If the repository has been initialized:

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/checkpoint_loader.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_checkpoint_loader.py
git commit -m "feat: add closed-loop checkpoint loader"
```

### Task 3: Add a Rollout Policy Wrapper for Inference

**Files:**
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/policy_wrapper.py`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_policy_wrapper.py`

**Step 1: Write the failing test**

Add a test that:

- creates a tiny model
- wraps it in the evaluation policy wrapper
- feeds two consecutive observations
- confirms:
  - action shape is correct
  - hidden state persists across steps

**Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_policy_wrapper.py -q
```

Expected: FAIL because no wrapper exists yet.

**Step 3: Write minimal implementation**

- hold model reference
- initialize and update hidden state
- adapt observation + command into model input
- emit deterministic action means for evaluation

**Step 4: Run test to verify it passes**

Run the same command and expect PASS.

**Step 5: Commit**

If the repository has been initialized:

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/policy_wrapper.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_policy_wrapper.py
git commit -m "feat: add closed-loop policy wrapper"
```

### Task 4: Implement the Flybody Closed-Loop Evaluation Script

**Files:**
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/scripts/eval_flybody_closed_loop.py`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/walking_eval.py`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/scripts/test_eval_flybody_closed_loop.py`

**Step 1: Write the failing test**

Add a script-level test that monkeypatches the environment and the loader so the CLI can be exercised without real `flybody`, then asserts:

- exit code `0`
- stdout JSON contains required fields

**Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/scripts/test_eval_flybody_closed_loop.py -q
```

Expected: FAIL because the script does not exist yet.

**Step 3: Write minimal implementation**

- accept:
  - `--checkpoint`
  - `--compiled-graph-dir`
  - `--task`
  - `--max-steps`
  - `--output-dir`
- run a short rollout
- compute summary
- print JSON
- write `summary.json`

**Step 4: Run test to verify it passes**

Run the same command and expect PASS.

**Step 5: Commit**

If the repository has been initialized:

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/scripts/eval_flybody_closed_loop.py /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/walking_eval.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/scripts/test_eval_flybody_closed_loop.py
git commit -m "feat: add flybody closed-loop evaluation CLI"
```

### Task 5: Run the First Real Closed-Loop Evaluation

**Files:**
- Input checkpoint: `/Users/zhuangwei/Downloads/coding/Fruitfly/outputs/train/full_graph_straight_v1/checkpoints/epoch_0001.pt`
- Input graph: `/Users/zhuangwei/Downloads/coding/Fruitfly/outputs/compiled/flywire_public_full_v783/`
- Output: `/Users/zhuangwei/Downloads/coding/Fruitfly/outputs/eval/full_graph_straight_v1/`

**Step 1: Run the real evaluation command**

Run from the dedicated `flybody` environment:

```bash
./.venv-flybody/bin/python /Users/zhuangwei/Downloads/coding/Fruitfly/scripts/eval_flybody_closed_loop.py \
  --checkpoint /Users/zhuangwei/Downloads/coding/Fruitfly/outputs/train/full_graph_straight_v1/checkpoints/epoch_0001.pt \
  --compiled-graph-dir /Users/zhuangwei/Downloads/coding/Fruitfly/outputs/compiled/flywire_public_full_v783 \
  --task straight_walking \
  --max-steps 64 \
  --output-dir /Users/zhuangwei/Downloads/coding/Fruitfly/outputs/eval/full_graph_straight_v1
```

**Step 2: Verify the evaluation outputs**

Check:

- stdout JSON exists
- `summary.json` exists
- fields are present
- no crash occurred

**Step 3: Add one narrow integration test only if the real run exposes a contract mismatch**

- keep it focused
- avoid speculative generalization

**Step 4: Commit**

If the repository has been initialized:

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/outputs/eval/full_graph_straight_v1
git commit -m "feat: run first flybody closed-loop evaluation"
```

### Task 6: Update Documentation

**Files:**
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/README.md`

**Step 1: Add a short closed-loop evaluation section**

Document:

- the new CLI path
- the dedicated `.venv-flybody` requirement
- the meaning of the engineering summary fields

**Step 2: Run the relevant tests**

Run:

```bash
python3 -m pytest \
  /Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation \
  /Users/zhuangwei/Downloads/coding/Fruitfly/tests/scripts -q
```

Expected: PASS.

**Step 3: Commit**

If the repository has been initialized:

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/README.md
git commit -m "docs: describe flybody closed-loop evaluation"
```
