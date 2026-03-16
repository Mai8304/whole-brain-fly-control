# Flybody Straight-Walking IL Dataset Design

> Status: approved on 2026-03-12
> Scope: first real `flybody（果蝇身体与 MuJoCo 物理环境）` expert-data slice only

## Goal

Build the first real behavior slice:

`flybody expert（专家策略）`
`-> straight walking（稳定直行） expert rollout（专家轨迹）`
`-> IL dataset（模仿学习数据集）`
`-> train_il.py` minimal smoke test

## Non-Goals

- No `gait initiation（起步）`
- No `turning（转向）`
- No `PPO fine-tune（强化学习微调）`
- No direct training inside the `flybody` environment
- No attempt to match paper metrics in this phase

## Approved Defaults

- Task: `straight walking（稳定直行）`
- Dataset size: `small real dataset（小规模真实数据集）`, not benchmark scale
- Dataset contract stays unchanged:
  - `observation`
  - `command`
  - `expert_mean`
  - `expert_log_std`
- Environment split:
  - `flybody` runs in its own environment
  - core training remains in the main project environment

## Architecture

### 1. Environment Boundary

The `flybody` stack is isolated in a dedicated environment because its physics and simulator dependencies are heavier and more fragile than the core training stack.

The first implementation should use file exchange, not cross-environment runtime calls:

`flybody env`
`-> dataset.jsonl`
`-> main training env`

This keeps failure domains separate:

- `flybody / MuJoCo（物理引擎）` install issues
- expert rollout logic issues
- training and model issues

### 2. Data Flow

The first real dataset pipeline should look like this:

1. launch a `flybody` straight-walking task
2. run the `expert controller（专家控制器）`
3. collect per-step observation and command
4. collect the expert action distribution parameters
5. serialize records into the existing `ILDataset（模仿学习数据集）` contract
6. load the dataset in the main training environment
7. run one minimal `IL smoke test（模仿学习烟测）`

### 3. Dataset Contract

The contract should remain intentionally narrow for the first slice:

- `observation`: flattened model input
- `command`: walking command input
- `expert_mean`: expert action mean
- `expert_log_std`: expert action log standard deviation

Optional metadata such as episode id, task tag, and timestep may be added later, but should not block the first end-to-end slice.

### 4. Dataset Builder

`build_il_dataset.py` should stop being a stub and become a real exporter for `straight walking`.

Responsibilities:

- create or open the `flybody` task
- run a small number of expert episodes
- flatten observations through the project adapter
- write a non-empty `jsonl` dataset
- report a small summary:
  - episode count
  - sample count
  - output path

The builder should prefer explicit caps such as:

- `--episodes`
- `--max-steps`
- `--output`

The first version should optimize for debuggability, not throughput.

### 5. Minimal Training Smoke

The first smoke test should use the real dataset but remain intentionally tiny.

Success means:

- `build_il_dataset.py` writes a non-empty dataset
- `ILDataset` reads it back without schema errors
- `train_il.py` completes one small training run
- the training loss is finite
- a checkpoint is written

This phase does not require visually convincing walking behavior.

## Acceptance Criteria

This slice is complete when:

- a dedicated `flybody` environment can export a real straight-walking expert dataset
- the dataset is compatible with the current `ILDataset` reader
- the main environment can run `train_il.py` against that dataset
- the run produces finite loss and a checkpoint artifact

## Next Step After This Slice

Once the straight-walking slice is stable, the next expansion options are:

- add `gait initiation（起步）`
- add `turning（转向）`
- enlarge expert dataset size
- improve dataset metadata
- later add `PPO fine-tune（强化学习微调）`
