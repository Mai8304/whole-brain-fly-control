# Replay Renderer Worker Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace per-frame replay subprocess launches with one resident replay renderer worker so timeline playback no longer spawns a new `Python.app` on every step.

**Architecture:** Keep FastAPI in the current environment, but introduce a long-lived `.venv-flybody` worker process that owns a single `ReplayRenderer`. The API sends render requests over stdio and returns the resulting JPEG bytes as the existing `/api/console/replay/frame` response.

**Tech Stack:** Python, FastAPI, subprocess stdio protocol, NumPy-based replay artifacts, flybody / MuJoCo renderer

---

### Task 1: Lock replay frame reuse behavior with a failing API test

**Files:**
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_console_replay_api.py`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/ui/console_api.py`

**Step 1: Write the failing test**

Add a test that:
- builds a small replay trace
- injects a fake resident renderer client factory
- requests `/api/console/replay/frame` twice with different current steps
- asserts the fake factory is called once
- asserts the fake client receives two render requests

**Step 2: Run test to verify it fails**

Run: `pytest tests/ui/test_console_replay_api.py -q -k resident`

Expected: FAIL because the API currently has no resident worker/client seam.

**Step 3: Write minimal implementation**

Add a worker-client factory seam to `create_console_api(...)` and route replay-frame requests through it.

**Step 4: Run test to verify it passes**

Run: `pytest tests/ui/test_console_replay_api.py -q -k resident`

Expected: PASS

### Task 2: Add a resident replay worker protocol and client

**Files:**
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/ui/replay_frame_worker.py`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_replay_frame_worker.py`

**Step 1: Write the failing test**

Add worker-client tests that:
- fake a worker subprocess using in-memory pipes or a stub `Popen`
- send a render request
- verify the client returns JPEG bytes
- verify a worker error becomes a Python exception

**Step 2: Run test to verify it fails**

Run: `pytest tests/ui/test_replay_frame_worker.py -q`

Expected: FAIL because the client module does not exist yet.

**Step 3: Write minimal implementation**

Create:
- a `ReplayFrameWorkerClient`
- JSON-line request / response-header protocol
- `render_frame(...)`
- `close()` and stale-worker recovery helpers

**Step 4: Run test to verify it passes**

Run: `pytest tests/ui/test_replay_frame_worker.py -q`

Expected: PASS

### Task 3: Add the resident worker entrypoint in the flybody environment

**Files:**
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/scripts/replay_frame_worker.py`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/scripts/render_replay_frame.py`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_replay_renderer.py`

**Step 1: Write the failing test**

Add a focused test for the new worker entrypoint parsing requests and reusing one renderer instance across multiple render commands.

**Step 2: Run test to verify it fails**

Run: `pytest tests/evaluation/test_replay_renderer.py -q -k worker`

Expected: FAIL because the worker entrypoint does not exist.

**Step 3: Write minimal implementation**

Implement a line-based worker loop that:
- loads one `ReplayRenderer.from_eval_dir(...)`
- reads JSON requests from stdin
- writes a JSON header and raw JPEG bytes to stdout

Keep `render_replay_frame.py` as a thin one-shot compatibility helper if still useful for manual debugging.

**Step 4: Run test to verify it passes**

Run: `pytest tests/evaluation/test_replay_renderer.py -q -k worker`

Expected: PASS

### Task 4: Wire API lifecycle management and verify end-to-end replay

**Files:**
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/ui/console_api.py`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_console_replay_api.py`

**Step 1: Write the failing test**

Add a test that simulates a broken worker, verifies the API returns `503`, then verifies a fresh client can be created on a later request.

**Step 2: Run test to verify it fails**

Run: `pytest tests/ui/test_console_replay_api.py -q -k worker`

Expected: FAIL because broken-worker recovery is not implemented.

**Step 3: Write minimal implementation**

Add:
- lazy client startup
- broken-client invalidation
- shutdown cleanup hook

**Step 4: Run test to verify it passes**

Run: `pytest tests/ui/test_console_replay_api.py -q -k worker`

Expected: PASS

### Task 5: Verify the replay path and document results

**Files:**
- Reference: `/Users/zhuangwei/Downloads/coding/Fruitfly/docs/plans/2026-03-17-replay-renderer-worker-design.md`
- Reference: `/Users/zhuangwei/Downloads/coding/Fruitfly/docs/plans/2026-03-17-replay-renderer-worker-implementation.md`

**Step 1: Run focused backend tests**

Run: `pytest tests/ui/test_replay_frame_worker.py tests/ui/test_console_replay_api.py tests/ui/test_replay_runtime.py tests/evaluation/test_replay_renderer.py -q`

Expected: PASS

**Step 2: Run browser/API verification**

Run the local console and confirm:
- playback no longer spawns a new Python process per frame
- `/api/console/replay/frame` still returns `image/jpeg`
- replay playback still advances body, brain, summary, and timeline together

**Step 3: Record outcome**

Capture the exact verification evidence in the final response.
