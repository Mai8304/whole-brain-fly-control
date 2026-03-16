# Fruitfly Phase 1 Design

> Status: approved on 2026-03-12
> Scope: first executable phase only

## Goal

Build a reproducible `IL-only（仅模仿学习）` walking stack that uses the full `139,246`-neuron FlyWire connectome to control `flybody（果蝇身体与 MuJoCo 物理环境）`.

## Non-Goals

- No `PPO fine-tune（强化学习微调）`
- No `flight（飞行）`
- No `Brian2（脉冲神经仿真框架）` whole-brain runtime
- No online `neuPrint（连接组查询服务）` queries during training or evaluation
- No small-graph proxy as the primary path

## Approved Defaults

- Embodiment: `flybody`
- Data source strategy: `FlyWire / neuPrint snapshot（本地冻结的连接组快照）`
- Graph size: full `139,246` neurons from day one
- Phase 1 training: `imitation learning（模仿学习）` only
- Phase 1 tasks: `gait initiation（起步）`, `straight walking（稳定直行）`, `turning（转向）`

## Architecture

### 1. Snapshot Layers

The project stores connectome data in three layers:

- `raw`: closest export from `FlyWire / neuPrint`
- `normalized`: project-level source of truth for nodes, edges, and `flow_role（输入 / 中间 / 输出标签）`
- `compiled`: tensors and sparse graph structures used directly by training and inference

Suggested layout:

```text
data/connectome/snapshots/<snapshot_id>/
  manifest.yaml
  raw/
  normalized/
  compiled/
```

### 2. Normalized Schema

`normalized` is the stable fact layer and must not depend on a specific trainer implementation.

Required files:

- `nodes.parquet`
- `edges.parquet`
- `partitions.parquet`
- `stats.json`

Required node facts:

- `source_id`
- `dataset_version`
- `hemisphere`
- `flow_role`
- `super_class`
- `cell_type`
- `region`
- `is_active`

Required edge facts:

- `pre_id`
- `post_id`
- `synapse_count`
- `edge_sign`
- `is_directed`
- `is_active`

### 3. Graph Compiler

`graph compiler（图编译层）` turns the normalized snapshot into a full-graph training object.

Responsibilities:

- assign contiguous node indices
- drop inactive nodes and edges
- build `afferent / intrinsic / efferent` masks
- materialize sparse directed adjacency
- freeze node ordering for training, evaluation, and visualization
- record compile-time config and checksums

Required compiled outputs:

- `graph.pt`
- `node_index.parquet`
- `io_masks.pt`
- `sparse_adj.pt` or `sparse_adj.npz`
- `config.json`

### 4. Whole-Brain Rate Model

Phase 1 uses a `whole-brain rate model（全脑速率模型）` instead of a spiking runtime.

Model components:

- `input projector（输入投影器）`: maps `flybody` observations to afferent neuron inputs
- `neuron state（神经元状态）`: continuous hidden state per neuron
- `message passing（消息传递）`: sparse directed propagation across the connectome
- `gated update（门控更新）`: stabilizes recurrent state transitions
- `intrinsic descriptor（神经元固有描述向量）`: trainable per-neuron parameters beyond graph topology
- `action decoder（动作解码器）`: reads efferent states and predicts the `flybody` action distribution

Phase 1 should prefer:

- sparse directed graph computation
- small hidden width such as 16 or 32 channels
- 2 to 4 propagation layers
- graph topology faithful to the paper's unweighted directed setup

### 5. Body Interface

The body layer is split into:

- `observation adapter（观测适配器）`: normalizes `flybody` observations into a stable project input contract
- `action decoder（动作解码器）`: translates efferent neuron states into 59-dimensional walking actions

The interface contract must stay stable so the brain model can evolve without rewriting the `flybody` integration.

### 6. IL-Only Training

Phase 1 trains only through `imitation learning（模仿学习）` against a `flybody expert MLP controller（flybody 中现成的专家 MLP 控制器）`.

Training data:

- expert rollouts from `gait initiation`, `straight walking`, and `turning`
- paired observation, command, and action-distribution targets
- filtered to keep only successful trajectories of sufficient length

Loss:

- primary: `KL divergence（KL 散度）` between predicted and expert action distributions
- auxiliary: `MSE（均方误差）` on means and log-stds

Evaluation:

- offline metrics: total loss, mean MSE, std/log-std MSE, KL
- closed-loop metrics: stable stepping, sustained walking, visible turning response, no NaN or action explosion

## Acceptance Criteria

Phase 1 is considered successful when:

- the full-graph snapshot compiles into a stable training graph
- the IL pipeline trains without numerical instability
- the trained policy can run closed-loop in `flybody`
- the policy can:
  - initiate gait from rest
  - sustain straight walking for at least 100 to 200 steps
  - respond to turning commands with directional trajectory change

## Phase 2

Phase 2 may add:

- `PPO fine-tune（强化学习微调）`
- richer edge features such as synapse counts and sign
- better neural interpretability tooling
- selected `spiking subcircuits（关键子回路脉冲化）`

