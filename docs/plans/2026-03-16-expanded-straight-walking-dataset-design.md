# Expanded Straight-Walking Dataset Design

> Status: approved on 2026-03-16
> Scope: expand the real `straight walking（稳定直行）` expert dataset beyond smoke scale while preserving the current training contract

## Goal

Export a larger real `flybody（果蝇身体与 MuJoCo 物理环境）` straight-walking dataset that is still small enough for rapid iteration, but large enough to support a more meaningful `IL-only（仅模仿学习）` training run on the real full-brain graph.

## Why This Exists

The repository has already achieved:

- a working real `flybody` expert export path
- a working real `compiled graph（训练编译图）` for the full-brain snapshot
- a successful first full-brain `IL smoke test（模仿学习烟测）`

What is missing is a dataset that is bigger than the current smoke file and therefore more useful for training behavior that can later be evaluated in closed loop.

## Approved Decisions

- The next dataset remains limited to `straight walking`, not `gait initiation（起步）` or `turning（转向）`.
- The export target is:
  - `episodes=3`
  - `max_steps=128`
- The core training contract remains unchanged:
  - `observation`
  - `command`
  - `expert_mean`
  - `expert_log_std`
- Only minimal metadata is added:
  - `episode_id`
  - `step_id`
  - `task`

## Data Contract

Each exported row keeps the existing training fields:

- `observation`
- `command`
- `expert_mean`
- `expert_log_std`

And adds lightweight metadata fields:

- `episode_id`
  - integer episode identifier
- `step_id`
  - integer timestep within the episode
- `task`
  - fixed string, first version value: `straight_walking`

This keeps existing training consumers compatible while giving future evaluation and debugging enough context to group rows by trajectory.

## Export Scope

The first expanded dataset is intentionally modest:

- `episodes=3`
- `max_steps=128`

This is large enough to move beyond smoke scale and small enough to keep export/debug time low on the current workstation.

## Acceptance Criteria

The expanded-dataset milestone is complete when:

- a new real straight-walking dataset is exported with:
  - `episodes=3`
  - `max_steps=128`
- the dataset contains more samples than the current smoke dataset
- each sample contains:
  - `observation`
  - `command`
  - `expert_mean`
  - `expert_log_std`
  - `episode_id`
  - `step_id`
  - `task`
- the full-brain compiled graph can be used to run a non-smoke `IL-only` training pass on this dataset
- the training pass ends with:
  - finite loss
  - checkpoint written
  - no `NaN`
  - no OOM

## Non-Goals

- no direct closed-loop walking evaluation in this milestone
- no `PPO fine-tune（强化学习微调）`
- no flight support
- no contract break for existing training consumers
