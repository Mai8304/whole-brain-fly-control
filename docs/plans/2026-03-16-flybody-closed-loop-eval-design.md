# Flybody Closed-Loop Evaluation Design

> Status: approved on 2026-03-16
> Scope: first real closed-loop evaluation for the trained full-brain `straight walking（稳定直行）` controller

## Goal

Add a first real `flybody（果蝇身体与 MuJoCo 物理环境）` closed-loop evaluation path that loads a trained checkpoint, runs short `straight walking` rollouts, and reports whether the learned full-brain controller can be reattached to the body environment without immediate instability.

## Why This Exists

The repository now has:

- a completed full-brain `compiled graph（训练编译图）`
- a real exported `straight_v1.jsonl` dataset
- a successful full-brain `IL-only（仅模仿学习）` training run against that dataset

What is still missing is the most important next validation step: whether a trained checkpoint can run in closed loop inside `flybody` without exploding, producing `NaN`, or terminating immediately.

## Approved Decisions

- The first closed-loop evaluation is engineering-focused, not paper-metric-focused.
- The first task scope is only `straight walking`, not `turning（转向）`, `gait initiation（起步）`, or `flight（飞行）`.
- The runtime stack is:
  - `checkpoint（模型检查点）`
  - `-> model loader（模型加载器）`
  - `-> policy wrapper（策略包装器）`
  - `-> flybody rollout（闭环展开）`
- The evaluation runs in the dedicated `.venv-flybody` environment.
- Output is both:
  - CLI JSON
  - `outputs/eval/<run>/summary.json`

## Evaluation Contract

The first closed-loop evaluation must emit a small engineering summary rather than a full benchmark report.

Required fields:

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

These are sufficient to answer the first-order question: can the trained controller stay attached to the body environment and run a short rollout without obvious failure.

## Runtime Architecture

The evaluation path should not embed environment logic directly into the model class.

Recommended split:

1. `checkpoint loader`
   - reconstruct the `WholeBrainRateModel（全脑速率模型）`
   - load the saved weights
   - load the compiled graph metadata needed for inference

2. `policy wrapper`
   - maintain model hidden state across rollout steps
   - adapt `flybody` observations into model input
   - produce deterministic action output for evaluation

3. `rollout runner`
   - create the `walk_imitation` environment
   - call `reset`
   - step the environment with wrapper-produced actions
   - collect the summary fields

This keeps model, environment, and evaluation logic separated cleanly.

## Failure Handling

The first version should prioritize diagnosability, not graceful degradation.

If any of the following happens, the summary should record failure explicitly:

- checkpoint load error
- compiled graph mismatch
- observation-shape mismatch
- `NaN` action output
- early environment termination
- rollout exception

The first version does not need recovery or retry logic inside evaluation.

## Acceptance Criteria

The milestone is complete when:

- a dedicated closed-loop evaluation script can run from `.venv-flybody`
- the script can load:
  - a real checkpoint
  - the compiled full-brain graph
- it can run a short `straight walking` rollout in `flybody`
- it writes a `summary.json`
- the summary reports the engineering metrics listed above

## Non-Goals

- no paper-style quantitative benchmark yet
- no multi-episode aggregate report yet
- no turning or flight support
- no video generation requirement
- no visualization dashboard in this milestone
