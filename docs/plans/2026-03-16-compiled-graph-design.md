# Compiled Graph Standardization Design

> Status: approved on 2026-03-16
> Scope: turn the completed full-brain `FlyWire（果蝇连接组平台）` snapshot into a long-lived standard `compiled graph（训练编译图）` artifact set for training, evaluation, and analysis

## Goal

Add a standard `compiled graph` output directory that is generated from the normalized full-brain snapshot and can be consumed directly by `IL-only（仅模仿学习）` training, later evaluation, and future analysis tooling without changing the artifact contract.

## Why This Exists

The repository now has:

- a completed full-brain normalized snapshot under `outputs/snapshots/flywire_public_full_v783/`
- a working `flybody（果蝇身体与 MuJoCo 物理环境）` expert-data export path
- a working `IL-only walking（仅模仿学习的步行阶段）` smoke-training skeleton

What it still does not have is a stable, reusable graph artifact package between snapshot export and model training. `compile_graph.py` currently emits a JSON summary, but not the actual files that training and analysis should load.

## Approved Decisions

- The first compiled output is a long-lived standard directory, not a temporary training-only blob.
- The first version optimizes for a stable contract, not maximal graph feature richness.
- `train_il.py` moves toward `--compiled-graph-dir` as the primary interface.
- Legacy debug flags remain temporarily for compatibility, but are no longer the main path.
- Acceptance is defined as “the real full-brain graph loads into training successfully,” not “walking quality matches the paper.”

## Output Directory Contract

Each compiled graph lives in its own directory:

```text
outputs/compiled/<compiled_id>/
  manifest.json
  config.json
  node_index.parquet
  edge_index.pt
  io_masks.pt
  graph_stats.json
```

### File Responsibilities

- `manifest.json`
  - records source snapshot ID
  - records compile timestamp
  - records compiler version or code path
  - records source file references

- `config.json`
  - records compile decisions such as:
    - active-node filtering
    - edge deduplication policy
    - ordering strategy

- `node_index.parquet`
  - stores the stable `source_id -> node_idx` mapping
  - serves as the bridge between biological identifiers and model indices

- `edge_index.pt`
  - stores the compiled directed edge list in training-ready tensor form
  - first version only requires source and target indices

- `io_masks.pt`
  - stores `afferent / intrinsic / efferent（输入 / 中间 / 输出）` boolean masks
  - acts as the canonical routing interface for model input and readout

- `graph_stats.json`
  - stores node count, edge count, mask counts, and deduplication summary

The first version intentionally avoids hiding everything in a single black-box `graph.pt`, because future training, evaluation, and analysis will need direct access to individual components.

## First-Version Compile Transformations

The first version performs only the minimum set of transformations required for a stable standard contract:

1. `active filtering（活跃过滤）`
   - keep only `is_active=true` nodes and edges

2. `stable reindexing（稳定重编号）`
   - assign contiguous `node_idx` values to active nodes
   - keep this mapping stable and reproducible

3. `flow-role masks（输入 / 中间 / 输出掩码）`
   - generate masks from `partitions.parquet`

4. `edge compilation（边编译）`
   - compile edges into model-ready directed `edge_index`

## Deferred Features

The following are explicitly out of scope for the first compiled-graph version:

- edge-weight normalization
- explicit excitatory/inhibitory edge sign support
- multiple sparse storage formats at once
- graph partition caches
- visualization-specific derived views
- behavior-specific or task-specific graph variants

This keeps the work focused on getting the real full-brain graph into the training path without mixing compile concerns with modeling experiments.

## Training Integration Contract

The repository should move from ad-hoc graph arguments to a directory-based interface:

```text
python scripts/train_il.py \
  --dataset <dataset.jsonl> \
  --compiled-graph-dir <compiled_dir> \
  --output-dir <train_output>
```

### Primary Training Inputs from the Compiled Graph

The first version of training only needs:

- `num_nodes`
- `edge_index`
- `afferent_indices`
- `efferent_indices`

This means the model internals can remain largely unchanged in the first integration step. The main change is the input contract, not a rewrite of the model architecture.

## Acceptance Criteria

This milestone is complete when:

- the full-brain normalized snapshot can be compiled into a standard artifact directory
- the compiled directory contains:
  - `manifest.json`
  - `config.json`
  - `node_index.parquet`
  - `edge_index.pt`
  - `io_masks.pt`
  - `graph_stats.json`
- `train_il.py` can load the compiled graph through `--compiled-graph-dir`
- a real `IL smoke test（模仿学习烟测）` succeeds using:
  - the compiled full-brain graph
  - the real `straight_smoke.jsonl` dataset
- the smoke test ends with:
  - finite loss
  - checkpoint written successfully
  - no `NaN`
  - no out-of-memory failure

## Non-Goals

- no immediate `PPO fine-tune（强化学习微调）`
- no walking-quality regression target yet
- no requirement to match paper metrics yet
- no flight support
- no brain-model redesign during the compiled-graph milestone
