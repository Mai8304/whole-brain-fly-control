# Training Console Design

**Goal:** Design a `Training Console（训练控制台）` for the fruit fly whole-brain research platform that makes the full training lifecycle observable, traceable, and scientifically honest.

**Scope:** This design covers the training-side console only. It is separate from the existing `Experiment Console（实验控制台）`, but it shares artifacts and lineage with it. The design assumes the current repository state: `IL-only（仅模仿学习）` training is real, `straight_walking（稳定直行）` is the only fully wired task today, and future tasks will expand over time.

**Design principle:** Complete capture, layered presentation, strict semantics.

**Design-system source:** Use the console-family design system generated through the repaired local `ui-ux-pro-max（界面设计技能）` workflow and persisted at:

- [MASTER.md](/Users/zhuangwei/Downloads/coding/Fruitfly/design-system/MASTER.md)
- [console-family.md](/Users/zhuangwei/Downloads/coding/Fruitfly/design-system/pages/console-family.md)

---

## 1. Product Positioning

`Training Console` is not a demo page and not a lightweight “start training” popup.

It is a `research training workbench（科研训练工作台）` for:

- launching training runs
- tracking runtime state
- inspecting full configuration and metrics
- running post-training closed-loop evaluation
- registering and tracing artifacts

It must answer four questions at all times:

1. What data and graph went into this run?
2. What configuration was used?
3. What is the system doing right now?
4. What artifacts came out, and are they formally usable?

The console must not overstate what is complete. It must clearly separate:

- training completed
- evaluation completed
- behavior quality acceptable
- formally validated

---

## 2. User Model

The console serves three primary users.

### 2.1 Research operator

Needs to:

- choose dataset and graph inputs
- start a run
- monitor whether training is progressing
- launch evaluation
- inspect final outputs

### 2.2 Model developer

Needs to:

- inspect hyperparameters
- inspect runtime metrics and raw logs
- identify failure stage and failure reason
- compare run provenance

### 2.3 Platform maintainer

Needs to:

- ensure data-source consistency
- enforce research strictness
- confirm which artifacts are formal versus experimental
- trace lineage from dataset to graph to checkpoint to evaluation

---

## 3. Scope of “Complete Training”

The design must support the full training lifecycle, not just the current `straight_walking` slice.

However, it must not pretend that future tasks are already implemented.

### 3.1 Current real task scope

Today, the repository has a real end-to-end training path for:

- `straight_walking（稳定直行）`

Today’s real pipeline is:

`flybody teacher（老师策略）`
`-> IL dataset（模仿学习数据集）`
`-> compiled graph（训练编译图）`
`-> train_il.py`
`-> checkpoint（检查点）`
`-> flybody closed-loop evaluation（闭环评估）`

### 3.2 Future task scope

The console must be designed to absorb future task families without redoing the page model.

Examples:

- `gait initiation（起步）`
- `turning（转向）`
- `speed tracking（速度跟踪）`
- `stop / restart（停走与重启）`
- `perturbation recovery（扰动恢复）`
- `terrain adaptation（地形适应）`
- future conditioned locomotion tasks
- future embodied tasks such as `flight（飞行）`
- future `PPO fine-tune（强化学习微调）`

Because of this, the console must be organized by `training lifecycle（训练生命周期）`, not by a hard-coded list of current tasks.

---

## 4. Top-Level Structure

The top-level structure is fixed to five stages:

- `Data`
- `Graph`
- `Train`
- `Eval`
- `Registry`

This mirrors the real engineering flow:

`teacher / expert source`
`-> dataset`
`-> compiled graph`
`-> training`
`-> checkpoint`
`-> closed-loop eval`
`-> artifact registration`

### 4.1 ASCII layout

```text
+==================================================================================================================+
| TRAINING CONSOLE                                                                                                 |
+==================================================================================================================+
| Workspace: flywire_public_full_v783      Run: full_graph_straight_v1      Status: IDLE / RUNNING / FAILED       |
|                                                                                                                  |
| [ Data ] [ Graph ] [ Train ] [ Eval ] [ Registry ]                         Strict Mode: ON                       |
+==================================================================================================================+
| LEFT: RUN NAVIGATOR                     | CENTER: ACTIVE WORKSPACE                | RIGHT: INSPECTOR              |
|                                         |                                         |                                |
| Current Pipeline                        | Stage panels                            | Selected artifact              |
| Run Context                             | Data / Graph / Train / Eval / Registry  | Job status                     |
| Quick Actions                           |                                         | Research guardrails            |
+==================================================================================================================+
| LOG                                                                                                              |
+==================================================================================================================+
```

### 4.2 Layout meaning

- Left column: where the run is in the lifecycle and what artifacts are already selected
- Center column: the active work area for each training stage
- Right column: expanded inspection, job state, and research guardrails
- Bottom log: append-only operational log

The visual tone should be more restrained than the experiment UI. This is a workbench, not a showpiece.

### 4.3 Shared design system requirements

`Training Console` must not become a stylistic fork of `Experiment Console`.

Both consoles must:

- use `shadcn/ui（组件体系）` for all shared 2D controls and surfaces
- share one design language, one spacing system, one tooltip pattern, and one status-color system
- preserve semantic consistency between training-side and experiment-side labels

The design direction should still distinguish the two surfaces in tone:

- `Experiment Console` is more observational and experiment-facing
- `Training Console` is more operational and artifact-facing

But they must still clearly belong to the same product family.

The approved family-wide visual baseline is:

- Visual direction: `scientific operations console（科研运维控制台）`
- Palette: blue-slate operational neutrals with amber warning accents and green/red validation states
- Typography:
  - `Fira Code` for section headings and dense metrics
  - `Fira Sans` for body text and labels
  - `Fira Code` for logs, paths, and dense numerical views

This should make the training page feel operational and inspectable, while staying recognizably part of the same product family as the experiment page.

---

## 5. Training Console vs Experiment Console

The repository should keep both consoles, but their semantics must remain separate.

### 5.1 Training Console

Responsible for:

- dataset generation / validation
- graph compilation
- training launch and monitoring
- evaluation launch and inspection
- artifact registration

### 5.2 Experiment Console

Responsible for:

- selecting a trained checkpoint
- applying experimental conditions
- running body-side experiments
- showing `neuropil（神经纤维区）` activity and body behavior

### 5.3 Shared lineage

They must share:

- checkpoint registry
- evaluation artifacts
- validation state
- run lineage

Training Console produces artifacts. Experiment Console consumes artifacts.

---

## 6. Information Architecture

The console must be information-complete, but not visually flat.

The recommended model is a three-layer disclosure design.

### 6.1 Layer 1: Primary view

This layer is always visible.

It shows:

- the current dataset
- the current compiled graph
- the current train/eval status
- the latest key metrics
- the current artifact references

Its job is quick observation.

### 6.2 Layer 2: Expanded inspector

This layer shows full configuration and full runtime status.

It includes:

- full dataset metadata
- graph metadata
- hyperparameters
- runtime timestamps
- raw metric groups
- artifact paths
- research labels

Its job is detailed inspection.

### 6.3 Layer 3: Raw snapshots and logs

This layer exposes raw evidence.

It includes:

- full config JSON
- full runtime status JSON
- stdout / stderr
- evaluation summary JSON
- validation JSON
- command-line invocation

Its job is auditability.

The system requirement is:

**Nothing important may be hidden from the user, but not everything should be forced into the main view.**

---

## 7. Panel Definitions

### 7.1 Data

Required V1 fields:

- `Dataset path`
- `Dataset name`
- `Task family`
- `Task variant`
- `Sample count`
- `Episode count` when available
- `Field contract status`
- `Source policy`

Primary actions:

- `Build Dataset`
- `Validate Dataset`
- `Preview Sample`

V1 non-goals:

- sample editing
- dataset augmentation UI
- multi-dataset mixing policy UI

### 7.2 Graph

Required V1 fields:

- `Snapshot dir`
- `Compiled graph dir`
- `Node count`
- `Edge count` when available
- `Afferent count`
- `Efferent count`
- `Compile status`

Primary actions:

- `Compile Graph`
- `Inspect Graph Stats`

V1 non-goals:

- graph editing
- subgraph crafting
- interactive edge surgery

### 7.3 Train

Required V1 fields:

- `Task family`
- `Task variant`
- `Dataset`
- `Compiled graph`
- `Output run name`
- `Epochs`
- `Batch size`
- `Learning rate`
- `Hidden dim`
- `Action dim`
- `Seed`
- `Train status`
- `Current epoch`
- `Last loss`
- `Latest checkpoint`

Primary actions:

- `Start Training`
- `Stop`
- `Resume`

V1 non-goals:

- distributed training topology
- auto-tuning
- online optimizer switching

### 7.4 Eval

Required V1 fields:

- `Checkpoint`
- `Task variant`
- `Max steps`
- `Save video`
- `Eval status`
- `Steps completed`
- `Has NaN action`
- `Terminated early`
- `Reward mean`
- `Forward velocity mean`
- `Body upright mean`
- `Summary path`
- `Video path`

Primary actions:

- `Run Eval`
- `Open Summary`
- `Open Video`

V1 non-goals:

- bulk checkpoint comparison
- benchmark leaderboard
- multi-task evaluation matrix

### 7.5 Registry

Required V1 fields:

- `Run name`
- `Dataset ref`
- `Graph ref`
- `Checkpoint ref`
- `Eval ref`
- `Registration status`
- `Research label`

Suggested labels:

- `experimental`
- `validated`
- `formal_pending`

Primary actions:

- `Register Run`
- `Mark Experimental`
- `Mark Validated`

V1 non-goals:

- multi-user approvals
- release governance workflows
- external model registry sync

---

## 8. State Model

The console should use stage-specific state machines, not a single global job label.

### 8.1 Data state machine

```text
missing -> building -> ready -> validated -> failed
```

### 8.2 Graph state machine

```text
missing -> compiling -> ready -> inspected -> failed
```

### 8.3 Train state machine

```text
idle -> queued -> running -> completed -> failed -> stopped
```

### 8.4 Eval state machine

```text
idle -> queued -> running -> completed -> failed
```

### 8.5 Registry state machine

```text
unregistered -> registered -> validated -> formal_ready -> failed
```

### 8.6 Status semantics

Execution state and quality state must remain separate.

Examples:

- `Training completed` means the script ended and wrote checkpoint artifacts
- `Closed-loop evaluation completed` means the rollout finished and wrote summary artifacts
- `Behavior quality acceptable` is a downstream judgment based on metrics
- `Formal ready` means the run is eligible to enter the formal artifact layer

The UI must never collapse these distinct meanings into one generic “success” label.

---

## 9. Copy Rules

Training Console copy should follow a research-console style.

### 9.1 Label rules

Labels must be:

- short
- stable
- engineering-like

Examples:

- `Dataset`
- `Task family`
- `Train status`
- `Validation status`

### 9.2 Status rules

Statuses must be:

- enumerable
- condition-bound
- non-emotional

Avoid:

- `looks good`
- `almost done`
- `great run`

### 9.3 Action rules

Actions must use explicit verbs.

Examples:

- `Build Dataset`
- `Compile Graph`
- `Start Training`
- `Run Eval`
- `Register Run`

### 9.4 Explanation rules

Explanatory copy must:

- define what the field means
- define what produced it
- define what completion does and does not imply

Example:

`Closed-loop evaluation completed`
`Summary artifact written. This does not imply acceptable behavior quality.`

---

## 10. Tooltip Rules

Core parameters, states, and metrics must expose `(?)` hover help.

Every tooltip should follow one compact structure:

- `Definition`
- `Source`
- `Update`
- `Null semantics`

When relevant, a `Unit` line may also be included.

Examples:

### `Last loss (?)`

- `Definition:` most recent total training loss reported by the trainer
- `Source:` training runtime
- `Update:` during training
- `Null semantics:` unavailable before the first completed step

### `Validation status (?)`

- `Definition:` whether this artifact passed configured research validation checks
- `Source:` validation artifact
- `Update:` after validation run completion
- `Null semantics:` validation not yet run

### `Reward mean (?)`

- `Definition:` mean rollout reward reported over completed evaluation steps
- `Source:` closed-loop evaluation summary
- `Update:` after evaluation run
- `Null semantics:` unavailable before evaluation completes

Tooltips are mandatory for meaning-rich fields. They are not needed for obvious file paths or simple buttons.

---

## 11. Theme and Localization

Both consoles must support a shared global theme and localization system.

### 11.1 Theme modes

Required theme modes:

- `light（亮色）`
- `dark（暗色）`
- `system（跟随系统）`

Theme mode must be shared across both consoles through one common application-level setting.

### 11.2 Languages

Required languages:

- `English（英文）`
- `简体中文`
- `繁體中文`
- `日本語（日文）`

Behavior:

- prefer the system language when available and supported
- fall back to `English` by default
- keep all critical labels, statuses, and tooltip definitions semantically equivalent across languages

### 11.3 Translation scope

The following content must be localizable:

- navigation labels
- stage names
- field labels
- status labels
- button labels
- tooltip definitions
- unavailable-state messages

Raw artifact content such as JSON payloads and file paths should remain raw and untranslated.

---

## 12. Research Strictness Rules

The training-side console must remain compatible with the repository’s scientific strictness policy.

This means:

- no mock values may masquerade as real run state
- no placeholder evaluation metrics may appear as completed metrics
- unavailable truth or validation states must remain unavailable
- `Registry` must not elevate a run to formal status without required evidence

The console should make source mismatch or validation absence visible, not silent.

---

## 13. Recommended V1 Visual Direction

Use the same frontend base stack already approved for the project:

- `React（前端框架）`
- `shadcn/ui（组件体系）`

The visual tone should be:

- restrained
- dense but legible
- documentation-like rather than marketing-like
- strongly state-driven

Compared with `Experiment Console`, this UI should feel:

- less cinematic
- more inspectable
- more operational

---

## 14. Summary

The approved V1 `Training Console` is:

- a lifecycle-based research workbench
- organized as `Data -> Graph -> Train -> Eval -> Registry`
- complete in information capture
- layered in information presentation
- strict about status semantics
- strict about artifact provenance
- separated from `Experiment Console`, but connected through shared lineage

Its purpose is not only to start runs, but to make training and evaluation traceable enough for a real research platform.
