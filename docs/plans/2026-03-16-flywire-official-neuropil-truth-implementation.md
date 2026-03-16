# FlyWire Official Neuropil Truth Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the strict FlyWire-only neuropil truth pipeline using official FlyWire 783 release files, then switch the neural console to consume only validated neuropil occupancy artifacts.

**Architecture:** Create a read-only raw source layer for FlyWire 783 release files, derive `synapse_neuropil_assignment.parquet`, derive `node_neuropil_occupancy.parquet`, validate against official per-neuron neuropil count files, and expose neuropil activity only after validation succeeds.

**Tech Stack:** Python, Parquet, Feather, NumPy, existing Fruitfly compiled graph outputs, existing FastAPI console backend, existing React + `shadcn/ui（组件体系）` + `react-three-fiber（React 的 Three.js 3D 渲染层）` front end.

---

### Task 1: Freeze the FlyWire 783 raw source contract

**Files:**
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/flywire_neuropil_raw.py`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_flywire_neuropil_raw.py`
- Reference: `/Users/zhuangwei/Downloads/coding/Fruitfly/docs/plans/2026-03-16-flywire-official-neuropil-truth-design.md`

**Step 1: Write the failing test**

Write tests asserting the raw source contract requires these exact files:
- `flywire_synapses_783.feather`
- `per_neuron_neuropil_count_pre_783.feather`
- `per_neuron_neuropil_count_post_783.feather`
- `proofread_connections_783.feather`
- `proofread_root_ids_783.npy`

Also assert helper functions expose:
- release version
- required filenames
- checksum metadata keys

**Step 2: Run test to verify it fails**

Run:
```bash
./.venv-flywire/bin/python -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_flywire_neuropil_raw.py -q
```

Expected: FAIL because the module does not exist yet.

**Step 3: Write minimal implementation**

Implement:
- required-file lists
- release metadata helpers
- raw-layer directory validation helpers

**Step 4: Run test to verify it passes**

Confirm PASS.

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/flywire_neuropil_raw.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_flywire_neuropil_raw.py
git commit -m "feat: add flywire raw neuropil contract"
```

---

### Task 2: Add a raw-source import/freeze script

**Files:**
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/scripts/import_flywire_783_neuropil_release.py`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/scripts/test_import_flywire_783_neuropil_release.py`

**Step 1: Write the failing test**

Write tests asserting the import script:
- accepts a destination raw-source directory
- writes a manifest containing file names and checksums
- refuses to mark success when any required release file is missing
- preserves original filenames unchanged

**Step 2: Run test to verify it fails**

Run the targeted script test and confirm failure.

**Step 3: Write minimal implementation**

Implement a script that:
- imports or copies the required official files into a read-only raw-source directory
- writes `release_manifest.json`
- records checksums

**Step 4: Run test to verify it passes**

Confirm PASS.

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/scripts/import_flywire_783_neuropil_release.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/scripts/test_import_flywire_783_neuropil_release.py
git commit -m "feat: add flywire 783 raw import script"
```

---

### Task 3: Add the synapse-neuropil truth compiler

**Files:**
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/synapse_neuropil_assignment.py`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_synapse_neuropil_assignment.py`

**Step 1: Write the failing test**

Write tests asserting:
- synapse truth rows are derived from released synapse table columns
- output rows include:
  - `synapse_id`
  - `root_id`
  - `direction`
  - `neuropil`
  - `materialization`
  - `dataset`
- one raw synapse may yield separate `pre` and `post` assignment rows when appropriate

**Step 2: Run test to verify it fails**

Run:
```bash
./.venv-flywire/bin/python -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_synapse_neuropil_assignment.py -q
```

Expected: FAIL because the module does not exist.

**Step 3: Write minimal implementation**

Implement:
- feather input loading
- directional row emission
- deterministic sorting
- Parquet writing helper

**Step 4: Run test to verify it passes**

Confirm PASS.

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/synapse_neuropil_assignment.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_synapse_neuropil_assignment.py
git commit -m "feat: add synapse neuropil truth compiler"
```

---

### Task 4: Add node-level neuropil occupancy aggregation

**Files:**
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/node_neuropil_occupancy.py`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_node_neuropil_occupancy.py`

**Step 1: Write the failing test**

Write tests asserting aggregation from `synapse_neuropil_assignment` produces:
- one row per `(source_id, neuropil)`
- `pre_count`
- `post_count`
- `synapse_count`
- `occupancy_fraction`
- `node_idx` joined from compiled graph `node_index.parquet`

Also assert:
- a node may occupy multiple neuropils
- fractions normalize within each node

**Step 2: Run test to verify it fails**

Run the targeted test and confirm failure.

**Step 3: Write minimal implementation**

Implement:
- group-by aggregation
- node-index join
- fraction normalization
- Parquet writer

**Step 4: Run test to verify it passes**

Confirm PASS.

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/node_neuropil_occupancy.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_node_neuropil_occupancy.py
git commit -m "feat: add node neuropil occupancy aggregation"
```

---

### Task 5: Add official consistency validation

**Files:**
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/neuropil_truth_validation.py`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_neuropil_truth_validation.py`

**Step 1: Write the failing test**

Write tests asserting validation compares derived aggregates against:
- `per_neuron_neuropil_count_pre_783.feather`
- `per_neuron_neuropil_count_post_783.feather`

and returns:
- pass/fail status
- mismatch counts
- example mismatches

**Step 2: Run test to verify it fails**

Run the targeted test and confirm failure.

**Step 3: Write minimal implementation**

Implement:
- pre-count comparison
- post-count comparison
- summary payload generation

**Step 4: Run test to verify it passes**

Confirm PASS.

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/neuropil_truth_validation.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_neuropil_truth_validation.py
git commit -m "feat: add neuropil truth validation"
```

---

### Task 6: Switch backend/runtime semantics to neuropil truth

**Files:**
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/ui/console_api.py`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/scripts/serve_neural_console_api.py`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/roi_activity.py`
- Test: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_console_api.py`
- Test: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_console_api_roi_assets.py`

**Step 1: Write the failing test**

Write tests asserting research-mode brain payloads:
- use `neuropil` naming
- require validated `node_neuropil_occupancy.parquet`
- return unavailable if truth files are missing or unvalidated

**Step 2: Run test to verify it fails**

Run the targeted UI tests and confirm failure.

**Step 3: Write minimal implementation**

Implement:
- neuropil terminology updates
- strict file existence + validation gating
- null/unavailable responses when truth is absent

**Step 4: Run test to verify it passes**

Confirm PASS.

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/ui/console_api.py /Users/zhuangwei/Downloads/coding/Fruitfly/scripts/serve_neural_console_api.py /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/roi_activity.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_console_api.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_console_api_roi_assets.py
git commit -m "feat: switch console to flywire neuropil truth"
```

---

### Task 7: Downgrade and isolate the old dominant-evidence path

**Files:**
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/node_roi_compile.py`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/node_roi_map.py`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/scripts/build_node_roi_map.py`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/README.md`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/AGENTS.md`
- Test: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_node_roi_compile.py`

**Step 1: Write the failing test**

Write/update tests asserting:
- the old route is explicitly non-official
- official docs point to the FlyWire raw-release neuropil truth path
- research mode does not treat the old route as formal truth

**Step 2: Run test to verify it fails**

Run the targeted tests and confirm failure.

**Step 3: Write minimal implementation**

Implement naming and documentation changes that clearly isolate the old route as debug-only.

**Step 4: Run test to verify it passes**

Confirm PASS.

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/node_roi_compile.py /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/node_roi_map.py /Users/zhuangwei/Downloads/coding/Fruitfly/scripts/build_node_roi_map.py /Users/zhuangwei/Downloads/coding/Fruitfly/README.md /Users/zhuangwei/Downloads/coding/Fruitfly/AGENTS.md /Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_node_roi_compile.py
git commit -m "docs: downgrade old roi evidence route"
```

---

### Task 8: Run real local smoke validation from official files

**Files:**
- Outputs under: `/Users/zhuangwei/Downloads/coding/Fruitfly/outputs/compiled/flywire_public_full_v783/`
- Modify docs if needed: `/Users/zhuangwei/Downloads/coding/Fruitfly/README.md`

**Step 1: Import/freeze the official files**

Run the raw import script and confirm all required release files are present in the raw source layer.

**Step 2: Build 1-node synapse truth smoke**

Compile a 1-node `synapse_neuropil_assignment` smoke and verify a small validated output.

**Step 3: Build 4-node occupancy smoke**

Aggregate a 4-node `node_neuropil_occupancy` smoke and verify validation against official per-neuron counts.

**Step 4: Record timings and file sizes**

Document:
- raw source size
- synapse truth size
- occupancy size
- smoke runtimes

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/README.md
git commit -m "docs: record flywire neuropil truth smoke workflow"
```

