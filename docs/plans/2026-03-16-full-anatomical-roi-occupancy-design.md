# Full Anatomical ROI Occupancy Design

**Goal:** Replace the temporary `dominant ROI evidence（主导脑区证据）` route with a strictly anatomy-first `full anatomical ROI occupancy truth（完整解剖脑区归属真值）` pipeline for the Fruitfly research platform.

**Scope:** This design defines the new official ROI data chain for offline compilation, API exposure, and neural-console rendering. It supersedes the current single-label `node_roi_map` as the repository's formal ROI ground truth path.

**Relationship to existing plans:** This design refines and partially supersedes:
- `/Users/zhuangwei/Downloads/coding/Fruitfly/docs/plans/2026-03-16-true-roi-mesh-first-design.md`
- `/Users/zhuangwei/Downloads/coding/Fruitfly/docs/plans/2026-03-16-neural-console-ui-design.md`
- `/Users/zhuangwei/Downloads/coding/Fruitfly/docs/plans/2026-03-16-neural-console-ui-refinement-design.md`

---

## 1. Problem Statement

The repository already has:
- real `FlyWire（果蝇连接组平台）` whole-brain snapshot data
- real compiled whole-brain graph assets
- real `FlyWire neuropil mesh（FlyWire 脑区网格）` assets for the V1 ROI set
- a temporary `dominant ROI evidence（主导脑区证据）` compilation route

The repository does **not** yet have:
- a formal `synapse-level ROI truth（突触级脑区真值）` table
- a formal `node-level ROI occupancy（节点级脑区占据）` table derived from that truth
- API/UI behavior that strictly refuses to substitute heuristic or partial ROI labels for anatomy truth

The user explicitly requires:
- all research data chains must be real
- all sources must be matched and auditable
- if full anatomical truth is unavailable, UI/API must return `null` or unavailable
- no fabricated, guessed, or silently downgraded ROI outputs

---

## 2. Best-Practice Interpretation

The recommended scientific best practice is:

`ROI SoT（脑区单一事实来源）`
`-> atlas / annotation volume（图谱 / 标注体数据）`
`-> ROI geometry（脑区几何）`
`-> synapse-level ROI assignment（突触级脑区归属）`
`-> node-level occupancy aggregation（节点级占据聚合）`
`-> runtime visualization（运行时可视化）`

Important consequence:
- `node -> ROI` is **not** the first truth layer
- synapses (or equivalent ROI-annotated point-level assignments) are the first truth layer
- node-level occupancy is a derived product

This repository should therefore treat:
- `synapse_roi_assignment.parquet` as first-order ground truth
- `node_roi_occupancy.parquet` as a derived, but still official, runtime artifact

---

## 3. Strict Switch Policy

This design adopts a strict switch:

1. `dominant ROI evidence（主导脑区证据）` is no longer an official ROI truth artifact.
2. The current single-label `node_roi_map.parquet` is no longer the formal project target.
3. UI/API may not substitute dominant evidence for anatomical occupancy.
4. When full occupancy truth is unavailable, ROI-specific brain activity endpoints must return `null` / unavailable.

Allowed role for old single-label outputs:
- debugging
- benchmark comparison
- migration diagnostics

Disallowed role:
- official scientific visualization
- official occupancy analysis
- default UI/API responses in research mode

---

## 4. Single Source of Truth Policy

### 4.1 ROI naming and ontology

`VFB/FBbt（Virtual Fly Brain / Drosophila Anatomy Ontology，果蝇虚拟脑平台 / 果蝇解剖本体）` remains the SoT for:
- ROI naming
- ROI identity
- ROI hierarchy
- explanatory text

### 4.2 Whole-brain node space

The local compiled `FlyWire-derived whole-brain graph（基于 FlyWire 的全脑图）` remains the SoT for:
- `source_id`
- `node_idx`
- node activity values

### 4.3 Geometry source

The V1 brain panel should continue using real FlyWire-aligned neuropil geometry:
- shell: existing `brain_shell.glb`
- ROI meshes: existing V1 ROI mesh imports

### 4.4 Truth-source tagging

All official ROI truth artifacts must carry:
- `dataset`
- `materialization`
- `roi_sot`
- `geometry_source`
- `truth_source`

This prevents future silent mixing of data sources.

---

## 5. Official Artifact Model

### 5.1 First-order truth

**File:** `synapse_roi_assignment.parquet`

Each row represents one real synapse assigned to one ROI.

Minimum columns:
- `synapse_id`
- `root_id`
- `direction`
- `roi_id`
- `materialization`
- `dataset`

Semantics:
- `root_id` identifies the query neuron owning the synapse in the current directional view
- `direction` is `pre` or `post`
- `roi_id` is the ROI assigned to that synapse

This is the first-order truth layer.

### 5.2 Derived official occupancy

**File:** `node_roi_occupancy.parquet`

Each row represents one `(source_id, roi_id)` occupancy record.

Minimum columns:
- `source_id`
- `node_idx`
- `roi_id`
- `pre_count`
- `post_count`
- `synapse_count`
- `occupancy_fraction`
- `materialization`
- `dataset`

Semantics:
- one node may occupy multiple ROIs
- `occupancy_fraction` is the ROI-specific fraction of all ROI-assigned synapses for that node
- there is no single official `primary_roi` field in this layer

### 5.3 Optional provenance artifact

**File:** `roi_truth_manifest.json`

This records:
- ROI manifest version
- geometry asset IDs
- source table versions
- batch-compile timestamps
- coverage summaries

---

## 6. Generation Strategy

### 6.1 Query source

The official first-order truth should be built from:
- `fafbseg.flywire.get_synapses(..., neuropils=True)` or an equivalent synapse-level ROI source

Not from:
- `get_connectivity(..., neuropils=True)` as the formal mainline
- `get_synapse_counts(by_neuropil=True)` as the formal truth layer

Reason:
- `get_synapses(..., neuropils=True)` returns synapse-level records with ROI assignment
- counts and connectivity tables are already aggregated views

### 6.2 Batch-wise cached compile

The official engineering route should be:

`query batch of root IDs`
`-> write raw synapse ROI batch cache`
`-> resume-safe batch recovery`
`-> compile full synapse truth`
`-> aggregate node occupancy`

This is preferred over:
- one-shot whole-brain compilation
- runtime online recomputation
- lossy single-label mapping

### 6.3 Failure policy

If a batch fails:
- preserve completed raw batches
- do not write partial official final artifacts as if complete
- mark outputs unavailable until final aggregation succeeds

---

## 7. Runtime Policy

### 7.1 Backend

The backend should expose:
- shell assets
- ROI mesh assets
- ROI manifest
- occupancy coverage summary
- ROI activity only when `node_roi_occupancy.parquet` exists

It must not synthesize ROI glow from dominant evidence in research mode.

### 7.2 Frontend

The neural console should:
- render ROI glow only from official occupancy outputs
- return unavailable / null when those outputs are absent
- continue showing body video and shell geometry independently when available

### 7.3 Strict null policy

Research mode rule:
- no occupancy truth -> no ROI activity payload
- no silent fallback to preview
- no silent fallback to dominant single-label evidence

---

## 8. Migration Policy

The current `dominant ROI evidence` route may remain temporarily for:
- debugging
- differential checks
- performance comparisons

But it must be renamed and downgraded in semantics:
- no official `node_roi_map.parquet`
- if retained, use a clearly non-official name such as `node_roi_dominant_evidence.parquet`

The official output names after migration should be:
- `synapse_roi_assignment.parquet`
- `node_roi_occupancy.parquet`

---

## 9. V1 ROI Scope

The V1 strict-truth rollout still uses the approved `8` representative ROIs:
- `AL`
- `LH`
- `PB`
- `FB`
- `EB`
- `NO`
- `LAL`
- `GNG`

This is a scope limit, not a semantic downgrade.

The semantics remain:
- synapse-level truth first
- node-level occupancy second

---

## 10. Non-Goals for This Phase

This phase does **not** include:
- full 78-ROI expansion
- neuron morphology-level occupancy fractions
- UI fallback heuristics
- converting occupancy into a single official dominant label

---

## 11. Acceptance Criteria

This design is considered implemented when:

1. `dominant ROI evidence` is no longer the official ROI truth path
2. `synapse_roi_assignment.parquet` is generated from real synapse-level ROI data
3. `node_roi_occupancy.parquet` is generated from that synapse truth
4. backend returns `null / unavailable` when occupancy truth is absent
5. frontend ROI glow depends only on official occupancy truth
6. all artifacts are source-tagged and auditable

