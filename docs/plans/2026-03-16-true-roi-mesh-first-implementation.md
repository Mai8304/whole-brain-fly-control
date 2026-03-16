# True ROI Mesh First Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build the first anatomically grounded ROI asset pipeline for the neural console so the brain panel can render real ROI meshes and aggregate whole-brain activity into those regions.

**Architecture:** Keep the existing `FlyWire brain shell（FlyWire 果蝇脑整脑外壳）` pipeline. Add an anatomy-driven ROI asset layer using `VFB/FBbt（果蝇虚拟脑平台 / 果蝇解剖本体）` naming, offline `ROI mesh（脑区网格）` compilation, and a compiled `node -> ROI mapping（节点到脑区映射）` table. Runtime code should only load assets and aggregate node activity.

**Tech Stack:** Python, existing Fruitfly snapshot/compiled graph stack, JSON manifests, Parquet mapping tables, existing FastAPI console backend, existing React + `shadcn/ui（组件体系）` + `react-three-fiber（React 的 Three.js 3D 渲染层）` front end.

---

### Task 1: Freeze the V1 ROI manifest contract

**Files:**
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/roi_manifest.py`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_roi_manifest.py`
- Reference: `/Users/zhuangwei/Downloads/coding/Fruitfly/docs/plans/2026-03-16-true-roi-mesh-first-design.md`

**Step 1: Write the failing test**

Write tests that assert the V1 manifest contains exactly the approved `8` ROIs:
- `AL`
- `LH`
- `PB`
- `FB`
- `EB`
- `NO`
- `LAL`
- `GNG`

Also assert each ROI includes:
- `roi_id`
- `short_label`
- `display_name`
- `display_name_zh`
- `group`
- `description_zh`
- `default_color`
- `priority`

**Step 2: Run test to verify it fails**

Run:
```bash
./.venv-flywire/bin/python -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_roi_manifest.py -q
```

Expected: FAIL because the module does not exist yet.

**Step 3: Write minimal implementation**

Implement a deterministic manifest builder for the V1 ROI set and expose a loader/helper.

**Step 4: Run test to verify it passes**

Re-run the targeted test and confirm PASS.

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/roi_manifest.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_roi_manifest.py
git commit -m "feat: freeze v1 roi manifest"
```

---

### Task 2: Add a compiled node-to-ROI mapping contract

**Files:**
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/node_roi_map.py`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_node_roi_map.py`

**Step 1: Write the failing test**

Write tests asserting a mapping table loader/validator requires:
- `source_id`
- `node_idx`
- `roi_id`

Also test that all `roi_id` values must exist in the ROI manifest.

**Step 2: Run test to verify it fails**

Run:
```bash
./.venv-flywire/bin/python -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_node_roi_map.py -q
```

Expected: FAIL because the mapping module does not exist.

**Step 3: Write minimal implementation**

Implement:
- mapping schema validation
- manifest cross-checking
- loader helpers for Parquet

**Step 4: Run test to verify it passes**

Confirm PASS.

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/node_roi_map.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_node_roi_map.py
git commit -m "feat: add node roi mapping contract"
```

---

### Task 3: Add an ROI asset pack manifest

**Files:**
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/roi_asset_pack.py`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_roi_asset_pack.py`

**Step 1: Write the failing test**

Write tests asserting an ROI asset pack manifest includes:
- shell metadata
- `roi_manifest_path`
- `node_roi_map_path`
- per-ROI mesh entries
- coverage summary

**Step 2: Run test to verify it fails**

Run the targeted test and confirm failure.

**Step 3: Write minimal implementation**

Implement a JSON manifest builder/loader for:
- asset id/version
- shell asset metadata
- ROI mesh registry
- mapping table path
- mapping coverage summary

**Step 4: Run test to verify it passes**

Confirm PASS.

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/roi_asset_pack.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_roi_asset_pack.py
git commit -m "feat: add roi asset pack manifest"
```

---

### Task 4: Build a representative ROI mesh import/compile entrypoint

**Files:**
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/scripts/build_roi_asset_pack.py`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/scripts/test_build_roi_asset_pack.py`
- Reference existing: `/Users/zhuangwei/Downloads/coding/Fruitfly/scripts/import_flywire_brain_mesh.py`

**Step 1: Write the failing test**

Write a script-level test that:
- creates a temporary output directory
- writes a shell asset reference
- writes a manifest
- writes placeholder per-ROI mesh records
- writes a mapping-table pointer

This first test should focus on file layout and contract, not final atlas correctness.

**Step 2: Run test to verify it fails**

Run the targeted test and confirm failure.

**Step 3: Write minimal implementation**

Implement a first-pass builder that:
- reads the frozen ROI manifest
- consumes existing shell asset metadata
- creates the ROI asset-pack directory layout
- emits a manifest referencing ROI mesh files and mapping-table paths

**Step 4: Run test to verify it passes**

Confirm PASS.

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/scripts/build_roi_asset_pack.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/scripts/test_build_roi_asset_pack.py
git commit -m "feat: scaffold roi asset pack builder"
```

---

### Task 5: Add ROI activity aggregation from whole-brain node activity

**Files:**
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/roi_activity.py`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_roi_activity.py`

**Step 1: Write the failing test**

Write tests that:
- take synthetic per-node activity
- apply a synthetic `node -> ROI` map
- produce per-ROI activity
- produce per-ROI delta
- produce mapping coverage counts

**Step 2: Run test to verify it fails**

Run the targeted test and confirm failure.

**Step 3: Write minimal implementation**

Implement aggregation using:
- mean absolute activity per ROI
- stable ordering by manifest priority
- top-3 active ROI extraction

**Step 4: Run test to verify it passes**

Confirm PASS.

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/roi_activity.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_roi_activity.py
git commit -m "feat: add roi activity aggregation"
```

---

### Task 6: Thread ROI asset-pack support into the console API

**Files:**
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/ui/console_api.py`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/scripts/serve_neural_console_api.py`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_console_api_roi_assets.py`

**Step 1: Write the failing test**

Write API tests asserting the backend can return:
- ROI asset-pack metadata
- real ROI manifest entries
- ROI mesh registry
- ROI activity payload schema

**Step 2: Run test to verify it fails**

Run the targeted test and confirm failure.

**Step 3: Write minimal implementation**

Add optional `roi_asset_dir` support to the console API so it can expose:
- shell
- ROI manifest
- ROI meshes
- aggregated ROI activity payload

Do not add WebSocket support yet.

**Step 4: Run test to verify it passes**

Confirm PASS.

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/ui/console_api.py /Users/zhuangwei/Downloads/coding/Fruitfly/scripts/serve_neural_console_api.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_console_api_roi_assets.py
git commit -m "feat: expose roi asset pack in console api"
```

---

### Task 7: Add front-end types for true ROI meshes

**Files:**
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/types/console.ts`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/lib/console-api.ts`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/data/mockRoiAssetPack.ts`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/lib/console-api.test.ts`

**Step 1: Write the failing test**

Write a front-end data-layer test asserting the client can parse:
- ROI manifest entries
- ROI mesh registry
- ROI activity payload

**Step 2: Run test to verify it fails**

Run:
```bash
pnpm --dir /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console test
```

Expected: FAIL because the new ROI asset shape is not supported yet.

**Step 3: Write minimal implementation**

Add the new front-end contracts and mock payloads so the app can distinguish:
- shell asset
- ROI mesh assets
- ROI activity

**Step 4: Run test to verify it passes**

Confirm PASS.

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/types/console.ts /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/lib/console-api.ts /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/data/mockRoiAssetPack.ts /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/lib/console-api.test.ts
git commit -m "feat: add front-end roi mesh contracts"
```

---

### Task 8: Verification and documentation pass

**Files:**
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/README.md`
- Review all files touched in Tasks 1-7

**Step 1: Run focused Python verification**

```bash
./.venv-flywire/bin/python -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation /Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui /Users/zhuangwei/Downloads/coding/Fruitfly/tests/scripts -q
```

Expected: PASS.

**Step 2: Run front-end verification**

```bash
pnpm --dir /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console test
pnpm --dir /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console build
```

Expected: PASS.

**Step 3: Run full repository verification**

```bash
./.venv-flywire/bin/python -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests -q
```

Expected: PASS.

**Step 4: Update README**

Add a short section explaining:
- `ROI SoT（脑区单一事实来源）` policy
- ROI asset-pack layout
- the distinction between shell assets and true ROI meshes

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/README.md
git commit -m "docs: document true roi mesh asset pipeline"
```
