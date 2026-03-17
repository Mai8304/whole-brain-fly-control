# 3D Neuropil Glow Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a strict V1 `3D neuropil glow（3D 神经纤维区发光）` layer to the experiment console so the 3D brain view renders the approved eight grouped neuropils from the formal validated brain-view chain.

**Architecture:** Keep `formal truth（正式真值）` and `display transform（显示变换）` separate. The backend will declare `display_region_activity` and grouped mesh metadata; the frontend will render `brain shell + grouped neuropil meshes` without doing any regrouping or anatomy inference. Missing grouped data or grouped meshes must fall back to `shell-only` mode.

**Tech Stack:** Python, FastAPI, PyArrow, NumPy, React, TypeScript, `@react-three/fiber`, `@react-three/drei`, Vitest, pytest, existing neural-console asset/runtime APIs.

---

### Task 1: Add grouped V1 display activity to the formal brain-view contract

**Files:**
- Modify: `src/fruitfly/evaluation/runtime_activity_artifacts.py`
- Test: `tests/evaluation/test_runtime_activity_artifacts.py`
- Test: `tests/ui/test_console_api.py`
- Test: `tests/ui/test_console_replay_api.py`

**Step 1: Write the failing runtime-aggregation test**

Extend `tests/evaluation/test_runtime_activity_artifacts.py` with a case that starts from mixed fine-grained occupancy rows:

```python
def test_materialize_runtime_activity_artifacts_emits_grouped_display_region_activity(
    tmp_path: Path,
) -> None:
    ...
    payload, _ = materialize_runtime_activity_artifacts(
        compiled_graph_dir=compiled_graph_dir,
        eval_dir=eval_dir,
    ) or ({}, {})

    grouped = {
        entry["group_neuropil_id"]: entry
        for entry in payload["display_region_activity"]
    }
    assert grouped["AL"]["member_neuropils"] == ["AL_L", "AL_R"]
    assert grouped["AL"]["is_display_transform"] is True
    assert grouped["AL"]["view_mode"] == "grouped-neuropil-v1"
```

Use at least one fixture where:

- `AL_L` and `AL_R` both appear in raw `region_activity`
- `FB` appears as already-grouped

Assert that:

- grouped entries are emitted only once per approved grouped neuropil
- grouped `raw_activity_mass` equals the sum of member formal neuropils
- grouped `signed_activity` preserves signed sums

**Step 2: Run the targeted runtime test and verify it fails**

Run:

```bash
PYTHONPATH=src ./.venv-flywire/bin/python -m pytest \
  tests/evaluation/test_runtime_activity_artifacts.py::test_materialize_runtime_activity_artifacts_emits_grouped_display_region_activity \
  -q
```

Expected: FAIL because `display_region_activity` does not exist yet.

**Step 3: Implement grouped display aggregation in the runtime builder**

In `src/fruitfly/evaluation/runtime_activity_artifacts.py`, add a helper such as:

```python
def _build_grouped_display_region_activity(
    region_activity: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for region in region_activity:
        group_id = str(region["display_name"])
        entry = grouped.setdefault(
            group_id,
            {
                "group_neuropil_id": group_id,
                "raw_activity_mass": 0.0,
                "signed_activity": 0.0,
                "covered_weight_sum": 0.0,
                "node_count": 0,
                "member_neuropils": [],
                "view_mode": "grouped-neuropil-v1",
                "is_display_transform": True,
            },
        )
        entry["raw_activity_mass"] += float(region["raw_activity_mass"])
        entry["signed_activity"] += float(region["signed_activity"])
        entry["covered_weight_sum"] += float(region["covered_weight_sum"])
        entry["node_count"] += int(region["node_count"])
        entry["member_neuropils"].append(str(region["neuropil_id"]))
    return [
        {
            **entry,
            "member_neuropils": sorted(set(entry["member_neuropils"])),
        }
        for entry in sorted(grouped.values(), key=lambda item: str(item["group_neuropil_id"]))
    ]
```

Then attach it to the payload:

```python
payload.update(
    {
        "display_region_activity": _build_grouped_display_region_activity(region_activity),
        ...
    }
)
```

Do not remove fine-grained `region_activity`; grouped display data is an additional declared layer.

**Step 4: Add API-level regression coverage**

Extend `tests/ui/test_console_api.py` and `tests/ui/test_console_replay_api.py` so both `initial` and `replay` responses assert:

```python
assert payload["display_region_activity"][0]["view_mode"] == "grouped-neuropil-v1"
assert payload["display_region_activity"][0]["is_display_transform"] is True
```

Also assert that:

- `member_neuropils` is a list
- `group_neuropil_id` is one of the approved 8 values

**Step 5: Run focused backend verification**

Run:

```bash
PYTHONPATH=src ./.venv-flywire/bin/python -m pytest \
  tests/evaluation/test_runtime_activity_artifacts.py \
  tests/ui/test_console_api.py \
  tests/ui/test_console_replay_api.py \
  -q
```

Expected: PASS.

**Step 6: Commit**

```bash
git add src/fruitfly/evaluation/runtime_activity_artifacts.py \
  tests/evaluation/test_runtime_activity_artifacts.py \
  tests/ui/test_console_api.py \
  tests/ui/test_console_replay_api.py
git commit -m "feat: add grouped display region activity"
```

---

### Task 2: Extend the brain asset manifest and runtime asset API for grouped neuropil meshes

**Files:**
- Modify: `src/fruitfly/evaluation/brain_asset_manifest.py`
- Modify: `src/fruitfly/evaluation/neuropil_manifest.py`
- Modify: `scripts/import_flywire_brain_mesh.py`
- Modify: `outputs/ui-assets/flywire_brain_v141/manifest.json`
- Test: `tests/evaluation/test_brain_asset_manifest.py`
- Test: `tests/scripts/test_import_flywire_brain_mesh.py`
- Test: `tests/ui/test_console_api.py`

**Step 1: Write the failing manifest test**

Extend `tests/evaluation/test_brain_asset_manifest.py` to require a grouped mesh contract:

```python
def test_load_brain_asset_manifest_validates_grouped_neuropil_mesh_contract(tmp_path: Path) -> None:
    ...
    assert manifest["neuropil_manifest"][0]["render_asset_path"] == "AL.glb"
    assert manifest["neuropil_manifest"][0]["render_format"] == "glb"
```

Also add a checked-in manifest assertion:

```python
assert manifest["neuropil_manifest"][0]["render_asset_path"].endswith(".glb")
```

**Step 2: Run the focused manifest test and verify it fails**

Run:

```bash
PYTHONPATH=src ./.venv-flywire/bin/python -m pytest \
  tests/evaluation/test_brain_asset_manifest.py::test_load_brain_asset_manifest_validates_grouped_neuropil_mesh_contract \
  -q
```

Expected: FAIL because grouped mesh fields are not required yet.

**Step 3: Extend the manifest schema**

In `src/fruitfly/evaluation/neuropil_manifest.py`, extend `REQUIRED_NEUROPIL_MANIFEST_KEYS` with:

```python
"render_asset_path",
"render_format",
```

Update each grouped neuropil entry returned by `build_v1_neuropil_manifest()`:

```python
{
    "neuropil": "AL",
    ...
    "render_asset_path": "AL.glb",
    "render_format": "glb",
}
```

In `src/fruitfly/evaluation/brain_asset_manifest.py`, extend `with_runtime_asset_urls(...)` to attach per-neuropil runtime URLs:

```python
payload["neuropil_manifest"] = [
    {
        **entry,
        "asset_url": f"/api/console/brain-mesh/{entry['neuropil']}",
    }
    for entry in payload["neuropil_manifest"]
]
```

**Step 4: Add the grouped mesh asset API route**

In `src/fruitfly/ui/console_api.py`, add:

```python
@app.get("/api/console/brain-mesh/{neuropil}")
def brain_mesh(neuropil: str) -> FileResponse:
    manifest = _brain_asset_manifest(config)
    entry = _find_grouped_neuropil_asset(manifest, neuropil)
    if entry is None:
        raise HTTPException(status_code=404, detail=f"{neuropil} mesh not found")
    assert config.brain_asset_dir is not None
    mesh_path = config.brain_asset_dir / entry["render_asset_path"]
    if not mesh_path.exists():
        raise HTTPException(status_code=404, detail=f"{mesh_path.name} not found")
    return FileResponse(mesh_path, media_type="model/gltf-binary", filename=mesh_path.name)
```

Add a helper:

```python
def _find_grouped_neuropil_asset(manifest: dict[str, Any], neuropil: str) -> dict[str, Any] | None:
    return next(
        (entry for entry in manifest["neuropil_manifest"] if str(entry["neuropil"]) == neuropil),
        None,
    )
```

**Step 5: Update the import script and checked-in manifest**

In `scripts/import_flywire_brain_mesh.py`, continue using `build_brain_asset_manifest(...)` so grouped mesh paths come from the default neuropil manifest.

Update `outputs/ui-assets/flywire_brain_v141/manifest.json` so the checked-in asset manifest includes `render_asset_path` and `render_format` for each grouped neuropil.

**Step 6: Extend API tests**

In `tests/ui/test_console_api.py`, assert:

```python
brain_assets_payload = client.get("/api/console/brain-assets").json()
assert brain_assets_payload["neuropil_manifest"][0]["asset_url"].startswith("/api/console/brain-mesh/")
mesh_response = client.get("/api/console/brain-mesh/AL")
assert mesh_response.status_code == 200
```

Reuse the tmp asset directory fixture with one or more grouped mesh files such as `AL.glb`.

**Step 7: Run focused verification**

Run:

```bash
PYTHONPATH=src ./.venv-flywire/bin/python -m pytest \
  tests/evaluation/test_brain_asset_manifest.py \
  tests/scripts/test_import_flywire_brain_mesh.py \
  tests/ui/test_console_api.py \
  -q
```

Expected: PASS.

**Step 8: Commit**

```bash
git add src/fruitfly/evaluation/brain_asset_manifest.py \
  src/fruitfly/evaluation/neuropil_manifest.py \
  src/fruitfly/ui/console_api.py \
  scripts/import_flywire_brain_mesh.py \
  outputs/ui-assets/flywire_brain_v141/manifest.json \
  tests/evaluation/test_brain_asset_manifest.py \
  tests/scripts/test_import_flywire_brain_mesh.py \
  tests/ui/test_console_api.py
git commit -m "feat: expose grouped neuropil mesh assets"
```

---

### Task 3: Render grouped 3D neuropil glow in the frontend viewport

**Files:**
- Modify: `apps/neural-console/src/types/console.ts`
- Modify: `apps/neural-console/src/components/brain-shell-viewport.tsx`
- Modify: `apps/neural-console/src/components/brain-shell-appearance.ts`
- Modify: `apps/neural-console/src/components/experiment-console-page.tsx`
- Modify: `apps/neural-console/src/data/mockConsoleData.ts`
- Modify: `apps/neural-console/src/lib/messages.ts`
- Create: `apps/neural-console/src/components/brain-shell-viewport.test.tsx`
- Modify: `apps/neural-console/src/components/experiment-console-page.test.tsx`
- Modify: `apps/neural-console/src/lib/console-api.test.ts`
- Modify: `apps/neural-console/src/App.test.tsx`

**Step 1: Write the failing viewport test**

Create `apps/neural-console/src/components/brain-shell-viewport.test.tsx` with a test that renders the viewport in non-Three fallback mode and asserts grouped glow state is described in the overlay copy when grouped data exists:

```tsx
it('describes grouped neuropil glow availability from grouped display payload', () => {
  render(
    <ConsolePreferencesProvider>
      <BrainShellViewport
        shell={shell}
        brainAssets={brainAssets}
        displayRegionActivity={[
          {
            group_neuropil_id: 'FB',
            raw_activity_mass: 0.9,
            signed_activity: 0.3,
            covered_weight_sum: 1,
            node_count: 4,
            member_neuropils: ['FB'],
            view_mode: 'grouped-neuropil-v1',
            is_display_transform: true,
          },
        ]}
        glowAvailable
      />
    </ConsolePreferencesProvider>,
  )

  expect(screen.getByText(/grouped neuropil glow/i)).toBeInTheDocument()
})
```

**Step 2: Run the frontend test and verify it fails**

Run:

```bash
pnpm --dir apps/neural-console exec vitest run \
  src/components/brain-shell-viewport.test.tsx
```

Expected: FAIL because the viewport only knows about the shell.

**Step 3: Extend frontend payload types**

In `apps/neural-console/src/types/console.ts`, add:

```ts
export interface DisplayRegionActivityPayload {
  group_neuropil_id: string
  raw_activity_mass: number
  signed_activity: number
  covered_weight_sum: number
  node_count: number
  member_neuropils: string[]
  view_mode: 'grouped-neuropil-v1'
  is_display_transform: true
}
```

Then extend:

```ts
export interface BrainViewPayload {
  ...
  display_region_activity?: DisplayRegionActivityPayload[]
}

export interface BrainAssetNeuropilPayload {
  ...
  render_asset_path: string
  render_format: string
  asset_url?: string
}
```

**Step 4: Refactor the viewport into shell + glow layers**

In `apps/neural-console/src/components/brain-shell-viewport.tsx`:

- rename the props surface to include `displayRegionActivity`
- add a `GroupedNeuropilGlowLayer`
- load grouped `.glb` assets with `useGLTF`
- use per-neuropil `default_color` for identity
- derive display intensity from `raw_activity_mass`

Recommended structure:

```tsx
<Canvas ...>
  <ShellLayer shell={shell} theme={resolvedTheme} />
  {glowAvailable ? (
    <GroupedNeuropilGlowLayer
      brainAssets={brainAssets}
      displayRegionActivity={displayRegionActivity}
      theme={resolvedTheme}
    />
  ) : null}
  <OrbitControls ... />
</Canvas>
```

Add a small explicit display mapper:

```ts
function toGlowStrength(rawActivityMass: number, maxActivityMass: number) {
  if (maxActivityMass <= 0) return 0
  return Math.min(1, Math.log1p(rawActivityMass) / Math.log1p(maxActivityMass))
}
```

Use that for opacity/emissive strength. Do not mutate scientific payload values.

**Step 5: Keep fail-closed behavior**

Only enable glow when all of the following are true:

- `brainView.display_region_activity` exists and is non-empty
- `brainView.graph_scope_validation_passed === true`
- every rendered grouped neuropil has a matching grouped mesh `asset_url`

Otherwise, render shell-only and overlay copy such as:

```ts
t('experiment.viewport.footer.glowUnavailable')
```

**Step 6: Wire the viewport from the page**

In `apps/neural-console/src/components/experiment-console-page.tsx`, pass:

```tsx
<BrainShellViewport
  shell={brainView.shell}
  brainAssets={brainAssets}
  displayRegionActivity={brainView.display_region_activity ?? []}
  glowAvailable={
    brainView.graph_scope_validation_passed === true &&
    (brainView.display_region_activity?.length ?? 0) > 0
  }
/>
```

**Step 7: Update mock data, copy, and tests**

Update:

- `apps/neural-console/src/data/mockConsoleData.ts`
- `apps/neural-console/src/lib/messages.ts`
- `apps/neural-console/src/lib/console-api.test.ts`
- `apps/neural-console/src/components/experiment-console-page.test.tsx`
- `apps/neural-console/src/App.test.tsx`

Add frontend assertions that:

- grouped mesh manifest fields exist
- `display_region_activity` is passed through
- provenance still renders in the right-side panel
- shell-only fallback still works when glow data is absent

**Step 8: Run focused frontend verification**

Run:

```bash
pnpm --dir apps/neural-console exec vitest run \
  src/components/brain-shell-viewport.test.tsx \
  src/components/experiment-console-page.test.tsx \
  src/lib/console-api.test.ts \
  src/App.test.tsx
```

Expected: PASS.

**Step 9: Commit**

```bash
git add apps/neural-console/src/types/console.ts \
  apps/neural-console/src/components/brain-shell-viewport.tsx \
  apps/neural-console/src/components/brain-shell-appearance.ts \
  apps/neural-console/src/components/brain-shell-viewport.test.tsx \
  apps/neural-console/src/components/experiment-console-page.tsx \
  apps/neural-console/src/components/experiment-console-page.test.tsx \
  apps/neural-console/src/data/mockConsoleData.ts \
  apps/neural-console/src/lib/messages.ts \
  apps/neural-console/src/lib/console-api.test.ts \
  apps/neural-console/src/App.test.tsx
git commit -m "feat: render grouped 3d neuropil glow"
```

---

### Task 4: Final verification, docs touch-up, and browser smoke check

**Files:**
- Modify if needed: `README.md`
- Modify if needed: `docs/sot/flywire-neuron-roster-sot.md`

**Step 1: Add final docs clarification only if implementation changed runtime contract wording**

If the final implementation adds `display_region_activity` or grouped mesh API routes, update the user-facing docs with one short paragraph describing:

- grouped mesh asset exposure
- grouped display payload exposure
- shell-only fallback semantics

Keep the docs concise; do not restate the entire design doc.

**Step 2: Run the full Python verification set**

Run:

```bash
PYTHONPATH=src ./.venv-flywire/bin/python -m pytest \
  tests/evaluation/test_brain_view_contract.py \
  tests/evaluation/test_runtime_activity_artifacts.py \
  tests/evaluation/test_brain_asset_manifest.py \
  tests/ui/test_console_api.py \
  tests/ui/test_console_replay_api.py \
  tests/scripts/test_import_flywire_brain_mesh.py \
  -q
```

Expected: PASS.

**Step 3: Run the full targeted frontend verification set**

Run:

```bash
pnpm --dir apps/neural-console exec vitest run \
  src/components/brain-shell-appearance.test.ts \
  src/components/brain-shell-viewport.test.tsx \
  src/components/experiment-console-page.test.tsx \
  src/lib/console-api.test.ts \
  src/App.test.tsx
```

Expected: PASS.

**Step 4: Run the production build**

Run:

```bash
pnpm --dir apps/neural-console build
```

Expected: success, with at most existing chunk-size warnings.

**Step 5: Run a manual browser smoke check**

Serve the console with:

```bash
./.venv-flywire/bin/python scripts/serve_neural_console_api.py \
  --compiled-graph-dir outputs/compiled/flywire_public_full_v783 \
  --eval-dir outputs/eval/full_graph_straight_v1 \
  --checkpoint outputs/train/full_graph_straight_v1/checkpoints/epoch_0001.pt

pnpm --dir apps/neural-console dev --host 127.0.0.1 --port 4173
```

Verify in the browser:

- the right panel still shows provenance
- the 3D viewport shows shell plus grouped glow
- replay state shows `replay-live-step`
- missing grouped glow data would fall back to shell-only without mock glow

**Step 6: Commit docs-only follow-up if needed**

```bash
git add README.md docs/sot/flywire-neuron-roster-sot.md
git commit -m "docs: clarify grouped 3d neuropil glow contract"
```

