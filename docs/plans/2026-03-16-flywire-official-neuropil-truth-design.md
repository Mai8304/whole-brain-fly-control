# FlyWire Official Neuropil Truth Design

**Goal:** Define the official `FlyWire（果蝇连接组平台）`-only neuropil truth route for the Fruitfly research platform, using FlyWire 783 released files as the sole truth source for neuropil occupancy.

**Scope:** This design replaces the current mixed and online-query-heavy ROI direction with a strict `FlyWire official route（FlyWire 官方路线）`. It covers raw sources, derived truth artifacts, validation rules, and runtime semantics for the neural console.

**Relationship to existing plans:** This design supersedes the previously broader ROI truth framing when strict FlyWire-only compliance is required:
- `/Users/zhuangwei/Downloads/coding/Fruitfly/docs/plans/2026-03-16-full-anatomical-roi-occupancy-design.md`
- `/Users/zhuangwei/Downloads/coding/Fruitfly/docs/plans/2026-03-16-true-roi-mesh-first-design.md`

---

## 1. Problem Statement

The repository already has:
- real local FlyWire whole-brain snapshot assets
- real FlyWire shell mesh assets
- real V1 neuropil mesh imports
- temporary online-query-based node-to-region compilation experiments

The repository does **not** yet have:
- a FlyWire-release-first neuropil truth source layer
- a formal `synapse_neuropil_assignment.parquet`
- a formal `node_neuropil_occupancy.parquet`
- backend/frontend behavior strictly aligned to FlyWire neuropil semantics

The user explicitly requires:
- strict adherence to FlyWire official practice and data chain
- no mixed truth sources in the formal mainline
- no dominant-evidence or preview fallback in research mode

---

## 2. Strict FlyWire Scope

### 2.1 Official semantic scope

This route is not a generic all-ontology ROI truth path.
It is a strict:

`full neuropil-level truth（完整神经纤维区级真值）`

using FlyWire's official `neuropil（神经纤维区）` vocabulary and released data products.

### 2.2 Consequence

Formal terminology in the mainline should prefer:
- `neuropil`

and not the broader:
- `ROI`

unless explicitly discussing a more general concept outside the FlyWire-only truth path.

---

## 3. Single Source of Truth Policy

### 3.1 Raw source SoT

The official raw source layer must consist only of the released FlyWire 783 files:

- `flywire_synapses_783.feather`
- `per_neuron_neuropil_count_pre_783.feather`
- `per_neuron_neuropil_count_post_783.feather`
- `proofread_connections_783.feather`
- `proofread_root_ids_783.npy`

These files are the sole truth source for the formal neuropil truth mainline.

### 3.2 Excluded from formal truth SoT

The following may be used only for support, debugging, or future documentation, but not as the formal truth source:
- online `fafbseg.flywire.get_connectivity(...)`
- online `fafbseg.flywire.get_synapses(...)`
- `VFB/FBbt（果蝇虚拟脑平台 / 果蝇解剖本体）` naming as the formal truth identity layer
- preview payloads, mock payloads, heuristic glow, dominant evidence labels

### 3.3 Geometry source

The geometry layer for the formal neuropil panel should use FlyWire official neuropil mesh assets.

---

## 4. Formal Artifact Stack

### 4.1 Raw layer

This layer stores the official files unchanged.

Properties:
- read-only
- versioned
- checksum tracked
- never rewritten by derived compilers

### 4.2 First-order truth layer

**Artifact:** `synapse_neuropil_assignment.parquet`

Each row represents one synapse assigned to one neuropil for one root-direction view.

Minimum columns:
- `synapse_id`
- `root_id`
- `direction`
- `neuropil`
- `materialization`
- `dataset`

This is the official first-order truth layer for the project.

### 4.3 Derived occupancy layer

**Artifact:** `node_neuropil_occupancy.parquet`

Each row represents one `(source_id, neuropil)` occupancy record.

Minimum columns:
- `source_id`
- `node_idx`
- `neuropil`
- `pre_count`
- `post_count`
- `synapse_count`
- `occupancy_fraction`
- `materialization`
- `dataset`

This is the runtime-facing official derived artifact.

### 4.4 Provenance manifest

**Artifact:** `neuropil_truth_manifest.json`

It should include:
- release version
- raw filenames
- checksums
- compile timestamp
- compile tool version
- validation status
- mesh asset IDs

---

## 5. Generation Flow

The formal generation flow is:

`FlyWire 783 raw release files`
`-> synapse_neuropil_assignment.parquet`
`-> node_neuropil_occupancy.parquet`
`-> official consistency validation`
`-> runtime API/UI`

Key rule:
- the formal mainline starts from released files, not from online API queries

---

## 6. Validation Policy

Formal derived artifacts are not considered valid just because they can be built.

They must pass official consistency checks:

### 6.1 Pre-count validation

Aggregate `synapse_neuropil_assignment` into:
- `(root_id, neuropil) -> pre_count`

and compare against:
- `per_neuron_neuropil_count_pre_783.feather`

### 6.2 Post-count validation

Aggregate into:
- `(root_id, neuropil) -> post_count`

and compare against:
- `per_neuron_neuropil_count_post_783.feather`

### 6.3 Proofread consistency checks

Use:
- `proofread_connections_783.feather`
- `proofread_root_ids_783.npy`

for subset validation where relevant.

### 6.4 Failure rule

If validation fails:
- artifacts are not marked official
- runtime neuropil activity remains unavailable

---

## 7. Runtime Policy

### 7.1 Backend

The backend should expose neuropil activity only when:
- `synapse_neuropil_assignment.parquet` exists
- `node_neuropil_occupancy.parquet` exists
- validation has passed

Otherwise:
- shell geometry may still be shown
- neuropil activity payloads must be `null` / unavailable

### 7.2 Frontend

The neural console should treat the brain panel as:
- `neuropil activity（神经纤维区活动）`

not generic ROI truth.

It must not:
- fall back to dominant evidence
- fall back to preview payloads
- silently mix old node-to-ROI maps into the official neuropil view

---

## 8. V1 Display Scope

The V1 display scope remains the approved 8 FlyWire neuropils:
- `AL`
- `LH`
- `PB`
- `FB`
- `EB`
- `NO`
- `LAL`
- `GNG`

This is a display-scope restriction only.
It does not change the formal truth semantics:
- truth remains neuropil-first
- occupancy remains multi-neuropil capable

---

## 9. Migration Policy

### 9.1 Old route downgrade

The old single-label route must be explicitly downgraded:
- not official
- not canonical
- not allowed to power formal research-mode neuropil activity

### 9.2 Formal migration order

1. Freeze FlyWire 783 raw source layer
2. Build `synapse_neuropil_assignment.parquet`
3. Build `node_neuropil_occupancy.parquet`
4. Run official consistency validation
5. Switch backend/UI to the new truth artifacts

---

## 10. Non-Goals for This Phase

This phase does **not** include:
- full non-FlyWire ontology integration
- broader FBbt hierarchy expansion
- live online truth queries as official mainline
- single-label dominant neuropil as a formal project truth artifact

---

## 11. Acceptance Criteria

This design is considered implemented when:

1. the repository has a read-only FlyWire 783 raw source layer
2. `synapse_neuropil_assignment.parquet` is derived only from official FlyWire release data
3. `node_neuropil_occupancy.parquet` is derived from the synapse truth
4. official pre/post count validation passes
5. research-mode backend/frontend expose neuropil activity only from validated truth artifacts
6. no dominant-evidence or preview fallback remains in the formal mainline

