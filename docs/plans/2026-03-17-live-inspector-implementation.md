# Live Inspector Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build an in-console `live inspector（实时观察器）` for the Fruitfly body panel that supports real `live / replay / artifact（实时 / 回放 / 归档）` workflows while preserving the existing `flybody（果蝇身体与 MuJoCo 环境） + MuJoCo（物理仿真引擎）` truth path.

**Architecture:** Add a backend inspector runtime that owns session state, current camera state, replay trace recording, and frame streaming. Extend the existing FastAPI console API with inspector endpoints, then replace the current body video player UI with a single-column viewport-first inspector surface whose behavior summary sits below the viewport.

**Tech Stack:** Python 3.11+, FastAPI, NumPy `NPZ（压缩数组归档）`, existing `fruitfly.ui` backend, existing `flybody` rollout entrypoint, React 19, TypeScript, Vite, Vitest, Testing Library.

---

### Task 1: Add replay trace serialization for inspector sessions

**Files:**
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/inspector_trace.py`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/__init__.py`
- Test: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_inspector_trace.py`

**Step 1: Write the failing test**

```python
from pathlib import Path

import numpy as np

from fruitfly.evaluation.inspector_trace import dump_inspector_trace, load_inspector_trace


def test_dump_and_load_inspector_trace_round_trips_arrays(tmp_path: Path) -> None:
    trace_dir = tmp_path / "trace"
    dump_inspector_trace(
        output_dir=trace_dir,
        session_metadata={"session_id": "sess-1", "task": "straight_walking"},
        arrays={
            "step_id": np.asarray([0, 1], dtype=np.int64),
            "sim_time": np.asarray([0.0, 0.1], dtype=np.float64),
            "qpos": np.asarray([[0.0, 1.0], [2.0, 3.0]], dtype=np.float64),
        },
        events=[{"step_id": 1, "event_type": "camera_change", "label": "hero"}],
    )

    payload = load_inspector_trace(trace_dir)

    assert payload.session["session_id"] == "sess-1"
    assert payload.arrays["qpos"].shape == (2, 2)
    assert payload.events[0]["event_type"] == "camera_change"
```

**Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_inspector_trace.py -q
```

Expected: FAIL with `ModuleNotFoundError` or missing symbol errors for `inspector_trace`.

**Step 3: Write minimal implementation**

Implement:

- a small `InspectorTracePayload` container
- `dump_inspector_trace(output_dir, session_metadata, arrays, events)`
- `load_inspector_trace(output_dir)`
- on-disk files:
  - `session.json`
  - `state_traces.npz`
  - `events.jsonl`

Keep the first version intentionally small and filesystem-only.

**Step 4: Run test to verify it passes**

Run:

```bash
python3 -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_inspector_trace.py -q
```

Expected: PASS

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/inspector_trace.py /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/__init__.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_inspector_trace.py
git commit -m "feat: add inspector replay trace contract"
```

### Task 2: Record replay traces from the closed-loop rollout entrypoint

**Files:**
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/scripts/eval_flybody_closed_loop.py`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/scripts/test_eval_flybody_closed_loop.py`
- Reference: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/inspector_trace.py`

**Step 1: Write the failing test**

Add a script test that asserts a rollout can emit replay artifacts:

```python
def test_eval_flybody_closed_loop_cli_writes_replay_trace(tmp_path, monkeypatch, capsys) -> None:
    from scripts import eval_flybody_closed_loop

    # monkeypatch fake env and fake policy exactly like the existing smoke test
    exit_code = eval_flybody_closed_loop.main(
        [
            "--checkpoint", str(tmp_path / "epoch_0001.pt"),
            "--compiled-graph-dir", str(tmp_path / "compiled"),
            "--task", "straight_walking",
            "--max-steps", "4",
            "--output-dir", str(tmp_path / "eval"),
            "--save-replay-trace",
        ]
    )

    assert exit_code == 0
    assert (tmp_path / "eval" / "session.json").exists()
    assert (tmp_path / "eval" / "state_traces.npz").exists()
    assert (tmp_path / "eval" / "events.jsonl").exists()
```

**Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/scripts/test_eval_flybody_closed_loop.py -q
```

Expected: FAIL because `--save-replay-trace` and trace outputs do not exist yet.

**Step 3: Write minimal implementation**

Update `/Users/zhuangwei/Downloads/coding/Fruitfly/scripts/eval_flybody_closed_loop.py` to:

- collect per-step `qpos`, `qvel`, `ctrl`, `reward`, `forward_velocity`, and `body_upright`
- add `--save-replay-trace`
- write replay artifacts beside `summary.json`
- add trace paths into the emitted summary payload when traces exist

Keep the recording logic behind a small helper instead of inlining all serialization in the CLI.

**Step 4: Run test to verify it passes**

Run:

```bash
python3 -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/scripts/test_eval_flybody_closed_loop.py -q
```

Expected: PASS

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/scripts/eval_flybody_closed_loop.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/scripts/test_eval_flybody_closed_loop.py
git commit -m "feat: record replay traces for flybody rollout"
```

### Task 3: Add backend inspector session runtime and FastAPI routes

**Files:**
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/ui/inspector_runtime.py`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/ui/console_api.py`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/ui/__init__.py`
- Test: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_console_inspector_api.py`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_console_api.py`

**Step 1: Write the failing test**

Create an API test that drives a fake in-memory inspector runtime:

```python
def test_console_api_exposes_inspector_session_routes(tmp_path: Path) -> None:
    from fruitfly.ui import ConsoleApiConfig, create_console_api

    app = create_console_api(
        ConsoleApiConfig(
            compiled_graph_dir=tmp_path / "compiled",
            eval_dir=tmp_path / "eval",
            checkpoint_path=tmp_path / "epoch_0001.pt",
        )
    )
    client = TestClient(app)

    create_response = client.post(
        "/api/console/inspector/sessions",
        json={"mode": "live", "quality": "balanced", "camera": "hero"},
    )

    assert create_response.status_code == 200
    payload = create_response.json()
    assert payload["mode"] == "live"
    assert payload["camera"] == "hero"
```

Also add assertions for:

- `POST /control`
- `POST /camera`
- `GET /frame`
- `GET /summary`

**Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_console_inspector_api.py -q
```

Expected: FAIL because the inspector runtime and routes do not exist yet.

**Step 3: Write minimal implementation**

Implement:

- an in-memory `InspectorRuntimeRegistry`
- a lightweight `InspectorSessionState`
- session creation and lookup
- `start / pause / resume / stop / seek`
- camera updates for `hero / side / back / bottom / free`
- `GET /frame` returning `image/jpeg`
- `GET /summary` returning current body metrics

Keep Phase 1 simple:

- one active live session
- fake stepping hooks can be injectable for tests
- no multi-user or background job system

**Step 4: Run test to verify it passes**

Run:

```bash
python3 -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_console_inspector_api.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_console_api.py -q
```

Expected: PASS

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/ui/inspector_runtime.py /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/ui/console_api.py /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/ui/__init__.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_console_inspector_api.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_console_api.py
git commit -m "feat: add live inspector api runtime"
```

### Task 4: Add front-end inspector contracts and data hooks

**Files:**
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/types/console.ts`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/lib/inspector-api.ts`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/hooks/use-inspector-session.ts`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/lib/console-api.ts`
- Test: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/lib/inspector-api.test.ts`

**Step 1: Write the failing test**

Add a front-end API test:

```ts
import { describe, expect, it, vi } from 'vitest'

import { createInspectorSession } from './inspector-api'

describe('inspector api', () => {
  it('creates a live inspector session and resolves frame url', async () => {
    vi.stubGlobal('fetch', vi.fn(async () => new Response(JSON.stringify({
      session_id: 'sess-1',
      mode: 'live',
      status: 'idle',
      camera: 'hero',
      quality: 'balanced',
      current_step: 0,
      max_steps: 64,
    }))))

    const payload = await createInspectorSession({ mode: 'live', quality: 'balanced', camera: 'hero' })
    expect(payload.session_id).toBe('sess-1')
  })
})
```

**Step 2: Run test to verify it fails**

Run:

```bash
pnpm --dir /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console test -- --run src/lib/inspector-api.test.ts
```

Expected: FAIL because `inspector-api.ts` does not exist yet.

**Step 3: Write minimal implementation**

Add:

- new inspector payload types in `console.ts`
- `createInspectorSession`, `controlInspectorSession`, `updateInspectorCamera`
- a `useInspectorSession` hook that tracks:
  - session metadata
  - frame URL
  - current summary
  - `live / replay` mode
  - unavailable state

Keep the first hook fetch-driven and simple. Avoid optimizing with unnecessary memoization.

**Step 4: Run test to verify it passes**

Run:

```bash
pnpm --dir /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console test -- --run src/lib/inspector-api.test.ts
```

Expected: PASS

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/types/console.ts /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/lib/inspector-api.ts /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/hooks/use-inspector-session.ts /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/lib/console-api.ts /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/lib/inspector-api.test.ts
git commit -m "feat: add frontend inspector api contract"
```

### Task 5: Replace the body video player with the approved viewport-first inspector layout

**Files:**
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/experiment-console-page.tsx`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/experiment-console-page.test.tsx`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/index.css`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/lib/messages.ts`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/App.test.tsx`

**Step 1: Write the failing test**

Extend the body layout test so it asserts the approved structure:

```tsx
it('renders a viewport-first body inspector with summary below the viewport', () => {
  render(/* existing ExperimentConsolePage harness */)

  const bodyCard = screen.getByTestId('experiment-body-card')
  expect(bodyCard.querySelector('[data-testid="body-inspector-toolbar"]')).toBeInTheDocument()
  expect(bodyCard.querySelector('[data-testid="body-inspector-viewport"]')).toBeInTheDocument()
  expect(bodyCard.querySelector('[data-testid="body-inspector-summary"]')).toBeInTheDocument()
  expect(bodyCard.querySelector('.console-status-strip')).not.toBeInTheDocument()
})
```

Also update app-level tests to stop expecting a raw `<video title="Fly rollout video">` element.

**Step 2: Run test to verify it fails**

Run:

```bash
pnpm --dir /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console test -- --run src/components/experiment-console-page.test.tsx src/App.test.tsx
```

Expected: FAIL because the body panel still renders the old video-first structure.

**Step 3: Write minimal implementation**

Refactor the body card to:

- remove the old status strip
- remove the `xl:grid-cols-[minmax(0,1fr)_320px]` body-area split
- introduce an inspector toolbar
- render a dominant `body-inspector-viewport`
- place `Behavior Summary` directly below the viewport
- keep unavailable states explicit and text-only when no real inspector session exists

CSS rules:

- one continuous body surface
- no nested `stage / shell / frame` styling
- respect source frame aspect ratio
- leave the viewport as large as possible

**Step 4: Run test to verify it passes**

Run:

```bash
pnpm --dir /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console test -- --run src/components/experiment-console-page.test.tsx src/App.test.tsx
```

Expected: PASS

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/experiment-console-page.tsx /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/experiment-console-page.test.tsx /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/index.css /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/lib/messages.ts /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/App.test.tsx
git commit -m "feat: replace body video with live inspector layout"
```

### Task 6: Wire live and replay controls into the console data flow

**Files:**
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/hooks/use-console-data.ts`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/data/mockConsoleData.ts`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/experiment-console-page.tsx`
- Test: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/hooks/use-console-data.test.ts`
- Test: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/experiment-console-page.test.tsx`

**Step 1: Write the failing test**

Add a hook test that verifies the console state surfaces inspector availability:

```ts
it('maps live inspector payloads into console state', async () => {
  // mock session, summary, and frame route responses
  const state = await loadConsoleState()
  expect(state.inspector.mode).toBe('live')
  expect(state.inspector.summary.steps_completed).toBe(12)
})
```

**Step 2: Run test to verify it fails**

Run:

```bash
pnpm --dir /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console test -- --run src/hooks/use-console-data.test.ts src/components/experiment-console-page.test.tsx
```

Expected: FAIL because the console state does not yet expose inspector data.

**Step 3: Write minimal implementation**

Update the console data layer to:

- fetch inspector availability from the new backend endpoints
- populate initial toolbar state
- pass inspector props into `ExperimentConsolePage`
- preserve strict unavailable states when the inspector API is missing
- keep mock fallback disabled unless explicitly enabled by environment flag

**Step 4: Run test to verify it passes**

Run:

```bash
pnpm --dir /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console test -- --run src/hooks/use-console-data.test.ts src/components/experiment-console-page.test.tsx
```

Expected: PASS

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/hooks/use-console-data.ts /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/data/mockConsoleData.ts /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/experiment-console-page.tsx /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/hooks/use-console-data.test.ts /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/experiment-console-page.test.tsx
git commit -m "feat: wire inspector into console state"
```

### Task 7: Run end-to-end verification for backend and frontend

**Files:**
- Reference: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_inspector_trace.py`
- Reference: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/scripts/test_eval_flybody_closed_loop.py`
- Reference: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_console_api.py`
- Reference: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_console_inspector_api.py`
- Reference: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/experiment-console-page.test.tsx`
- Reference: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/App.test.tsx`

**Step 1: Run the backend test slice**

Run:

```bash
python3 -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_inspector_trace.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/scripts/test_eval_flybody_closed_loop.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_console_api.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_console_inspector_api.py -q
```

Expected: PASS

**Step 2: Run the frontend test slice**

Run:

```bash
pnpm --dir /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console test -- --run src/components/experiment-console-page.test.tsx src/App.test.tsx src/lib/inspector-api.test.ts src/hooks/use-console-data.test.ts
```

Expected: PASS

**Step 3: Run the front-end build**

Run:

```bash
pnpm --dir /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console build
```

Expected: PASS

**Step 4: Manual smoke check**

Run the local console backend and verify:

- the body area is single-column
- the old gray status strip is gone
- the viewport dominates the body panel
- `Behavior Summary` sits below the viewport
- switching `hero / side / back` changes the rendered body perspective

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/docs/plans/2026-03-17-live-inspector-design.md /Users/zhuangwei/Downloads/coding/Fruitfly/docs/plans/2026-03-17-live-inspector-implementation.md
git commit -m "docs: add live inspector plan"
```
