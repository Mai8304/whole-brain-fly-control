# Live Inspector Replay Phase 1A Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a `replay-first（回放优先）` inspector for the Fruitfly experiment console so a real closed-loop rollout can be replayed step-by-step with synchronized body, brain, summary, and timeline views.

**Architecture:** Extend the current evaluation artifact pipeline so closed-loop eval writes a clean replay contract: `session.json + state_traces.npz + neural_traces.npz + events.jsonl`. Add a backend replay runtime that owns one global shared step cursor and renders MuJoCo frames on demand from saved state, then upgrade the experiment console body panel into a replay inspector surface that drives both body and brain views from that shared step.

**Tech Stack:** Python 3.11+, NumPy `NPZ（压缩数组归档）`, FastAPI, existing `fruitfly.evaluation` and `fruitfly.ui` packages, React 19, TypeScript, Vite, Vitest, Testing Library, `shadcn/ui（组件体系）`, `lucide-react`.

---

### Task 1: Replace transitional activity artifacts with the formal replay contract

**Files:**
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/inspector_trace.py`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/__init__.py`
- Test: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_inspector_trace.py`

**Step 1: Write the failing test**

Add a test that expects the new replay artifact set:

```python
from pathlib import Path

import numpy as np

from fruitfly.evaluation.inspector_trace import dump_replay_trace, load_replay_trace


def test_dump_and_load_replay_trace_round_trips_session_state_and_neural_arrays(tmp_path: Path) -> None:
    trace_dir = tmp_path / "trace"
    dump_replay_trace(
        output_dir=trace_dir,
        session={
            "session_id": "sess-1",
            "task": "straight_walking",
            "default_camera": "follow",
            "steps_completed": 2,
        },
        state_arrays={
            "step_id": np.asarray([0, 1], dtype=np.int64),
            "qpos": np.asarray([[0.0, 1.0], [2.0, 3.0]], dtype=np.float64),
        },
        neural_arrays={
            "step_id": np.asarray([0, 1], dtype=np.int64),
            "node_activity": np.asarray([[0.1, 0.2], [0.3, 0.4]], dtype=np.float32),
        },
        events=[{"step_id": 1, "event_type": "rollout_completed"}],
    )

    payload = load_replay_trace(trace_dir)

    assert payload.session["default_camera"] == "follow"
    assert payload.state_arrays["qpos"].shape == (2, 2)
    assert payload.neural_arrays["node_activity"].shape == (2, 2)
    assert payload.events[0]["event_type"] == "rollout_completed"
```

**Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_inspector_trace.py -q
```

Expected: FAIL because `dump_replay_trace` / `load_replay_trace` and `neural_traces.npz` do not exist yet.

**Step 3: Write minimal implementation**

Implement:

- `dump_replay_trace(...)`
- `load_replay_trace(...)`
- `ReplayTracePayload`

On-disk contract:

- `session.json`
- `state_traces.npz`
- `neural_traces.npz`
- `events.jsonl`

Keep the module small, filesystem-only, and explicit about schema.

**Step 4: Run test to verify it passes**

Run:

```bash
python3 -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_inspector_trace.py -q
```

Expected: PASS

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/inspector_trace.py /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/__init__.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_inspector_trace.py
git commit -m "feat: add replay trace artifact contract"
```

### Task 2: Write replay trace artifacts from closed-loop evaluation

**Files:**
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/scripts/eval_flybody_closed_loop.py`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/policy_wrapper.py`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/neural_activity.py`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/scripts/test_eval_flybody_closed_loop.py`
- Reference: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/inspector_trace.py`

**Step 1: Write the failing test**

Add a script test that expects the new replay artifact set after a rollout:

```python
def test_eval_flybody_closed_loop_writes_replay_trace_artifacts(tmp_path, monkeypatch) -> None:
    from scripts import eval_flybody_closed_loop

    exit_code = eval_flybody_closed_loop.main(
        [
            "--checkpoint", str(tmp_path / "epoch_0001.pt"),
            "--compiled-graph-dir", str(tmp_path / "compiled"),
            "--task", "straight_walking",
            "--max-steps", "4",
            "--output-dir", str(tmp_path / "eval"),
            "--save-video",
        ]
    )

    assert exit_code == 0
    assert (tmp_path / "eval" / "session.json").exists()
    assert (tmp_path / "eval" / "state_traces.npz").exists()
    assert (tmp_path / "eval" / "neural_traces.npz").exists()
    assert (tmp_path / "eval" / "events.jsonl").exists()
```

**Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/scripts/test_eval_flybody_closed_loop.py -q
```

Expected: FAIL because the CLI still emits transitional activity artifacts only.

**Step 3: Write minimal implementation**

Update the eval script so it:

- records per-step physical state arrays
- records per-step `node_activity[T, N]`
- computes `afferent / intrinsic / efferent` summaries
- emits `session.json`
- replaces transitional reliance on `activity_trace.json` / `final_node_activity.npy` for replay semantics
- keeps `summary.json` and `rollout.mp4` for artifact compatibility

Use the new `inspector_trace.py` helper for serialization.

**Step 4: Run test to verify it passes**

Run:

```bash
python3 -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/scripts/test_eval_flybody_closed_loop.py -q
```

Expected: PASS

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/scripts/eval_flybody_closed_loop.py /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/policy_wrapper.py /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/neural_activity.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/scripts/test_eval_flybody_closed_loop.py
git commit -m "feat: record replay-first inspector artifacts"
```

### Task 3: Add a replay runtime with a global shared step cursor

**Files:**
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/ui/replay_runtime.py`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/ui/__init__.py`
- Test: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_replay_runtime.py`

**Step 1: Write the failing test**

Create a test for the runtime contract:

```python
def test_replay_runtime_uses_one_shared_step_cursor_for_body_brain_and_summary(tmp_path: Path) -> None:
    runtime = ReplayRuntime.from_eval_dir(tmp_path)

    runtime.seek(3)

    assert runtime.current_step == 3
    assert runtime.current_summary()["step_id"] == 3
    assert runtime.current_brain_payload()["step_id"] == 3
```

Also assert:

- `prev_step()` / `next_step()`
- `play()` / `pause()`
- `set_speed()`
- `set_camera()`

**Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_replay_runtime.py -q
```

Expected: FAIL because `ReplayRuntime` does not exist yet.

**Step 3: Write minimal implementation**

Implement:

- `ReplayRuntime.from_eval_dir(...)`
- one global `current_step`
- `status = paused | playing`
- `speed`
- `camera_preset`
- helpers:
  - `seek(step)`
  - `prev_step()`
  - `next_step()`
  - `current_summary()`
  - `current_brain_payload()`

Do not implement live sessions here. This runtime is replay-only.

**Step 4: Run test to verify it passes**

Run:

```bash
python3 -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_replay_runtime.py -q
```

Expected: PASS

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/ui/replay_runtime.py /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/ui/__init__.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_replay_runtime.py
git commit -m "feat: add replay runtime with shared step cursor"
```

### Task 4: Add step-synchronized replay API routes and dynamic brain aggregation

**Files:**
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/ui/console_api.py`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/runtime_activity_artifacts.py`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_console_api.py`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_console_replay_api.py`

**Step 1: Write the failing test**

Add API tests for replay endpoints:

```python
def test_console_api_exposes_replay_seek_and_step_synchronized_payloads(tmp_path: Path) -> None:
    app = create_console_api(
        ConsoleApiConfig(
            compiled_graph_dir=tmp_path / "compiled",
            eval_dir=tmp_path / "eval",
            checkpoint_path=tmp_path / "epoch_0001.pt",
        )
    )
    client = TestClient(app)

    seek_response = client.post("/api/console/replay/seek", json={"step": 2})
    assert seek_response.status_code == 200
    assert seek_response.json()["current_step"] == 2

    brain_response = client.get("/api/console/replay/brain-view")
    summary_response = client.get("/api/console/replay/summary")

    assert brain_response.json()["step_id"] == 2
    assert summary_response.json()["step_id"] == 2
```

Also add assertions for:

- `GET /api/console/replay/session`
- `POST /api/console/replay/control`
- `POST /api/console/replay/camera`
- `GET /api/console/replay/timeline`

**Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_console_replay_api.py -q
```

Expected: FAIL because the replay API does not exist yet.

**Step 3: Write minimal implementation**

Add replay-only routes to `console_api.py` that:

- load `ReplayRuntime`
- expose `session`
- expose shared step `seek`
- expose `summary` at current step
- expose `timeline` with current step
- expose `brain-view` generated dynamically from `node_activity[t] + node_neuropil_occupancy`

Keep existing non-replay endpoints intact for current homepage compatibility.

**Step 4: Run test to verify it passes**

Run:

```bash
python3 -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_console_replay_api.py -q
```

Expected: PASS

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/ui/console_api.py /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/runtime_activity_artifacts.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_console_api.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_console_replay_api.py
git commit -m "feat: add replay inspector api"
```

### Task 5: Add on-demand body frame rendering with fixed camera presets

**Files:**
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/replay_renderer.py`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/ui/replay_runtime.py`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_replay_renderer.py`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_replay_runtime.py`

**Step 1: Write the failing test**

Create a test that expects renderer output to vary by preset while keeping the same step:

```python
def test_replay_renderer_renders_same_step_from_different_presets(tmp_path: Path) -> None:
    renderer = ReplayRenderer.from_eval_dir(tmp_path)

    side_frame = renderer.render_frame(step=4, camera="side")
    top_frame = renderer.render_frame(step=4, camera="top")

    assert side_frame.content_type == "image/jpeg"
    assert top_frame.content_type == "image/jpeg"
    assert side_frame.bytes != top_frame.bytes
```

**Step 2: Run test to verify it fails**

Run:

```bash
python3 -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_replay_renderer.py -q
```

Expected: FAIL because `ReplayRenderer` does not exist.

**Step 3: Write minimal implementation**

Implement:

- `follow`
- `side`
- `top`
- `front-quarter`
- `reset view`

Rules:

- render from saved MuJoCo state
- camera target stays on fly body center
- no free camera in Phase 1A

Expose a replay frame endpoint via the runtime after the renderer works.

**Step 4: Run test to verify it passes**

Run:

```bash
python3 -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_replay_renderer.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_replay_runtime.py -q
```

Expected: PASS

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/replay_renderer.py /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/ui/replay_runtime.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_replay_renderer.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_replay_runtime.py
git commit -m "feat: add replay body renderer and camera presets"
```

### Task 6: Upgrade the experiment console body panel into a replay inspector surface

**Files:**
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/experiment-console-page.tsx`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/lib/console-api.ts`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/hooks/use-console-data.ts`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/lib/messages.ts`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/body-replay-inspector.tsx`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/replay-timeline.tsx`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/definition-hint.tsx`
- Test: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/experiment-console-page.test.tsx`
- Test: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/body-replay-inspector.test.tsx`

**Step 1: Write the failing test**

Add UI tests that assert:

- replay controls render
- changing step updates body and brain sections from one shared source
- camera preset selector exists
- body panel no longer behaves like a plain video player in replay mode

Example:

```tsx
it("keeps body and brain in sync through one replay step cursor", async () => {
  render(<ExperimentConsolePage />);

  await user.click(screen.getByRole("button", { name: /next step/i }));

  expect(screen.getByText(/step 1 \/ 64/i)).toBeInTheDocument();
  expect(screen.getByTestId("brain-step")).toHaveTextContent("1");
  expect(screen.getByTestId("body-step")).toHaveTextContent("1");
});
```

**Step 2: Run test to verify it fails**

Run:

```bash
zsh -lic 'cd /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console && pnpm test --run'
```

Expected: FAIL because the replay inspector UI does not exist yet.

**Step 3: Write minimal implementation**

Implement:

- one shared replay store at the experiment page level
- body replay toolbar:
  - play/pause
  - prev/next step
  - step slider
  - step counter
  - speed select
  - camera preset select
  - reset view
- dual-focus layout:
  - brain top-right
  - body bottom-right
  - timeline promoted as shared component

Use `shadcn/ui` and existing design tokens only.

**Step 4: Run test to verify it passes**

Run:

```bash
zsh -lic 'cd /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console && pnpm test --run'
```

Expected: PASS

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/experiment-console-page.tsx /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/lib/console-api.ts /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/hooks/use-console-data.ts /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/lib/messages.ts /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/body-replay-inspector.tsx /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/replay-timeline.tsx /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/definition-hint.tsx /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/experiment-console-page.test.tsx /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/body-replay-inspector.test.tsx
git commit -m "feat: add replay-first body inspector ui"
```

### Task 7: Verify end-to-end replay behavior and update docs

**Files:**
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/README.md`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/AGENTS.md`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/docs/plans/2026-03-17-live-inspector-design.md`
- Reference: `/Users/zhuangwei/Downloads/coding/Fruitfly/docs/plans/2026-03-17-live-inspector-replay-phase1a-design.md`

**Step 1: Write the failing verification checklist**

Create a short manual verification checklist in the docs that requires:

- replay session starts from a real eval directory
- body frame changes when camera preset changes at the same step
- brain and body stay on the same shared step
- missing replay artifacts surface `unavailable`, not fake fallback

**Step 2: Run full verification before docs claim success**

Run:

```bash
python3 -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_inspector_trace.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/scripts/test_eval_flybody_closed_loop.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_replay_runtime.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_console_replay_api.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_console_api.py -q
zsh -lic 'cd /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console && pnpm test --run && pnpm build'
```

Expected:

- all Python tests PASS
- all front-end tests PASS
- `pnpm build` PASS

**Step 3: Update docs**

Update repo docs so they clearly state:

- Phase 1A is replay-first
- `rollout.mp4` is artifact, not primary inspector truth
- replay truth lives in `session/state/neural/events`

**Step 4: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/README.md /Users/zhuangwei/Downloads/coding/Fruitfly/AGENTS.md /Users/zhuangwei/Downloads/coding/Fruitfly/docs/plans/2026-03-17-live-inspector-design.md /Users/zhuangwei/Downloads/coding/Fruitfly/docs/plans/2026-03-17-live-inspector-replay-phase1a-design.md
git commit -m "docs: define replay-first live inspector phase 1a"
```
