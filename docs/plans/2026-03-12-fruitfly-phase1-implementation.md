# Fruitfly Phase 1 Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a reproducible full-graph `IL-only（仅模仿学习）` walking pipeline that compiles a frozen FlyWire snapshot into a whole-brain controller and runs it in `flybody（果蝇身体与 MuJoCo 物理环境）`.

**Architecture:** Freeze the connectome as a local snapshot, normalize it into repository-owned schemas, compile it into sparse full-graph training artifacts, then train a `whole-brain rate model（全脑速率模型）` to imitate the `flybody` expert controller. Keep the body adapter, graph compiler, and trainer decoupled so later `PPO fine-tune（强化学习微调）` can be added without reworking the data path.

**Tech Stack:** Python 3.11, PyTorch, `flybody`, parquet/pyarrow, numpy, pytest

---

### Task 1: Bootstrap Repository and Tooling

**Files:**
- Create: `README.md`
- Create: `pyproject.toml`
- Create: `src/fruitfly/__init__.py`
- Create: `tests/conftest.py`

**Step 1: Write the failing test**

```python
def test_package_imports() -> None:
    import fruitfly

    assert fruitfly.__all__ == []
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests -q`
Expected: FAIL because `fruitfly` package does not exist yet.

**Step 3: Write minimal implementation**

```python
__all__ = []
```

Add a minimal `pyproject.toml` with package metadata, Python version, pytest config, and core dependencies.

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests -q`
Expected: PASS for the bootstrap import test.

**Step 5: Commit**

```bash
git add README.md pyproject.toml src/fruitfly/__init__.py tests/conftest.py
git commit -m "chore: bootstrap fruitfly package"
```

### Task 2: Define Snapshot Manifest and Normalized Schemas

**Files:**
- Create: `src/fruitfly/snapshot/schema.py`
- Create: `src/fruitfly/snapshot/io.py`
- Create: `configs/snapshot/flywire_fafb_v783.yaml`
- Create: `tests/snapshot/test_schema.py`

**Step 1: Write the failing test**

```python
def test_validate_normalized_snapshot_tables() -> None:
    from fruitfly.snapshot.schema import validate_nodes_columns

    columns = {"source_id", "dataset_version", "hemisphere", "flow_role", "is_active"}
    assert validate_nodes_columns(columns)
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/snapshot/test_schema.py -q`
Expected: FAIL because the schema module is missing.

**Step 3: Write minimal implementation**

Implement:
- required column constants for nodes, edges, and partitions
- manifest loader
- lightweight validators that raise clear errors on missing fields

```python
REQUIRED_NODE_COLUMNS = {...}

def validate_nodes_columns(columns: set[str]) -> bool:
    missing = REQUIRED_NODE_COLUMNS - columns
    if missing:
        raise ValueError(f"Missing node columns: {sorted(missing)}")
    return True
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/snapshot/test_schema.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/fruitfly/snapshot/schema.py src/fruitfly/snapshot/io.py configs/snapshot/flywire_fafb_v783.yaml tests/snapshot/test_schema.py
git commit -m "feat: add snapshot schema validation"
```

### Task 3: Implement Graph Compiler for Full-Graph Artifacts

**Files:**
- Create: `src/fruitfly/graph/compiler.py`
- Create: `src/fruitfly/graph/types.py`
- Create: `scripts/compile_graph.py`
- Create: `tests/graph/test_compiler.py`

**Step 1: Write the failing test**

```python
def test_compiler_creates_contiguous_indices() -> None:
    from fruitfly.graph.compiler import compile_snapshot

    compiled = compile_snapshot(
        nodes=[
            {"source_id": 10, "flow_role": "afferent", "is_active": True},
            {"source_id": 20, "flow_role": "intrinsic", "is_active": True},
        ],
        edges=[{"pre_id": 10, "post_id": 20, "is_active": True}],
    )

    assert compiled.node_index == {10: 0, 20: 1}
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/graph/test_compiler.py -q`
Expected: FAIL because compiler code does not exist yet.

**Step 3: Write minimal implementation**

Implement:
- active node filtering
- contiguous index assignment
- edge remapping
- `afferent / intrinsic / efferent` masks
- sparse adjacency export

```python
node_index = {source_id: idx for idx, source_id in enumerate(active_ids)}
edge_index = torch.tensor([[...], [...]], dtype=torch.long)
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/graph/test_compiler.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/fruitfly/graph/compiler.py src/fruitfly/graph/types.py scripts/compile_graph.py tests/graph/test_compiler.py
git commit -m "feat: add full-graph compiler"
```

### Task 4: Build the flybody Observation Adapter and IL Dataset Writer

**Files:**
- Create: `src/fruitfly/adapters/flybody_obs.py`
- Create: `src/fruitfly/training/il_dataset.py`
- Create: `scripts/build_il_dataset.py`
- Create: `tests/adapters/test_flybody_obs.py`
- Create: `tests/training/test_il_dataset.py`

**Step 1: Write the failing test**

```python
def test_observation_adapter_flattens_sections() -> None:
    from fruitfly.adapters.flybody_obs import adapt_observation

    obs = {"proprio": [1.0, 2.0], "command": [3.0]}
    adapted = adapt_observation(obs)
    assert adapted.shape[0] == 3
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/adapters/test_flybody_obs.py tests/training/test_il_dataset.py -q`
Expected: FAIL because adapter and dataset code do not exist yet.

**Step 3: Write minimal implementation**

Implement:
- stable field ordering for observation groups
- serialization format for expert rollouts
- dataset reader that returns observation, command, expert mean, and expert log-std

```python
def adapt_observation(obs: dict[str, list[float]]) -> torch.Tensor:
    ordered = [*obs["proprio"], *obs["command"]]
    return torch.tensor(ordered, dtype=torch.float32)
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/adapters/test_flybody_obs.py tests/training/test_il_dataset.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/fruitfly/adapters/flybody_obs.py src/fruitfly/training/il_dataset.py scripts/build_il_dataset.py tests/adapters/test_flybody_obs.py tests/training/test_il_dataset.py
git commit -m "feat: add flybody observation adapter and IL dataset writer"
```

### Task 5: Implement the Whole-Brain Rate Model

**Files:**
- Create: `src/fruitfly/models/rate_model.py`
- Create: `tests/models/test_rate_model.py`

**Step 1: Write the failing test**

```python
def test_rate_model_outputs_action_distribution_shapes() -> None:
    import torch
    from fruitfly.models.rate_model import WholeBrainRateModel

    model = WholeBrainRateModel(num_nodes=4, hidden_dim=8, action_dim=59)
    obs = torch.randn(2, 16)
    state = model.initial_state(batch_size=2)
    mean, log_std, next_state = model(obs, state)

    assert mean.shape == (2, 59)
    assert log_std.shape == (2, 59)
    assert next_state.shape == state.shape
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/models/test_rate_model.py -q`
Expected: FAIL because the model does not exist yet.

**Step 3: Write minimal implementation**

Implement:
- input projector
- sparse message passing
- gated recurrent update
- efferent readout and small decoder

```python
class WholeBrainRateModel(nn.Module):
    def forward(self, obs, state):
        afferent_input = self.input_projector(obs)
        messages = self.propagate(state, afferent_input)
        next_state = self.update(state, messages)
        mean, log_std = self.decode(next_state)
        return mean, log_std, next_state
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/models/test_rate_model.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/fruitfly/models/rate_model.py tests/models/test_rate_model.py
git commit -m "feat: add whole-brain rate model"
```

### Task 6: Implement IL Losses and Offline Trainer

**Files:**
- Create: `src/fruitfly/training/losses.py`
- Create: `src/fruitfly/training/trainer.py`
- Create: `scripts/train_il.py`
- Create: `tests/training/test_losses.py`
- Create: `tests/training/test_trainer.py`

**Step 1: Write the failing test**

```python
def test_kl_loss_is_zero_for_identical_distributions() -> None:
    import torch
    from fruitfly.training.losses import gaussian_kl

    mean = torch.zeros(2, 3)
    log_std = torch.zeros(2, 3)
    assert torch.isclose(gaussian_kl(mean, log_std, mean, log_std), torch.tensor(0.0))
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/training/test_losses.py tests/training/test_trainer.py -q`
Expected: FAIL because loss and trainer modules do not exist yet.

**Step 3: Write minimal implementation**

Implement:
- Gaussian KL
- auxiliary MSE terms
- annealed weighting schedule
- offline training loop with checkpoint saving

```python
loss = kl + lambda_t * (mean_mse + alpha * log_std_mse)
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/training/test_losses.py tests/training/test_trainer.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/fruitfly/training/losses.py src/fruitfly/training/trainer.py scripts/train_il.py tests/training/test_losses.py tests/training/test_trainer.py
git commit -m "feat: add IL trainer and losses"
```

### Task 7: Implement Closed-Loop Walking Evaluation

**Files:**
- Create: `src/fruitfly/evaluation/walking_eval.py`
- Create: `scripts/eval_walking.py`
- Create: `tests/evaluation/test_walking_eval.py`

**Step 1: Write the failing test**

```python
def test_eval_marks_direction_change_for_turning_rollout() -> None:
    from fruitfly.evaluation.walking_eval import summarize_turning

    summary = summarize_turning(headings=[0.0, 0.1, 0.3, 0.6])
    assert summary["direction_changed"] is True
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/evaluation/test_walking_eval.py -q`
Expected: FAIL because evaluation helpers do not exist yet.

**Step 3: Write minimal implementation**

Implement:
- rollout summary for gait initiation
- walking duration without collapse
- turning direction change
- NaN / action explosion checks

```python
def summarize_turning(headings):
    return {"direction_changed": headings[-1] - headings[0] > 0.2}
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/evaluation/test_walking_eval.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add src/fruitfly/evaluation/walking_eval.py scripts/eval_walking.py tests/evaluation/test_walking_eval.py
git commit -m "feat: add closed-loop walking evaluation"
```

### Task 8: Add End-to-End Smoke Config and Execution Runbook

**Files:**
- Create: `configs/model/full_graph_il.yaml`
- Create: `configs/train/walking_il.yaml`
- Create: `configs/eval/walking_closed_loop.yaml`
- Modify: `README.md`
- Create: `tests/integration/test_smoke_configs.py`

**Step 1: Write the failing test**

```python
def test_smoke_configs_exist() -> None:
    from pathlib import Path

    assert Path("configs/model/full_graph_il.yaml").exists()
    assert Path("configs/train/walking_il.yaml").exists()
    assert Path("configs/eval/walking_closed_loop.yaml").exists()
```

**Step 2: Run test to verify it fails**

Run: `python -m pytest tests/integration/test_smoke_configs.py -q`
Expected: FAIL because the config files are missing.

**Step 3: Write minimal implementation**

Add:
- one model config
- one IL train config
- one evaluation config
- README runbook with the canonical command order

```bash
python scripts/compile_graph.py --config configs/compile/full_graph.yaml
python scripts/build_il_dataset.py --config configs/train/walking_il.yaml
python scripts/train_il.py --config configs/train/walking_il.yaml
python scripts/eval_walking.py --config configs/eval/walking_closed_loop.yaml
```

**Step 4: Run test to verify it passes**

Run: `python -m pytest tests/integration/test_smoke_configs.py -q`
Expected: PASS.

**Step 5: Commit**

```bash
git add configs/model/full_graph_il.yaml configs/train/walking_il.yaml configs/eval/walking_closed_loop.yaml README.md tests/integration/test_smoke_configs.py
git commit -m "docs: add smoke configs and execution runbook"
```
