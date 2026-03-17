# Initial/Replay Brain-View Unification Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make `initial /api/console/brain-view` and `replay /api/console/replay/brain-view` provably consume the same formal `neuropil（神经纤维区）` data chain, with strict stale-cache invalidation and explicit provenance.

**Architecture:** Keep `brain_view.json / timeline.json` as materialized cache artifacts for the initial path, but treat them as disposable cache rather than source of truth. Both initial and replay responses must be built from the same canonical `runtime_activity_artifacts（运行时活动产物构建器）` contract; only `step_id` and `artifact_origin` may differ. Add freshness invalidation for cached artifacts based on dependency mtimes, then expose provenance markers to both API consumers and the right-side console panel.

**Tech Stack:** Python, FastAPI, PyArrow, NumPy, pytest, React, TypeScript, Vitest, existing `brain_view_contract` and neural-console UI.

---

### Task 1: Tighten materialized-cache stale invalidation for initial brain-view

**Files:**
- Modify: `src/fruitfly/ui/console_api.py`
- Test: `tests/ui/test_console_api.py`

**Step 1: Write the failing test for dependency-freshness invalidation**

Add a new pytest case next to the existing stale-contract test that creates:

- a valid-looking `brain_view.json`
- a valid-looking `timeline.json`
- a newer `final_node_activity.npy`

Assert that `GET /api/console/brain-view` rematerializes the payload instead of trusting the stale cache.

```python
def test_console_api_rematerializes_when_final_node_activity_is_newer(tmp_path: Path) -> None:
    ...
    old_brain_view_path.write_text(json.dumps(stale_payload), encoding="utf-8")
    old_timeline_path.write_text(json.dumps(stale_timeline), encoding="utf-8")
    time.sleep(0.01)
    np.save(eval_dir / "final_node_activity.npy", np.asarray([0.2, 0.6], dtype=np.float32))

    brain_payload = client.get("/api/console/brain-view").json()

    assert brain_payload["artifact_contract_version"] == RUNTIME_ACTIVITY_ARTIFACT_VERSION
    assert brain_payload["mapping_coverage"]["neuropil_mapped_nodes"] == 2
```

**Step 2: Run the targeted test to verify it fails**

Run:

```bash
PYTHONPATH=src ./.venv-flywire/bin/python -m pytest tests/ui/test_console_api.py::test_console_api_rematerializes_when_final_node_activity_is_newer -q
```

Expected: FAIL because `_runtime_activity_artifacts_are_current(...)` only validates contract shape, not input freshness.

**Step 3: Implement dependency-based freshness checks**

In `src/fruitfly/ui/console_api.py`, extend `_runtime_activity_artifacts_are_current(...)` to require:

- both artifacts exist
- both artifacts pass contract checks
- both artifacts are at least as new as all required inputs

Add a helper that computes the latest dependency mtime:

```python
def _latest_runtime_activity_dependency_mtime(config: ConsoleApiConfig) -> float | None:
    dependency_paths = [
        config.eval_dir / "activity_trace.json",
        config.eval_dir / "final_node_activity.npy",
        config.eval_dir / "summary.json",
        config.compiled_graph_dir / "node_neuropil_occupancy.parquet",
        config.compiled_graph_dir / "neuropil_truth_validation.json",
        config.compiled_graph_dir / "node_index.parquet",
    ]
    if any(not path.exists() for path in dependency_paths):
        return None
    return max(path.stat().st_mtime for path in dependency_paths)
```

Then gate the cache:

```python
latest_dependency_mtime = _latest_runtime_activity_dependency_mtime(config)
if latest_dependency_mtime is None:
    return False
if brain_view_path.stat().st_mtime < latest_dependency_mtime:
    return False
if timeline_path.stat().st_mtime < latest_dependency_mtime:
    return False
```

**Step 4: Add one truth-drift regression test**

In `tests/ui/test_console_api.py`, add a second focused test where:

- cache files are valid
- `node_neuropil_occupancy.parquet` becomes newer

Assert rematerialization happens for truth drift as well.

**Step 5: Run the targeted console API tests**

Run:

```bash
PYTHONPATH=src ./.venv-flywire/bin/python -m pytest \
  tests/ui/test_console_api.py::test_console_api_rematerializes_stale_brain_view_contract \
  tests/ui/test_console_api.py::test_console_api_rematerializes_when_final_node_activity_is_newer \
  tests/ui/test_console_api.py::test_console_api_rematerializes_when_neuropil_truth_is_newer \
  -q
```

Expected: PASS.

**Step 6: Commit**

```bash
git add tests/ui/test_console_api.py src/fruitfly/ui/console_api.py
git commit -m "fix: invalidate stale initial brain-view artifacts"
```

### Task 2: Make initial and replay responses fully contract-parity compliant

**Files:**
- Modify: `src/fruitfly/evaluation/runtime_activity_artifacts.py`
- Modify: `src/fruitfly/ui/console_api.py`
- Test: `tests/ui/test_console_api.py`
- Test: `tests/ui/test_console_replay_api.py`

**Step 1: Write the failing replay parity test**

Add a test that asserts replay responses also expose:

- `artifact_contract_version`
- `artifact_origin`

and that `artifact_origin == "replay-live-step"`.

```python
assert brain_payload["artifact_contract_version"] == RUNTIME_ACTIVITY_ARTIFACT_VERSION
assert brain_payload["artifact_origin"] == "replay-live-step"
```

**Step 2: Run the replay test to verify it fails**

Run:

```bash
PYTHONPATH=src ./.venv-flywire/bin/python -m pytest tests/ui/test_console_replay_api.py::test_console_api_exposes_replay_seek_and_step_synchronized_payloads -q
```

Expected: FAIL because replay payloads currently do not include `artifact_contract_version` or `artifact_origin`.

**Step 3: Add provenance fields to both initial and replay payloads**

In `src/fruitfly/evaluation/runtime_activity_artifacts.py`:

- ensure builder output always includes `artifact_contract_version`
- add optional `artifact_origin` parameter to `_build_brain_view_payload_for_step(...)`
- set:
  - `artifact_origin="initial-materialized"` in `materialize_runtime_activity_artifacts(...)`
  - `artifact_origin="replay-live-step"` in `build_replay_brain_view_payload(...)`

Minimal shape:

```python
payload["artifact_contract_version"] = RUNTIME_ACTIVITY_ARTIFACT_VERSION
payload["artifact_origin"] = artifact_origin
```

In `src/fruitfly/ui/console_api.py`, keep `payload.setdefault(...)` only as a fallback, not as the primary source for these fields.

**Step 4: Extend initial-path contract assertions**

In `tests/ui/test_console_api.py`, extend the existing recorded-payload tests to assert:

```python
assert brain_payload["artifact_contract_version"] == RUNTIME_ACTIVITY_ARTIFACT_VERSION
assert brain_payload["artifact_origin"] == "initial-materialized"
```

**Step 5: Run the focused backend test set**

Run:

```bash
PYTHONPATH=src ./.venv-flywire/bin/python -m pytest \
  tests/ui/test_console_api.py \
  tests/ui/test_console_replay_api.py \
  -q
```

Expected: PASS.

**Step 6: Commit**

```bash
git add src/fruitfly/evaluation/runtime_activity_artifacts.py src/fruitfly/ui/console_api.py tests/ui/test_console_api.py tests/ui/test_console_replay_api.py
git commit -m "feat: expose brain-view provenance markers"
```

### Task 3: Surface provenance in the right-side console panel

**Files:**
- Modify: `apps/neural-console/src/types/console.ts`
- Modify: `apps/neural-console/src/components/experiment-console-page.tsx`
- Modify: `apps/neural-console/src/lib/messages.ts`
- Test: `apps/neural-console/src/components/experiment-console-page.test.tsx`
- Test: `apps/neural-console/src/lib/console-api.test.ts`

**Step 1: Write the failing UI test**

Add a test that renders `ExperimentConsolePage` with:

- `artifact_contract_version: 1`
- `artifact_origin: "replay-live-step"`
- `validation_passed: true`

Assert the right-side panel shows a short provenance line such as:

`Formal neuropil truth · contract v1 · replay-live-step`

```tsx
expect(screen.getByText(/formal neuropil truth/i)).toBeInTheDocument()
expect(screen.getByText(/contract v1/i)).toBeInTheDocument()
expect(screen.getByText(/replay-live-step/i)).toBeInTheDocument()
```

**Step 2: Run the UI test to verify it fails**

Run:

```bash
pnpm --dir apps/neural-console exec vitest run src/components/experiment-console-page.test.tsx
```

Expected: FAIL because the page does not currently render a provenance metric row.

**Step 3: Extend the frontend payload types**

In `apps/neural-console/src/types/console.ts`, add:

```ts
artifact_contract_version?: number
artifact_origin?: 'initial-materialized' | 'replay-live-step'
```

to `BrainViewPayload`.

**Step 4: Render a provenance row in the brain details panel**

In `apps/neural-console/src/components/experiment-console-page.tsx`, add a formatter:

```ts
function formatBrainViewProvenance(brainView: BrainViewPayload, unavailableLabel: string) {
  if (
    brainView.artifact_contract_version == null ||
    brainView.artifact_origin == null ||
    brainView.validation_passed !== true
  ) {
    return unavailableLabel
  }
  return `Formal neuropil truth · contract v${brainView.artifact_contract_version} · ${brainView.artifact_origin}`
}
```

Render it as a `MetricRow` near coverage / shell metadata.

**Step 5: Add message keys if needed and update console client tests**

If you introduce a label key such as `experiment.brain.metric.provenance`, add it in `apps/neural-console/src/lib/messages.ts`, then extend `console-api.test.ts` to assert the fetched payload retains the new fields.

**Step 6: Run the frontend test set**

Run:

```bash
pnpm --dir apps/neural-console exec vitest run \
  src/lib/console-api.test.ts \
  src/components/experiment-console-page.test.tsx
```

Expected: PASS.

**Step 7: Commit**

```bash
git add apps/neural-console/src/types/console.ts apps/neural-console/src/components/experiment-console-page.tsx apps/neural-console/src/lib/messages.ts apps/neural-console/src/components/experiment-console-page.test.tsx apps/neural-console/src/lib/console-api.test.ts
git commit -m "feat: show brain-view provenance in console"
```

### Task 4: Run end-to-end verification and document residual limits

**Files:**
- Modify: `README.md`
- Test: `tests/ui/test_console_api.py`
- Test: `tests/ui/test_console_replay_api.py`
- Test: `apps/neural-console/src/App.test.tsx`

**Step 1: Add a short README note about initial/replay parity**

Append a concise paragraph in `README.md` clarifying:

- `brain_view.json` is a materialized cache artifact
- stale or out-of-contract artifacts are automatically regenerated
- initial and replay responses share the same formal neuropil contract

**Step 2: Add one integration-style assertion to the app shell test**

Extend `apps/neural-console/src/App.test.tsx` to include provenance-bearing `brainView` payloads in the mocked API responses and assert the page renders without falling back.

**Step 3: Run the complete verification set**

Run:

```bash
PYTHONPATH=src ./.venv-flywire/bin/python -m pytest \
  tests/ui/test_console_api.py \
  tests/ui/test_console_replay_api.py \
  -q

pnpm --dir apps/neural-console exec vitest run \
  src/lib/console-api.test.ts \
  src/components/experiment-console-page.test.tsx \
  src/App.test.tsx

pnpm --dir apps/neural-console build
```

Expected:

- pytest passes
- vitest passes
- build passes, allowing existing non-fatal Vite chunk warnings

**Step 4: Commit**

```bash
git add README.md tests/ui/test_console_api.py tests/ui/test_console_replay_api.py apps/neural-console/src/lib/console-api.test.ts apps/neural-console/src/components/experiment-console-page.test.tsx apps/neural-console/src/App.test.tsx
git commit -m "docs: clarify unified brain-view cache contract"
```

### Task 5: Final review before merge

**Files:**
- Review only: `src/fruitfly/evaluation/runtime_activity_artifacts.py`
- Review only: `src/fruitfly/ui/console_api.py`
- Review only: `apps/neural-console/src/components/experiment-console-page.tsx`

**Step 1: Run diff-focused review**

Inspect the final diff and confirm:

- no `roi_mapped_nodes` usage remains in live brain-view code
- no replay response omits provenance markers
- no initial response can bypass freshness invalidation

Run:

```bash
git diff --stat HEAD~4..HEAD
git diff HEAD~4..HEAD -- src/fruitfly/evaluation/runtime_activity_artifacts.py src/fruitfly/ui/console_api.py apps/neural-console/src/components/experiment-console-page.tsx
```

**Step 2: Request code review**

Use the repo’s review workflow before merge. The review must focus on:

- stale-cache invalidation correctness
- initial/replay contract parity
- UI provenance clarity

**Step 3: Merge or hand off**

If all checks pass, merge using the repo’s normal integration workflow. If not, capture the exact failing test or review finding before any further edits.
