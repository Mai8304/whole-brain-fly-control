# Neuropil Single Truth Hard Delete Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Hard-delete the legacy `ROI preview（脑区预览）` runtime and tooling so the repository keeps only validated `neuropil truth（神经纤维区真值）`.

**Architecture:** Remove the old ROI asset-pack API and build helpers, stop the frontend from requesting or displaying ROI preview assets, and rename surviving runtime-facing metadata from ROI wording to neuropil wording where it belongs to the formal truth path. The runtime brain-view path stays anchored on `node_neuropil_occupancy.parquet` plus official validation.

**Tech Stack:** Python, FastAPI, PyArrow, React, TypeScript, Vitest/Jest-style frontend tests, pytest.

---

### Task 1: Lock backend removal with tests

**Files:**
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_console_api_roi_assets.py`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/scripts/test_serve_neural_console_api.py`

**Step 1: Write the failing test**

Assert that:
- `/api/console/roi-assets` is absent
- `/api/console/roi-mesh/AL` is absent
- CLI no longer accepts or resolves `--roi-asset-dir`

**Step 2: Run test to verify it fails**

Run:
```bash
python -m pytest tests/ui/test_console_api_roi_assets.py tests/scripts/test_serve_neural_console_api.py -q
```

Expected: FAIL because the old routes and CLI option still exist.

**Step 3: Write minimal implementation**

Remove:
- ROI routes from `console_api.py`
- `roi_asset_dir` from `ConsoleApiConfig`
- ROI startup wiring from `serve_neural_console_api.py`

**Step 4: Run test to verify it passes**

Confirm PASS.

### Task 2: Lock frontend removal with tests

**Files:**
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/lib/console-api.test.ts`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/App.test.tsx`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/experiment-console-page.test.tsx`

**Step 1: Write the failing test**

Assert that:
- console snapshot fetch no longer requests `/api/console/roi-assets`
- experiment console no longer shows ROI mesh-pack metric

**Step 2: Run test to verify it fails**

Run:
```bash
cd apps/neural-console && pnpm test -- --runInBand src/lib/console-api.test.ts src/App.test.tsx src/components/experiment-console-page.test.tsx
```

Expected: FAIL because the frontend still requests and renders ROI asset-pack data.

**Step 3: Write minimal implementation**

Remove:
- ROI asset type from shared snapshot
- ROI asset fetch from API client
- ROI asset log line
- ROI mesh-pack UI metric

**Step 4: Run test to verify it passes**

Confirm PASS.

### Task 3: Remove backend preview modules and rename surviving formal metadata

**Files:**
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/brain_asset_manifest.py`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/runtime_activity_artifacts.py`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/__init__.py`
- Delete: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/roi_asset_pack.py`
- Delete: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/roi_activity.py`
- Delete: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/node_roi_compile.py`
- Delete: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/node_roi_map.py`

**Step 1: Write the failing test**

Add or adjust tests so formal brain asset metadata uses `neuropil_manifest` rather than preview-style ROI-only naming.

**Step 2: Run test to verify it fails**

Run targeted pytest for brain asset/runtime tests.

**Step 3: Write minimal implementation**

Keep only formal display metadata and rename fields where appropriate.

**Step 4: Run test to verify it passes**

Confirm PASS.

### Task 4: Delete legacy scripts and test coverage

**Files:**
- Delete: `/Users/zhuangwei/Downloads/coding/Fruitfly/scripts/build_node_roi_map.py`
- Delete: `/Users/zhuangwei/Downloads/coding/Fruitfly/scripts/build_roi_asset_pack.py`
- Delete: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/scripts/test_build_node_roi_map.py`
- Delete: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/scripts/test_build_roi_asset_pack.py`
- Delete: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_node_roi_compile.py`
- Delete: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_node_roi_map.py`
- Delete: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_roi_asset_pack.py`
- Delete: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_roi_activity.py`

**Step 1: Verify no remaining imports**

Run:
```bash
rg -n "node_roi_map|roi_asset_pack|compile_node_roi_map|aggregate_roi_activity" src tests scripts apps
```

**Step 2: Delete the dead code**

Remove files and stale exports/imports.

**Step 3: Run focused tests**

Confirm no import errors remain.

### Task 5: Update docs and verify the remaining truth route

**Files:**
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/README.md`

**Step 1: Remove stale ROI preview documentation**

Delete:
- ROI preview endpoint references
- ROI preview import/build instructions
- migration notes that say runtime switch is unfinished

**Step 2: Describe the final single truth route**

Document only:
- formal FlyWire raw source
- formal neuropil truth artifacts
- brain shell asset path
- validated runtime behavior

**Step 3: Run final verification**

Run the targeted Python and frontend suites plus a final `rg` sweep for deleted legacy symbols.
