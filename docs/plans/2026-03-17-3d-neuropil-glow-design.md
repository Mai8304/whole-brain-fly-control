# 3D Neuropil Glow Design

**Goal:** Define a strict `3D neuropil glow（3D 神经纤维区发光）` design for the neural console that follows the approved `FlyWire official route（FlyWire 官方路线）`, preserves one authoritative data chain, and produces a clearly visible but scientifically honest V1 brain view.

**Scope:** This design covers the V1 grouped-neuropil glow path for the experiment console 3D viewport. It defines the data contract, rendering contract, asset integration contract, failure semantics, and testing strategy for `brain shell + grouped neuropil glow` rendering.

**Relationship to existing plans:**
- `/Users/zhuangwei/Downloads/coding/Fruitfly/docs/plans/2026-03-17-neuropil-activity-mapping-design.md`
- `/Users/zhuangwei/Downloads/coding/Fruitfly/docs/plans/2026-03-17-initial-replay-brain-view-unification-design.md`

---

## 1. Problem Statement

The repository already has:

- formal `neuropil truth（神经纤维区真值）` artifacts
- unified `initial / replay brain-view（初始 / 回放脑图）` provenance
- a working `brain shell（整脑外壳）` 3D viewport
- grouped V1 neuropil metadata for the approved eight display neuropils

The repository still lacks:

- a formal 3D rendering contract for neuropil glow
- a backend-declared grouped glow payload for V1 meshes
- a runtime asset contract for grouped neuropil meshes
- fail-closed rules for missing 3D glow data

The main risk is semantic drift:

- letting the frontend infer grouped activity on its own
- letting display effects rewrite anatomical truth
- using mesh availability or visual convenience as if it were truth

For this project, 3D glow is not a decorative extra layer. It is a visual projection of formal, validated neuropil activity and must behave as such.

---

## 2. Approved Design Principles

The approved V1 design is governed by these principles:

- preserve one authoritative formal data chain
- keep `formal truth（正式真值）`, `display transform（显示变换）`, and `3D rendering（3D 渲染）` as separate layers
- use grouped V1 neuropils for V1 3D glow
- keep laterality-preserving truth in backend truth artifacts; do not force the 3D layer to invent laterality
- use color for neuropil identity and intensity for activity strength
- fail closed in `research strict mode（科研严格模式）`
- keep V1 visually legible without using heavy postprocessing

---

## 3. Scope and Non-Goals

### 3.1 In scope

V1 will render:

- `brain shell（整脑外壳）`
- `8 grouped neuropil meshes（8 个分组神经纤维区网格）`
- activity-driven glow intensity from formal grouped payloads
- right-panel provenance that remains aligned with the active 3D state

The grouped V1 neuropils are fixed to:

- `AL`
- `LH`
- `PB`
- `FB`
- `EB`
- `NO`
- `LAL`
- `GNG`

### 3.2 Out of scope

V1 does not include:

- `AL_L / AL_R` style laterality-specific 3D meshes
- `node position mapping（神经元空间位置映射）`
- `postprocessing bloom（后处理辉光）`
- click/hover data exploration beyond existing viewport controls
- any frontend regrouping of formal region activity

---

## 4. Approach Comparison

### Approach A: Mesh Material Swap

Load grouped neuropil meshes and change their material opacity/emissive values directly from activity.

Pros:

- simple implementation
- fits current `react-three-fiber（React Three.js 渲染层）`

Cons:

- visual effect can be too weak
- easy to end up with “brighter plastic” rather than clear glow

### Approach B: Shell + Neuropil Mesh Overlay

Keep the shell as a low-contrast base layer and add grouped neuropil meshes as a dedicated overlay layer with activity-driven opacity and emissive tuning.

Pros:

- best balance of scientific discipline and visible effect
- clean separation of shell and activity layers
- aligns with current V1 grouped-neuropil display semantics

Cons:

- requires a clearer asset manifest and grouped payload contract
- needs careful transparency layering

### Approach C: Overlay + Bloom

Build Approach B, then add postprocessing bloom to create stronger glow halos.

Pros:

- strongest visual effect

Cons:

- higher rendering complexity
- more parameter tuning
- easier to hide contract problems behind visual polish

### Recommended approach

Recommend **Approach B** for V1.

This preserves formal correctness while still making the 3D brain visibly “light up” in a way users can immediately see.

---

## 5. Single Authoritative Data Chain for 3D Glow

The formal V1 3D glow chain must be:

`FlyWire 783 official truth`
`-> synapse_neuropil_assignment.parquet`
`-> node_neuropil_occupancy.parquet`
`-> neuropil_truth_validation.json`
`-> runtime node_activity aggregation`
`-> backend grouped display transform`
`-> brain-view payload`
`-> grouped neuropil mesh rendering`

This means:

- the frontend does not regroup formal activity
- the frontend does not infer missing grouped activity
- the frontend only renders grouped glow if backend grouped display payload exists

The 3D layer is a consumer of declared display payloads, not a source of truth.

---

## 6. 3D Glow Data Contract

### 6.1 Formal source for the 3D layer

The 3D glow layer must consume only the validated `brain-view（脑图载荷）` response.

It must not directly read:

- raw truth files
- compiled occupancy parquet files
- mesh directory names
- heuristic region groupings

### 6.2 Grouped display payload

The backend must expose a dedicated grouped payload for the 3D layer:

- `display_region_activity`

This payload is display-facing and explicitly derived from formal truth. It does not replace truth-level `region_activity`.

Each entry should include:

- `group_neuropil_id`
- `raw_activity_mass`
- `signed_activity`
- `covered_weight_sum`
- `node_count`
- `member_neuropils`
- `view_mode = grouped-neuropil-v1`
- `is_display_transform = true`

### 6.3 Grouped identifier restrictions

`group_neuropil_id` may only be one of:

- `AL`
- `LH`
- `PB`
- `FB`
- `EB`
- `NO`
- `LAL`
- `GNG`

If the backend cannot produce this grouped payload cleanly, the 3D glow layer must be unavailable.

---

## 7. 3D Rendering Contract

### 7.1 Layer model

The scene is composed of three conceptual layers:

1. `background`
2. `brain shell`
3. `grouped neuropil glow meshes`

The shell is always the low-contrast anatomical context layer.
The glow meshes are the activity-carrying layer.

### 7.2 Shell behavior

The shell:

- remains low-opacity
- remains low-saturation
- does not encode activity
- exists even when glow is unavailable

### 7.3 Neuropil glow behavior

Each grouped neuropil mesh should have:

- `default_color`
- low inactive opacity
- higher active opacity
- emissive intensity scaled by display activity

V1 should use:

- identity-first colors from the official/grouped manifest
- activity strength mapped through a declared display function

V1 should not use:

- hidden normalization
- arbitrary rainbow heatmaps
- bloom-based halo postprocessing

### 7.4 Intensity mapping

The display function should be explicit and read-only.

Recommended V1 display rule:

- use `raw_activity_mass` as the scientific source
- use a clamped non-linear display mapping such as log-scaled normalization for emissive strength
- preserve raw values in payloads for auditability

The rendering layer may transform values for visibility, but must never redefine the stored activity values themselves.

---

## 8. UI and Asset Integration Contract

### 8.1 Brain asset manifest requirements

The current manifest exposes shell metadata and grouped neuropil descriptors, but V1 glow requires grouped mesh runtime metadata as well.

The formal runtime-facing asset layer should expose, for each grouped neuropil:

- `neuropil`
- `asset_url`
- `render_asset_path`
- `render_format`
- `default_color`
- `priority`

This should be delivered by the `brain-assets（脑资产）` API, not inferred on the client from filesystem conventions.

### 8.2 Frontend lookup rules

The frontend may only perform this mapping:

`display_region_activity.group_neuropil_id`
`-> grouped neuropil asset manifest entry`
`-> grouped mesh instance`

The frontend must not:

- collapse or merge formal `region_activity` on its own
- guess mesh names
- fall back to “nearest available” mesh

### 8.3 Viewport structure

The current single viewport component should evolve into a composition like:

- `ShellLayer`
- `NeuropilGlowLayer`
- `ViewportHUD`

This keeps shell rendering, glow rendering, and overlay copy separable and testable.

---

## 9. Failure Semantics

The 3D glow layer must fail closed.

Only `shell-only` mode is allowed when any of the following is true:

- `graph_scope_validation_passed != true`
- `display_region_activity` is missing
- grouped asset manifest entries are missing
- grouped mesh asset lookup fails
- grouped payload identifiers do not match grouped asset identifiers

In those cases:

- shell remains visible
- grouped glow does not render
- UI continues to show provenance and/or unavailable messaging

No synthetic fallback glow is allowed.

---

## 10. Testing Strategy

Minimum required coverage:

1. backend groups formal region activity into `display_region_activity`
2. backend includes grouped mesh manifest data in `brain-assets`
3. frontend renders shell-only when grouped glow data is unavailable
4. frontend renders grouped glow meshes when grouped data is present
5. provenance stays visible in the right panel when 3D glow is active
6. invalid grouped identifiers do not render fallback glow

Recommended verification layers:

- Python contract tests for grouped payload generation
- Python API tests for `brain-view` and `brain-assets`
- frontend unit tests for viewport state transitions
- browser-level verification that at least one grouped mesh visibly activates on recorded replay

---

## 11. V1 Implementation Summary

V1 should deliver:

- grouped backend display activity for 8 approved neuropils
- grouped mesh runtime manifest
- shell + grouped mesh overlay rendering
- activity-driven mesh intensity
- shell-only fail-closed fallback
- no bloom
- no laterality-specific 3D glow

This gives the project a first real 3D neuropil glow layer that is both visible and scientifically disciplined.

---

## 12. Conclusion

The approved V1 direction is:

- keep formal truth fine-grained in backend truth artifacts
- declare grouped display activity in backend payloads
- declare grouped neuropil meshes in the runtime asset manifest
- render shell plus grouped glow meshes in the frontend
- fail closed whenever the grouped formal path is incomplete

This is the recommended official-best-practice route for introducing 3D neuropil glow into the current Fruitfly console.
