# Neuropil Activity Mapping Design

**Goal:** Define a strict `neuropil activity mapping（神经纤维区活动映射）` design for the Fruitfly research platform that follows the `FlyWire official route（FlyWire 官方路线）`, preserves a single authoritative data chain, and satisfies scientific reproducibility and interpretability requirements.

**Scope:** This design covers the formal `neuron-to-neuropil truth（神经元到神经纤维区真值映射）` contract, the `runtime aggregation（运行时活动聚合）` contract, and the `UI/API semantics（界面与接口语义）` contract for formal neuropil activity display.

**Relationship to existing plans:** This design extends and tightens the current FlyWire neuropil truth direction:
- `/Users/zhuangwei/Downloads/coding/Fruitfly/docs/plans/2026-03-16-flywire-official-neuropil-truth-design.md`

---

## 1. Problem Statement

The repository already has:
- an official `FlyWire 783` raw truth route
- a formal `synapse_neuropil_assignment.parquet（突触级神经纤维区归属表）`
- a formal `node_neuropil_occupancy.parquet（节点级神经纤维区占据表）`
- runtime code that can aggregate node activity into display-region activity

The repository still lacks a fully nailed-down design for:
- the exact scientific meaning of `neuron-to-neuropil mapping`
- the exact scientific meaning of `neuropil activity`
- the boundary between formal truth and display convenience
- the required provenance and failure semantics for the `brain-view（脑图载荷）` API

The core risk is semantic drift:
- treating a display grouping as if it were formal anatomical truth
- treating a graph-scoped validation pass as if it implied full official roster alignment
- treating a single dominant label as if a neuron belonged to exactly one neuropil

For a research platform, these shortcuts are not acceptable.

---

## 2. Approved Design Principles

The approved design is governed by the following principles:

- use a single authoritative data chain for formal neuropil activity
- keep official `neuropil` semantics separate from legacy generic `ROI（脑区）` semantics
- preserve multi-neuropil occupancy as the formal truth representation
- keep runtime aggregation read-only with respect to anatomical truth
- fail closed in `research strict mode（科研严格模式）`
- expose provenance and validation status explicitly in API payloads
- allow display grouping only as a declared transform, never as hidden truth rewriting

---

## 3. Single Authoritative Data Chain

The formal mainline for neuropil activity must be:

`FlyWire 783 official raw release`
`-> synapse_neuropil_assignment.parquet`
`-> node_neuropil_occupancy.parquet`
`-> neuropil_truth_validation.json`
`-> runtime node_activity aggregation`
`-> brain-view API payload`
`-> optional UI display grouping`

This chain is the only formal source of `neuropil activity`.

The following are explicitly excluded from the formal activity chain:
- `node_roi_map.parquet`
- annotation-derived dominant region heuristics
- preview payloads
- mock data
- online lookup at runtime
- UI-side inference of missing anatomy

These sources may exist for support or development, but they must not participate in formal scientific neuropil activity computation.

---

## 4. Formal Truth Contract

### 4.1 Canonical source contract

The only canonical raw truth sources are:
- `data/raw/flywire_783_neuropil_release/proofread_root_ids_783.npy`
- `data/raw/flywire_783_neuropil_release/flywire_synapses_783.feather`
- `data/raw/flywire_783_neuropil_release/per_neuron_neuropil_count_pre_783.feather`
- `data/raw/flywire_783_neuropil_release/per_neuron_neuropil_count_post_783.feather`

No other raw source may override these files in the formal mainline.

### 4.2 Formal semantic unit

The formal anatomical unit is `neuropil（神经纤维区）`, not generic `ROI`.

The truth layer must preserve official vocabulary and granularity, including laterality where present:
- `AL_L`
- `AL_R`
- `LH_L`
- `LH_R`
- `LAL_L`
- `LAL_R`

Collapsed display labels such as `AL` or `LH` are not formal truth identifiers.

### 4.3 Formal truth artifacts

The project must preserve the two-stage truth stack:

1. `synapse_neuropil_assignment.parquet`
   - first-order anatomical evidence
   - one row per synapse-root-direction-neuropil observation

2. `node_neuropil_occupancy.parquet`
   - runtime-facing derived truth
   - one row per `(source_id, neuropil)` occupancy record

`node_neuropil_occupancy` is a compiled anatomical distribution artifact.
It is not a dominant-label table.

### 4.4 Occupancy semantics

`occupancy_fraction（占据比例）` must retain one stable meaning:

`occupancy_fraction = synapse_count_in_this_neuropil / total_synapse_count_for_this_node`

This value means:
- anatomical evidence share within the current graph scope

It does not mean:
- exclusive membership
- functional causality
- probabilistic certainty

### 4.5 Validation semantics

Formal validation must remain split into two distinct statuses:

1. `graph-scoped validation（运行图范围校验）`
   - compares `node_neuropil_occupancy` against official per-neuron counts projected into the current `node_index.parquet` scope

2. `proofread roster alignment（官方校对名录对齐）`
   - compares current graph roots against `proofread_root_ids_783.npy`

These statuses must never be collapsed into a single generic “official pass/fail” field.

---

## 5. Runtime Aggregation Contract

### 5.1 Runtime responsibility

The runtime layer is a consumer of validated anatomical truth.

It is responsible for answering:

`Given a node activity vector at a step, how much activity mass and signed activity are carried by each neuropil under validated occupancy weights?`

It is not responsible for redefining anatomy.

### 5.2 Runtime inputs

The formal runtime aggregation path may consume only:
- `node_activity`
- `node_neuropil_occupancy.parquet`
- `node_index.parquet`
- validation metadata for the same compiled graph

If any of these are missing or inconsistent, formal neuropil activity must be unavailable.

### 5.3 Aggregation metrics

The design should expose two explicit aggregation metrics:

1. `activity_mass（活动质量）`
   - `sum(abs(node_activity_i) * occupancy_fraction_i,k)`

2. `signed_activity（带符号活动）`
   - `sum(node_activity_i * occupancy_fraction_i,k)`

Recommended policy:
- default heatmap emphasis uses `activity_mass` because it is visually stable
- formal payloads should also carry `signed_activity` because it preserves the model's directional dynamics

The system must not silently replace one metric with the other.

### 5.4 Normalization policy

The runtime layer must not apply hidden normalization.

At minimum, the payload should expose:
- `raw_activity_mass`
- `signed_activity`
- `covered_weight_sum`
- `node_count`

This keeps later analysis reproducible and prevents visually convenient but scientifically ambiguous normalization from becoming implicit truth.

### 5.5 Membership policy

For a node, formal anatomical membership remains multi-valued.

Therefore runtime payloads must not represent top active nodes with only one anatomical label.

Formal node activity payloads should expose:
- `node_idx`
- `source_id`
- `activity_value`
- `flow_role`
- `neuropil_memberships`

Where:
- `neuropil_memberships = [{ neuropil, occupancy_fraction, synapse_count }]`

If a UI needs one simplified label, it may additionally expose:
- `display_group_hint`

But that field must be explicitly marked as display-only.

---

## 6. UI/API Semantics Contract

### 6.1 Payload provenance

Every formal `brain-view` payload must carry explicit provenance fields:
- `semantic_scope = "neuropil"`
- `mapping_mode = "node_neuropil_occupancy"`
- `activity_metric`
- `validation_passed`
- `graph_scope_validation_passed`
- `roster_alignment_passed`
- `materialization`
- `dataset`

This is required so the payload can be audited without relying on implicit frontend assumptions.

### 6.2 Region payload schema

The formal `region_activity` payload should represent neuropil activity, not generic ROI glow.

Each entry should include:
- `neuropil_id`
- `display_name`
- `raw_activity_mass`
- `signed_activity`
- `covered_weight_sum`
- `node_count`
- `is_display_grouped`

Legacy names like `roi_id` may remain temporarily in compatibility layers, but the design target should move formal payloads toward neuropil-specific naming.

### 6.3 Top-node payload schema

The formal `top_nodes` payload should include:
- `node_idx`
- `source_id`
- `activity_value`
- `flow_role`
- `neuropil_memberships`
- `display_group_hint`

The API must not imply that `display_group_hint` is a formal unique anatomical assignment.

### 6.4 Display grouping

The approved V1 display scope remains the 8 grouped neuropils:
- `AL`
- `LH`
- `PB`
- `FB`
- `EB`
- `NO`
- `LAL`
- `GNG`

This grouping is allowed only as a declared display transform.

If grouping is applied, the payload must say so explicitly, for example:
- `view_mode = "grouped-neuropil-v1"`
- `is_display_grouped = true`

The underlying formal truth semantics remain at the official neuropil granularity.

### 6.5 Mesh role separation

Neuropil mesh assets provide geometry only.

They must not:
- define activity values
- repair missing occupancy data
- substitute for validation
- determine membership in the absence of formal truth artifacts

---

## 7. Failure and Strict-Mode Policy

Formal neuropil activity must fail closed.

The `brain-view` payload must return `null`, empty, or explicit unavailable state when any of the following is true:
- `node_neuropil_occupancy.parquet` is missing
- validation output is missing
- graph-scoped validation failed
- `node_activity` length does not match `node_index`
- the payload cannot prove provenance for the current compiled graph

The following are explicitly forbidden in formal research mode:
- mock fallback
- preview fallback
- dominant-evidence fallback
- heuristic reassignment
- silent degradation into a legacy ROI path

Whole-brain shell rendering may still be allowed when neuropil activity is unavailable, but formal neuropil glow must remain unavailable.

---

## 8. Auditability and Scientific Interpretation

The design must keep anatomical truth and runtime interpretation separable.

The scientific meaning of the formal payload is:
- activity is aggregated using validated anatomical occupancy weights
- activity values describe weighted activity carried by neuropils within the current graph scope
- the payload does not claim exclusive anatomical assignment per neuron
- graph-scoped correctness and full proofread alignment are related but distinct properties

The UI should be able to display both:
- `graph-scoped validation passed`
- `proofread roster alignment incomplete`

without forcing a misleading binary “official / unofficial” summary.

---

## 9. Required Test Strategy

The design requires tests at four levels:

### 9.1 Truth artifact tests

Validate that:
- synapse assignments compile from official raw files only
- occupancy aggregation preserves counts and fractions
- occupancy rows keep provenance fields intact

### 9.2 Validation contract tests

Validate that:
- graph-scoped validation status is correct
- proofread roster alignment status is reported separately
- payloads do not collapse these states into one boolean

### 9.3 Runtime aggregation tests

Validate that:
- `activity_mass` and `signed_activity` are both computed correctly
- grouping does not change underlying truth semantics
- top-node payloads retain multi-membership information
- invalid or mismatched inputs return unavailable state

### 9.4 UI/API contract tests

Validate that:
- `brain-view` payload exposes provenance fields
- grouped 8-neuropil display is marked as grouped
- the API never emits formal neuropil activity when truth artifacts are absent or invalid

---

## 10. Out of Scope

This design does not change:
- the current scientific embodiment choice of `flybody（果蝇身体与 MuJoCo 物理环境）`
- the current Phase 1 focus on `IL-only walking（仅模仿学习步行阶段）`
- the raw FlyWire release itself

This design also does not introduce:
- online `neuPrint（连接组查询服务）` dependence at training or evaluation time
- front-end-generated anatomical inference
- alternative non-FlyWire truth routes for formal neuropil activity

---

## 11. Approved Design Summary

The approved direction is:

- keep one formal data chain for neuropil activity
- define `node_neuropil_occupancy` as the only runtime-facing anatomical weighting source
- preserve multi-neuropil truth semantics
- expose both `activity_mass` and `signed_activity`
- separate formal truth, runtime aggregation, and display grouping
- fail closed in strict scientific mode
- make provenance and validation states explicit in API payloads

This design is the required basis for any later implementation work on formal neuropil activity mapping.
