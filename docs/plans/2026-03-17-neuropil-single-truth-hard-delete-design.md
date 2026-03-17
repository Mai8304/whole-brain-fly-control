# Neuropil Single Truth Hard Delete Design

**Goal:** Remove the legacy `ROI preview（脑区预览）` pipeline from the Fruitfly research platform and leave a single runtime truth path based only on validated `neuropil truth（神经纤维区真值）`.

**Scope:** This design covers backend API removal, frontend contract removal, deletion of deprecated compile/asset utilities, and semantic cleanup of remaining runtime-facing asset metadata.

---

## 1. Problem

The repository already runs the formal brain-view path from:

- `synapse_neuropil_assignment.parquet`
- `node_neuropil_occupancy.parquet`
- `neuropil_truth_validation.json`

But the repository still exposes a legacy parallel route:

- `/api/console/roi-assets`
- `/api/console/roi-mesh/{roi_id}`
- `node_roi_map.parquet`
- `roi_asset_pack`
- ROI mesh import/build helper scripts
- frontend snapshot/types/UI that still fetch and display ROI asset-pack data

This leaves two contradictory mental models alive:

- formal `neuropil truth（神经纤维区真值）`
- legacy `ROI preview（脑区预览）`

That violates the repository rule that formal brain-region display must use a single official truth chain.

## 2. Decision

Use a hard-delete migration.

The repository will:

- keep only validated `neuropil truth（神经纤维区真值）`
- remove the legacy ROI preview API surface entirely
- remove old ROI preview compiler/asset helpers entirely
- stop documenting ROI preview as a supported runtime path

The repository will not keep a compatibility shim, hidden fallback, or dual contract.

## 3. Runtime Contract After Migration

The neural console runtime will expose only:

- `brain-view`
- `brain-assets`
- `timeline`
- `summary`
- replay endpoints

`brain-view` remains powered only by validated `node_neuropil_occupancy.parquet`.

`brain-assets` remains the only geometry metadata endpoint. Its manifest should describe the approved displayed `neuropils（神经纤维区）`, not a legacy ROI preview pack.

## 4. Deletion Boundary

### 4.1 Delete completely

- backend ROI asset endpoints and config
- frontend ROI asset fetches, types, and metrics
- `node_roi_compile`
- `node_roi_map`
- `roi_asset_pack`
- `roi_activity`
- `build_node_roi_map.py`
- `build_roi_asset_pack.py`
- ROI preview tests tied to the old route

### 4.2 Keep but rename semantically

The formal displayed eight-region metadata can stay, but should move from generic `roi_manifest` naming toward `neuropil_manifest`.

This is not keeping the old preview route. It is renaming the surviving formal display metadata to match the actual truth semantics.

## 5. Validation Rules

After migration:

- requests to `/api/console/roi-assets` must no longer exist
- requests to `/api/console/roi-mesh/{roi_id}` must no longer exist
- server startup must not accept `--roi-asset-dir`
- frontend live snapshot fetch must not request ROI assets
- experiment console must not render ROI mesh-pack status
- formal `neuropil truth（神经纤维区真值）` gating and unavailable behavior must stay intact

## 6. Risks

### 6.1 Dirty worktree risk

The frontend worktree already has local edits. The implementation must patch only the ROI-removal slices and avoid reverting unrelated user changes.

### 6.2 Naming migration risk

Some runtime payload fields still use `roi_*` names even though the source is formal `neuropil` truth. These should be cleaned carefully so tests and UI stay aligned.

## 7. Recommended Execution Order

1. Lock backend removal with failing tests.
2. Remove backend ROI endpoints and CLI/config support.
3. Lock frontend removal with failing tests.
4. Remove frontend ROI fetch/display/types.
5. Delete unused ROI preview modules/scripts/tests.
6. Update docs and run targeted verification.
