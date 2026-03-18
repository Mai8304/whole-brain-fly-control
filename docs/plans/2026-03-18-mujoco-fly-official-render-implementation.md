# MuJoCo Fly Official Render Page Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a new `/mujoco-fly-official-render` page that shows strict-official `MuJoCo render（MuJoCo 原生渲染）` output from the authoritative Python `flybody（果蝇身体环境）` runtime, without changing the existing `/mujoco-fly` route.

**Architecture:** Keep the authoritative runtime entirely in Python. Reuse the mature repository pattern already present in `replay_renderer.py`: step the official `walk_imitation()` environment in Python, call `physics.render(...)`, and return encoded frames to the browser. The new browser page becomes a thin official-render observer with lifecycle controls and camera preset selection.

**Tech Stack:** Python, `flybody`, `dm_control`, `MuJoCo`, FastAPI, React, TypeScript, Vite, Vitest.

---

### Task 1: Define the official render runtime contract

**Files:**
- Create: `src/fruitfly/ui/mujoco_fly_official_render_contract.py`
- Create: `tests/ui/test_mujoco_fly_official_render_contract.py`

**Goal:** Freeze the API contract for the new official render route before implementing the runtime.

**Step 1: Write the failing test**

Add tests that assert:
- session payload includes:
  - `available`
  - `running_state`
  - `current_camera`
  - `checkpoint_loaded`
  - `reason`
- frame request contract includes:
  - `width`
  - `height`
  - `camera`
- invalid camera preset is rejected

**Step 2: Run test to verify it fails**

Run:
```bash
PYTHONPATH=src ./.venv-flywire/bin/python -m pytest \
  tests/ui/test_mujoco_fly_official_render_contract.py -q
```

Expected: FAIL because the contract module does not exist yet.

**Step 3: Write minimal implementation**

Implement:
- contract dataclasses or validators
- camera preset validation helper
- payload serialization helpers

**Step 4: Run test to verify it passes**

Run the same command and confirm PASS.

**Step 5: Commit**

```bash
git add \
  src/fruitfly/ui/mujoco_fly_official_render_contract.py \
  tests/ui/test_mujoco_fly_official_render_contract.py
git commit -m "feat: add mujoco fly official render contract"
```

---

### Task 2: Add the strict-official render runtime

**Files:**
- Create: `src/fruitfly/ui/mujoco_fly_official_render_runtime.py`
- Create: `tests/ui/test_mujoco_fly_official_render_runtime.py`

**Goal:** Stand up an authoritative local runtime that owns:
- `walk_imitation()`
- official checkpoint loading
- official stepping
- `physics.render(...)`

**Step 1: Write the failing test**

Add tests that assert:
- runtime initializes in unavailable state when the official checkpoint is missing
- runtime exposes lifecycle methods:
  - `start`
  - `pause`
  - `reset`
  - `set_camera_preset`
- runtime can render a frame through an injected renderer seam
- runtime rejects unsupported camera presets

**Step 2: Run test to verify it fails**

Run:
```bash
PYTHONPATH=src ./.venv-flywire/bin/python -m pytest \
  tests/ui/test_mujoco_fly_official_render_runtime.py -q
```

Expected: FAIL because the runtime module does not exist yet.

**Step 3: Write minimal implementation**

Implement a runtime object that:
- resolves the official scene and checkpoint paths
- initializes `walk_imitation()`
- stays `unavailable` when checkpoint loading is not possible
- exposes lifecycle state
- delegates rendering to the official `physics.render(...)` path or a test seam

**Step 4: Run test to verify it passes**

Run the same command and confirm PASS.

**Step 5: Commit**

```bash
git add \
  src/fruitfly/ui/mujoco_fly_official_render_runtime.py \
  tests/ui/test_mujoco_fly_official_render_runtime.py
git commit -m "feat: add mujoco fly official render runtime"
```

---

### Task 3: Expose official render API endpoints

**Files:**
- Modify: `src/fruitfly/ui/console_api.py`
- Modify: `src/fruitfly/ui/mujoco_fly_runtime.py` only if route coexistence needs shared helpers
- Modify: `scripts/serve_neural_console_api.py`
- Modify: `tests/ui/test_console_api.py`

**Goal:** Add a dedicated API surface for `/mujoco-fly-official-render`.

**Step 1: Write the failing test**

Extend API tests to cover:
- `GET /api/mujoco-fly-official-render/session`
- `GET /api/mujoco-fly-official-render/frame`
- `POST /api/mujoco-fly-official-render/start`
- `POST /api/mujoco-fly-official-render/pause`
- `POST /api/mujoco-fly-official-render/reset`
- `POST /api/mujoco-fly-official-render/camera`

Assert:
- unavailable status when checkpoint is missing
- frame endpoint returns image bytes only when runtime is available
- camera endpoint rejects invalid presets

**Step 2: Run test to verify it fails**

Run:
```bash
PYTHONPATH=src ./.venv-flywire/bin/python -m pytest \
  tests/ui/test_console_api.py -q
```

Expected: FAIL on missing routes or mismatched payloads.

**Step 3: Write minimal implementation**

Add:
- runtime bootstrap wiring in `console_api.py`
- explicit route handlers for the official render page
- new CLI options in `serve_neural_console_api.py` if separate scene/checkpoint flags are needed

**Step 4: Run test to verify it passes**

Run the same command and confirm PASS.

**Step 5: Commit**

```bash
git add \
  src/fruitfly/ui/console_api.py \
  scripts/serve_neural_console_api.py \
  tests/ui/test_console_api.py
git commit -m "feat: expose mujoco fly official render api"
```

---

### Task 4: Add the new front-end route and page shell

**Files:**
- Modify: `apps/neural-console/src/App.tsx`
- Create: `apps/neural-console/src/pages/mujoco-fly-official-render/mujoco-fly-official-render-page.tsx`
- Create: `apps/neural-console/src/pages/mujoco-fly-official-render/mujoco-fly-official-render-page.test.tsx`
- Modify: `apps/neural-console/src/App.test.tsx`
- Modify: `apps/neural-console/src/lib/messages.ts`

**Goal:** Add a dedicated page route without changing `/mujoco-fly`.

**Step 1: Write the failing test**

Add tests that assert:
- `readPageFromLocation()` recognizes `/mujoco-fly-official-render`
- the new page renders its title and controls
- the existing `/mujoco-fly` route remains unchanged

**Step 2: Run test to verify it fails**

Run:
```bash
pnpm --dir apps/neural-console exec vitest run \
  src/pages/mujoco-fly-official-render/mujoco-fly-official-render-page.test.tsx \
  src/App.test.tsx
```

Expected: FAIL because the route and page do not exist yet.

**Step 3: Write minimal implementation**

Implement:
- new route switch in `App.tsx`
- page shell with:
  - title
  - large render viewport
  - `Start / Pause / Reset`
  - camera preset controls
  - runtime status display

**Step 4: Run test to verify it passes**

Run the same command and confirm PASS.

**Step 5: Commit**

```bash
git add \
  apps/neural-console/src/App.tsx \
  apps/neural-console/src/App.test.tsx \
  apps/neural-console/src/lib/messages.ts \
  apps/neural-console/src/pages/mujoco-fly-official-render/mujoco-fly-official-render-page.tsx \
  apps/neural-console/src/pages/mujoco-fly-official-render/mujoco-fly-official-render-page.test.tsx
git commit -m "feat: add mujoco fly official render route"
```

---

### Task 5: Add the official render client and frame surface

**Files:**
- Create: `apps/neural-console/src/pages/mujoco-fly-official-render/lib/mujoco-fly-official-render-client.ts`
- Create: `apps/neural-console/src/pages/mujoco-fly-official-render/lib/mujoco-fly-official-render-client.test.ts`
- Create: `apps/neural-console/src/pages/mujoco-fly-official-render/components/mujoco-fly-official-render-viewport.tsx`
- Create: `apps/neural-console/src/pages/mujoco-fly-official-render/components/mujoco-fly-official-render-viewport.test.tsx`

**Goal:** Make the page consume official runtime status and render frames, without using Babylon as the primary renderer.

**Step 1: Write the failing test**

Add tests that assert:
- client boots from `session` endpoint
- frame URL generation includes:
  - `width`
  - `height`
  - `camera`
  - cache-busting key if needed
- controls call the official render API
- unavailable responses disable frame rendering and surface the reason

**Step 2: Run test to verify it fails**

Run:
```bash
pnpm --dir apps/neural-console exec vitest run \
  src/pages/mujoco-fly-official-render/lib/mujoco-fly-official-render-client.test.ts \
  src/pages/mujoco-fly-official-render/components/mujoco-fly-official-render-viewport.test.tsx
```

Expected: FAIL because the client and viewport do not exist yet.

**Step 3: Write minimal implementation**

Implement:
- a client that talks to the official render endpoints
- a viewport component that displays the current frame as the primary surface
- camera preset selection wired to the API
- strict unavailable state rendering

**Step 4: Run test to verify it passes**

Run the same command and confirm PASS.

**Step 5: Commit**

```bash
git add \
  apps/neural-console/src/pages/mujoco-fly-official-render/lib/mujoco-fly-official-render-client.ts \
  apps/neural-console/src/pages/mujoco-fly-official-render/lib/mujoco-fly-official-render-client.test.ts \
  apps/neural-console/src/pages/mujoco-fly-official-render/components/mujoco-fly-official-render-viewport.tsx \
  apps/neural-console/src/pages/mujoco-fly-official-render/components/mujoco-fly-official-render-viewport.test.tsx
git commit -m "feat: add official render page client and viewport"
```

---

### Task 6: Add strict unavailable handling and preserve `/mujoco-fly`

**Files:**
- Modify: `apps/neural-console/src/pages/mujoco-fly-official-render/mujoco-fly-official-render-page.tsx`
- Modify: `apps/neural-console/src/lib/messages.ts`
- Modify tests accordingly

**Goal:** Ensure the new page fails closed and does not blur into the existing Babylon route.

**Step 1: Write the failing test**

Add tests that assert:
- missing checkpoint shows unavailable state
- invalid camera preset shows error or rejected state
- `/mujoco-fly` route continues to use its current viewer implementation

**Step 2: Run test to verify it fails**

Run:
```bash
pnpm --dir apps/neural-console exec vitest run \
  src/pages/mujoco-fly-official-render/**/*.test.ts \
  src/pages/mujoco-fly-official-render/**/*.test.tsx \
  src/App.test.tsx
```

Expected: FAIL on missing unavailable behavior or route isolation regressions.

**Step 3: Write minimal implementation**

Implement:
- explicit unavailable copy
- disabled controls for unavailable runtime
- route isolation so existing `/mujoco-fly` semantics are unchanged

**Step 4: Run test to verify it passes**

Run the same command and confirm PASS.

**Step 5: Commit**

```bash
git add \
  apps/neural-console/src/pages/mujoco-fly-official-render/mujoco-fly-official-render-page.tsx \
  apps/neural-console/src/lib/messages.ts \
  apps/neural-console/src/pages/mujoco-fly-official-render/**/*.test.ts \
  apps/neural-console/src/pages/mujoco-fly-official-render/**/*.test.tsx \
  apps/neural-console/src/App.test.tsx
git commit -m "fix: fail closed on official render page"
```

---

### Task 7: Verification and manual smoke

**Commands:**

- Python tests:
```bash
PYTHONPATH=src ./.venv-flywire/bin/python -m pytest \
  tests/ui/test_mujoco_fly_official_render_contract.py \
  tests/ui/test_mujoco_fly_official_render_runtime.py \
  tests/ui/test_console_api.py \
  -q
```

- Front-end tests:
```bash
pnpm --dir apps/neural-console exec vitest run \
  src/pages/mujoco-fly-official-render/**/*.test.ts \
  src/pages/mujoco-fly-official-render/**/*.test.tsx \
  src/App.test.tsx
```

- Build:
```bash
pnpm --dir apps/neural-console build
```

- Manual smoke:
  - start the local API with official render runtime flags
  - open `/mujoco-fly-official-render`
  - verify the page shows the official render surface
  - verify `Start / Pause / Reset`
  - verify camera preset switching changes the rendered frame source
  - verify missing checkpoint produces `unavailable`
  - verify `/mujoco-fly` still behaves exactly as before

**Commit:** `chore: verify mujoco fly official render page`

---

## Delivery Notes

This plan intentionally keeps `/mujoco-fly` untouched. The new page is the strict-official render route; the earlier Babylon route remains a separate concern and must not be silently redefined by this work.
