# Full Anatomical ROI Occupancy Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the current single-label ROI pipeline with a strict synapse-first anatomical truth chain that produces `synapse_roi_assignment.parquet` and derived `node_roi_occupancy.parquet`.

**Architecture:** Treat synapse-level ROI assignment as the first-order truth, batch-cache raw synapse ROI records offline, then derive node-level occupancy as a second-order artifact. In research mode, backend and frontend must refuse to substitute dominant evidence or preview data for the official occupancy truth.

**Tech Stack:** Python, `fafbseg.flywire（FlyWire 官方 Python 工具）`, Parquet, JSON manifests, existing compiled graph assets, existing FastAPI console backend, existing React + `shadcn/ui（组件体系）` + `react-three-fiber（React 的 Three.js 3D 渲染层）` front end.

---

### Task 1: Freeze the strict-truth artifact contracts

**Files:**
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/roi_truth_contract.py`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_roi_truth_contract.py`
- Reference: `/Users/zhuangwei/Downloads/coding/Fruitfly/docs/plans/2026-03-16-full-anatomical-roi-occupancy-design.md`

**Step 1: Write the failing test**

Write tests asserting contract helpers define:
- official truth filenames:
  - `synapse_roi_assignment.parquet`
  - `node_roi_occupancy.parquet`
- required columns for `synapse_roi_assignment`
- required columns for `node_roi_occupancy`
- explicit source-tag keys:
  - `dataset`
  - `materialization`
  - `roi_sot`
  - `truth_source`

**Step 2: Run test to verify it fails**

Run:
```bash
./.venv-flywire/bin/python -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_roi_truth_contract.py -q
```

Expected: FAIL because the contract module does not exist yet.

**Step 3: Write minimal implementation**

Implement deterministic helpers for:
- official filenames
- required schema field lists
- truth-source metadata helpers

**Step 4: Run test to verify it passes**

Re-run the targeted test and confirm PASS.

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/roi_truth_contract.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_roi_truth_contract.py
git commit -m "feat: add roi truth artifact contracts"
```

---

### Task 2: Add a synapse-level ROI assignment compiler

**Files:**
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/synapse_roi_compile.py`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_synapse_roi_compile.py`

**Step 1: Write the failing test**

Write tests asserting the compiler:
- calls `fafbseg.flywire.get_synapses(..., neuropils=True)`
- emits one row per synapse/ROI assignment
- records:
  - `synapse_id`
  - `root_id`
  - `direction`
  - `roi_id`
  - `materialization`
  - `dataset`
- ignores synapses whose `neuropil` is outside the approved V1 ROI set

**Step 2: Run test to verify it fails**

Run:
```bash
./.venv-flywire/bin/python -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_synapse_roi_compile.py -q
```

Expected: FAIL because the module does not exist.

**Step 3: Write minimal implementation**

Implement:
- a batch compiler that queries `get_synapses`
- a coercion path for returned DataFrame rows
- V1 neuropil-to-ROI collapse using the existing V1 ROI set
- deterministic row ordering

**Step 4: Run test to verify it passes**

Confirm PASS.

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/synapse_roi_compile.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_synapse_roi_compile.py
git commit -m "feat: add synapse roi assignment compiler"
```

---

### Task 3: Add batch-cache support for synapse truth

**Files:**
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/scripts/build_synapse_roi_assignment.py`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/scripts/test_build_synapse_roi_assignment.py`

**Step 1: Write the failing test**

Write a script-level test that:
- reads `node_index.parquet`
- batches root IDs
- writes per-batch JSON cache files
- resumes from existing batch files
- emits a final JSON summary only after all batches complete

Also assert that partial batch caches do **not** masquerade as final truth outputs.

**Step 2: Run test to verify it fails**

Run the targeted test and confirm failure.

**Step 3: Write minimal implementation**

Implement a resume-safe batch compiler that:
- writes `batch_<index>.json`
- stores raw truth rows plus per-batch summary
- sorts final rows deterministically
- writes `synapse_roi_assignment.parquet` only after the full compile stage

**Step 4: Run test to verify it passes**

Confirm PASS.

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/scripts/build_synapse_roi_assignment.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/scripts/test_build_synapse_roi_assignment.py
git commit -m "feat: add synapse roi batch compiler"
```

---

### Task 4: Add node-level occupancy aggregation

**Files:**
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/node_roi_occupancy.py`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_node_roi_occupancy.py`

**Step 1: Write the failing test**

Write tests asserting aggregation from `synapse_roi_assignment` produces:
- one row per `(source_id, roi_id)`
- `pre_count`
- `post_count`
- `synapse_count`
- `occupancy_fraction`
- preserved `dataset` and `materialization`

Also assert:
- a single node may occupy multiple ROIs
- there is no required single `primary_roi`

**Step 2: Run test to verify it fails**

Run:
```bash
./.venv-flywire/bin/python -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_node_roi_occupancy.py -q
```

Expected: FAIL because the aggregation module does not exist.

**Step 3: Write minimal implementation**

Implement:
- occupancy aggregation grouped by `(root_id, roi_id, direction)`
- `node_idx` joins from existing compiled graph `node_index.parquet`
- fraction normalization over total ROI-assigned synapses for each node

**Step 4: Run test to verify it passes**

Confirm PASS.

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/node_roi_occupancy.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_node_roi_occupancy.py
git commit -m "feat: add node roi occupancy aggregation"
```

---

### Task 5: Replace official ROI backend payloads with occupancy truth

**Files:**
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/ui/console_api.py`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/scripts/serve_neural_console_api.py`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/roi_activity.py`
- Test: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_console_api.py`
- Test: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_console_api_roi_assets.py`

**Step 1: Write the failing test**

Write tests asserting research-mode endpoints:
- return `null` / unavailable for ROI activity when `node_roi_occupancy.parquet` is absent
- do not fall back to dominant-evidence outputs
- expose occupancy coverage metadata when truth exists

**Step 2: Run test to verify it fails**

Run the targeted UI backend tests and confirm failure.

**Step 3: Write minimal implementation**

Implement:
- occupancy-truth loading path
- strict unavailable behavior
- source metadata in ROI activity payloads

**Step 4: Run test to verify it passes**

Confirm PASS.

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/ui/console_api.py /Users/zhuangwei/Downloads/coding/Fruitfly/scripts/serve_neural_console_api.py /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/roi_activity.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_console_api.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_console_api_roi_assets.py
git commit -m "feat: switch roi api to occupancy truth"
```

---

### Task 6: Downgrade the old dominant-evidence route

**Files:**
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/node_roi_compile.py`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/node_roi_map.py`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/scripts/build_node_roi_map.py`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/README.md`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/AGENTS.md`
- Test: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_node_roi_compile.py`

**Step 1: Write the failing test**

Write or update tests asserting:
- the old route is explicitly non-official
- filenames/docs no longer imply it is the canonical truth
- research-mode docs direct users to the synapse-first truth route

**Step 2: Run test to verify it fails**

Run the targeted tests and confirm failure.

**Step 3: Write minimal implementation**

Update:
- naming
- docs
- metadata
- comments

Do not remove the old route yet; reclassify it.

**Step 4: Run test to verify it passes**

Confirm PASS.

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/node_roi_compile.py /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/node_roi_map.py /Users/zhuangwei/Downloads/coding/Fruitfly/scripts/build_node_roi_map.py /Users/zhuangwei/Downloads/coding/Fruitfly/README.md /Users/zhuangwei/Downloads/coding/Fruitfly/AGENTS.md /Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_node_roi_compile.py
git commit -m "docs: downgrade dominant roi evidence route"
```

---

### Task 7: Run real smoke compiles and record evidence

**Files:**
- Outputs under: `/Users/zhuangwei/Downloads/coding/Fruitfly/outputs/compiled/flywire_public_full_v783/`
- Modify docs if needed: `/Users/zhuangwei/Downloads/coding/Fruitfly/README.md`

**Step 1: Run a 1-node smoke**

Run:
```bash
./.venv-flywire/bin/python /Users/zhuangwei/Downloads/coding/Fruitfly/scripts/build_synapse_roi_assignment.py \
  --compiled-graph-dir /Users/zhuangwei/Downloads/coding/Fruitfly/outputs/compiled/flywire_public_full_v783 \
  --cache-dir /Users/zhuangwei/Downloads/coding/Fruitfly/outputs/compiled/flywire_public_full_v783/synapse_roi_batches_debug \
  --resume \
  --limit-nodes 1 \
  --materialization 783 \
  --json
```

Expected:
- one batch cache written
- one `synapse_roi_assignment_debug.parquet` written
- no fallback data

**Step 2: Run a 4-node benchmark**

Use a 4-node benchmark to capture real timing and output sizes.

**Step 3: Verify occupancy aggregation**

Run the occupancy aggregation on the smoke truth file and confirm:
- multiple ROI rows can exist for a single node
- fractions sum correctly

**Step 4: Record results in docs**

Add a short note to `README.md` documenting:
- this is now the official strict-truth path
- expected runtime characteristics

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/README.md
git commit -m "docs: record occupancy truth smoke workflow"
```

