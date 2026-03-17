# Neuropil Activity Mapping Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement the strict `neuropil activity mapping（神经纤维区活动映射）` contract so the backend and UI expose only one authoritative FlyWire-derived activity chain, with explicit provenance, strict failure semantics, and no fake single-neuropil assignment.

**Architecture:** Keep the formal truth path unchanged at the artifact level, then refactor the runtime and API contracts around it. Backend code should compute dual metrics and explicit multi-membership payloads from validated `node_neuropil_occupancy`, while the frontend should consume those fields without collapsing them back into legacy single-ROI semantics.

**Tech Stack:** Python 3.11+, FastAPI, NumPy, PyArrow, existing `fruitfly.evaluation` and `fruitfly.ui` modules, React 19, TypeScript, Vitest, Testing Library.

---

**Execution context:** Run this plan in a fresh worktree created from commit `166a630fa42a4a15061d132fd950939de657b1d1` so the current workspace's unrelated UI edits are not mixed into the implementation commits.

### Task 1: Tighten the backend brain-view contract to explicit neuropil semantics

**Files:**
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/brain_view_contract.py`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_brain_view_contract.py`
- Reference: `/Users/zhuangwei/Downloads/coding/Fruitfly/docs/plans/2026-03-17-neuropil-activity-mapping-design.md`

**Step 1: Write the failing test**

Replace the old region-centric assertions with a contract test like:

```python
def test_build_brain_view_payload_exposes_formal_neuropil_contract() -> None:
    payload = build_brain_view_payload(
        semantic_scope="neuropil",
        view_mode="grouped-neuropil-v1",
        mapping_mode="node_neuropil_occupancy",
        activity_metric="activity_mass",
        mapping_coverage={"neuropil_mapped_nodes": 2, "total_nodes": 4},
        formal_truth={
            "validation_passed": True,
            "graph_scope_validation_passed": True,
            "roster_alignment_passed": False,
        },
        region_activity=[
            {
                "neuropil_id": "AL",
                "display_name": "AL",
                "raw_activity_mass": 0.9,
                "signed_activity": -0.1,
                "covered_weight_sum": 1.0,
                "node_count": 2,
                "is_display_grouped": True,
            }
        ],
        top_nodes=[
            {
                "node_idx": 1,
                "source_id": "20",
                "activity_value": 0.6,
                "flow_role": "intrinsic",
                "neuropil_memberships": [
                    {"neuropil": "AL_L", "occupancy_fraction": 0.75, "synapse_count": 3}
                ],
                "display_group_hint": "AL",
            }
        ],
    )

    assert payload["mapping_mode"] == "node_neuropil_occupancy"
    assert payload["region_activity"][0]["neuropil_id"] == "AL"
    assert payload["top_nodes"][0]["neuropil_memberships"][0]["neuropil"] == "AL_L"
```

**Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_brain_view_contract.py -q
```

Expected: FAIL because `build_brain_view_payload(...)` does not yet accept or normalize the new contract fields.

**Step 3: Write minimal implementation**

Update `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/brain_view_contract.py` to:

- accept explicit top-level contract fields:
  - `semantic_scope`
  - `view_mode`
  - `mapping_mode`
  - `activity_metric`
  - `formal_truth`
- rename normalized region keys from legacy `roi_*` to neuropil-specific keys
- normalize `top_nodes[].neuropil_memberships`
- sort `top_regions` by `raw_activity_mass`

Keep the first implementation narrow and deterministic:

```python
normalized_regions = [
    {
        "neuropil_id": str(region["neuropil_id"]),
        "display_name": str(region["display_name"]),
        "raw_activity_mass": float(region["raw_activity_mass"]),
        "signed_activity": float(region["signed_activity"]),
        "covered_weight_sum": float(region["covered_weight_sum"]),
        "node_count": int(region["node_count"]),
        "is_display_grouped": bool(region["is_display_grouped"]),
    }
    for region in region_activity
]
```

**Step 4: Run test to verify it passes**

Run:

```bash
python3 -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_brain_view_contract.py -q
```

Expected: PASS

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/brain_view_contract.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_brain_view_contract.py
git commit -m "feat: tighten neuropil brain view contract"
```

### Task 2: Refactor runtime aggregation to emit dual metrics and multi-membership nodes

**Files:**
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/runtime_activity_artifacts.py`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_runtime_activity_artifacts.py`
- Reference: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/node_neuropil_occupancy.py`

**Step 1: Write the failing test**

Create a focused aggregation test that builds a tiny compiled graph in `tmp_path` and asserts:

```python
def test_build_replay_brain_view_payload_exposes_dual_metrics_and_memberships(tmp_path: Path) -> None:
    # write node_index.parquet and node_neuropil_occupancy.parquet into tmp_path / "compiled"
    payload = build_replay_brain_view_payload(
        compiled_graph_dir=compiled_dir,
        step_id=3,
        node_activity=np.asarray([0.2, -0.6], dtype=np.float32),
        afferent_activity=0.1,
        intrinsic_activity=0.2,
        efferent_activity=0.3,
    )

    assert payload["activity_metric"] == "activity_mass"
    assert payload["region_activity"][0]["raw_activity_mass"] > 0.0
    assert "signed_activity" in payload["region_activity"][0]
    assert payload["top_nodes"][0]["neuropil_memberships"][0]["occupancy_fraction"] == 0.75
```

Use occupancy rows that prove:
- one node contributes to two neuropils
- grouped display labels differ from underlying formal neuropil IDs
- `signed_activity` and `raw_activity_mass` produce different values

**Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_runtime_activity_artifacts.py -q
```

Expected: FAIL because the runtime payload still emits legacy `activity_value`, `roi_name`, and single-label top-node output.

**Step 3: Write minimal implementation**

Refactor `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/runtime_activity_artifacts.py` to:

- accumulate both:
  - `raw_activity_mass = sum(abs(activity) * occupancy_fraction)`
  - `signed_activity = sum(activity * occupancy_fraction)`
- accumulate `covered_weight_sum`
- build `top_nodes[].neuropil_memberships` from all occupancy rows for the node
- keep `display_group_hint` as a separate convenience field
- pass the normalized result through `build_brain_view_payload(...)` instead of hand-assembling a partially divergent dict

Keep the math explicit and avoid hidden normalization:

```python
raw_activity_mass[mapped_group] += abs(activity_value) * occupancy_fraction
signed_activity[mapped_group] += activity_value * occupancy_fraction
covered_weight_sum[mapped_group] += occupancy_fraction
memberships_by_node_idx[node_idx].append(...)
```

**Step 4: Run test to verify it passes**

Run:

```bash
python3 -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_runtime_activity_artifacts.py -q
```

Expected: PASS

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/runtime_activity_artifacts.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_runtime_activity_artifacts.py
git commit -m "feat: expose neuropil activity metrics and memberships"
```

### Task 3: Enforce strict formal-truth gating in the console API and replay endpoints

**Files:**
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/ui/console_api.py`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_console_api.py`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_console_replay_api.py`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/README.md`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/docs/sot/flywire-neuron-roster-sot.md`

**Step 1: Write the failing test**

Add two API tests:

```python
def test_console_api_returns_unavailable_brain_view_when_validation_is_missing(tmp_path: Path) -> None:
    # write activity_trace.json + final_node_activity.npy + occupancy parquet
    # omit neuropil_truth_validation.json
    response = client.get("/api/console/brain-view")
    payload = response.json()

    assert payload["data_status"] == "unavailable"
    assert payload["region_activity"] == []


def test_console_api_surfaces_formal_neuropil_provenance_fields(tmp_path: Path) -> None:
    response = client.get("/api/console/brain-view")
    payload = response.json()

    assert payload["mapping_mode"] == "node_neuropil_occupancy"
    assert payload["graph_scope_validation_passed"] is True
    assert payload["roster_alignment_passed"] is False
```

Mirror the same strictness in replay tests for `/api/console/replay/brain-view`.

**Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_console_api.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_console_replay_api.py -q
```

Expected: FAIL because the API currently materializes brain payloads without the full provenance contract and still allows older field shapes.

**Step 3: Write minimal implementation**

Update `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/ui/console_api.py` to:

- refuse formal neuropil activity when validation JSON is absent or not passed
- include top-level provenance fields in both recorded and unavailable payloads
- rename mapping coverage to `neuropil_mapped_nodes`
- ensure replay brain views use the same contract as recorded brain views

Then update the docs in:
- `/Users/zhuangwei/Downloads/coding/Fruitfly/README.md`
- `/Users/zhuangwei/Downloads/coding/Fruitfly/docs/sot/flywire-neuron-roster-sot.md`

Document three explicit facts:
- runtime activity requires validated `node_neuropil_occupancy`
- graph-scoped validation and proofread alignment are separate states
- grouped V1 display is a display transform, not raw truth

**Step 4: Run test to verify it passes**

Run:

```bash
python3 -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_console_api.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_console_replay_api.py -q
```

Expected: PASS

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/ui/console_api.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_console_api.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_console_replay_api.py /Users/zhuangwei/Downloads/coding/Fruitfly/README.md /Users/zhuangwei/Downloads/coding/Fruitfly/docs/sot/flywire-neuron-roster-sot.md
git commit -m "feat: gate console neuropil activity on validated truth"
```

### Task 4: Update the frontend data contract and API fixtures

**Files:**
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/types/console.ts`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/lib/console-api.test.ts`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/hooks/use-console-data.ts`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/data/mockConsoleData.ts`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/App.test.tsx`

**Step 1: Write the failing test**

Update `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/lib/console-api.test.ts` so the mocked brain payload includes the new contract:

```ts
const brainView = {
  semantic_scope: 'neuropil',
  view_mode: 'grouped-neuropil-v1',
  mapping_mode: 'node_neuropil_occupancy',
  activity_metric: 'activity_mass',
  mapping_coverage: { neuropil_mapped_nodes: 12, total_nodes: 42 },
  region_activity: [
    {
      neuropil_id: 'AL',
      display_name: 'AL',
      raw_activity_mass: 0.8,
      signed_activity: -0.2,
      covered_weight_sum: 1.0,
      node_count: 3,
      is_display_grouped: true,
    },
  ],
  top_nodes: [
    {
      node_idx: 5,
      source_id: '1005',
      activity_value: 0.7,
      flow_role: 'intrinsic',
      neuropil_memberships: [{ neuropil: 'AL_L', occupancy_fraction: 0.75, synapse_count: 3 }],
      display_group_hint: 'AL',
    },
  ],
}
```

Assert that the API helpers and default fallback values preserve this shape without dropping the new keys.

**Step 2: Run test to verify it fails**

Run:

```bash
pnpm --dir /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console exec vitest run src/lib/console-api.test.ts src/App.test.tsx
```

Expected: FAIL because the TypeScript interfaces and fallback objects still expect `roi_id`, `roi_name`, `activity_value`, and `roi_mapped_nodes`.

**Step 3: Write minimal implementation**

Update `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/types/console.ts` to add:

- `BrainNeuropilMembershipPayload`
- neuropil-specific `BrainRegionPayload`
- `mapping_mode`
- `activity_metric`
- `neuropil_mapped_nodes`
- `graph_scope_validation_passed`
- `roster_alignment_passed`

Then update the API fallback and fixture files so the app can boot with the new contract:

```ts
export interface BrainRegionPayload {
  neuropil_id: string
  display_name: string
  raw_activity_mass: number
  signed_activity: number
  covered_weight_sum: number
  node_count: number
  is_display_grouped: boolean
}
```

**Step 4: Run test to verify it passes**

Run:

```bash
pnpm --dir /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console exec vitest run src/lib/console-api.test.ts src/App.test.tsx
```

Expected: PASS

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/types/console.ts /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/lib/console-api.test.ts /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/hooks/use-console-data.ts /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/data/mockConsoleData.ts /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/App.test.tsx
git commit -m "feat: update console neuropil payload types"
```

### Task 5: Update the experiment console to display formal memberships without fake single labels

**Files:**
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/experiment-console-page.tsx`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/experiment-console-page.test.tsx`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/lib/messages.ts`

**Step 1: Write the failing test**

Update the component test to assert the rendered brain panel shows:

- grouped coverage using `neuropil_mapped_nodes`
- top-region lines based on `raw_activity_mass`
- top-node summaries that list memberships rather than a fake singular neuropil name

Use an assertion shape like:

```tsx
expect(screen.getByText(/AL_L 0.75/)).toBeInTheDocument()
expect(screen.getByText(/display group: AL/i)).toBeInTheDocument()
expect(screen.queryByText(/roi name/i)).not.toBeInTheDocument()
```

Also add labels for:
- `activity mass`
- `signed activity`
- `display grouping`

**Step 2: Run test to verify it fails**

Run:

```bash
pnpm --dir /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console exec vitest run src/components/experiment-console-page.test.tsx
```

Expected: FAIL because the component still reads legacy region fields and displays top nodes as `flow_role:node_idx`.

**Step 3: Write minimal implementation**

Update `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/experiment-console-page.tsx` to:

- render top neuropils using `region.display_name` and `raw_activity_mass`
- render coverage from `mapping_coverage.neuropil_mapped_nodes`
- render each top node as a compact membership summary, for example:

```ts
`${node.flow_role}:${node.node_idx} | ${node.neuropil_memberships
  .map((membership) => `${membership.neuropil} ${membership.occupancy_fraction.toFixed(2)}`)
  .join(', ')}`
```

- show `display_group_hint` only as a hint, not as the formal anatomical identity
- update message keys in `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/lib/messages.ts`

Keep the first UI pass factual and low-drama. Do not invent visual ranking or color semantics that are not present in the data.

**Step 4: Run test to verify it passes**

Run:

```bash
pnpm --dir /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console exec vitest run src/components/experiment-console-page.test.tsx
```

Expected: PASS

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/experiment-console-page.tsx /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/experiment-console-page.test.tsx /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/lib/messages.ts
git commit -m "feat: show neuropil memberships in experiment console"
```

### Task 6: Run focused regression verification before any broader rollout

**Files:**
- Reference only; no code changes in this task

**Step 1: Re-run focused Python contract tests**

Run:

```bash
python3 -m pytest \
  /Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_brain_view_contract.py \
  /Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_runtime_activity_artifacts.py \
  /Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_console_api.py \
  /Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_console_replay_api.py -q
```

Expected: PASS

**Step 2: Re-run focused frontend tests**

Run:

```bash
pnpm --dir /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console exec vitest run \
  src/lib/console-api.test.ts \
  src/components/experiment-console-page.test.tsx \
  src/App.test.tsx
```

Expected: PASS

**Step 3: Run one lightweight build verification**

Run:

```bash
pnpm --dir /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console build
```

Expected: PASS

**Step 4: Inspect git history and working tree**

Run:

```bash
git log --oneline -6
git status --short
```

Expected:
- one atomic commit per task
- no unrelated files included

**Step 5: Commit only if this task required follow-up fixes**

If the verification task required no code changes, do not create an extra commit.
If a fix was needed, create one small final commit with only the regression fix.
