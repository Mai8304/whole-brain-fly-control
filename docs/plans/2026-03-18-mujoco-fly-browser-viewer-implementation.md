# MuJoCo Fly Browser Viewer Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a new `/mujoco-fly-browser-viewer` route that renders a Babylon 3D scene driven by the authoritative official `flybody（果蝇身体环境）` runtime through bootstrap data and a streamed `body pose（刚体位姿）` contract, without modifying the behavior of `/mujoco-fly` or `/mujoco-fly-official-render`.

**Architecture:** Keep strict official runtime ownership in Python. Add a browser-viewer adapter layer that exposes a bootstrap payload, a session payload, and a streamed body-pose payload. On the front-end, Babylon builds a scene graph keyed by `body_name` and updates transforms from the official stream.

**Tech Stack:** Python, `flybody`, `dm_control`, `MuJoCo`, FastAPI, WebSocket, React, TypeScript, Vite, Vitest, Babylon.js.

---

### Task 1: Define the browser-viewer contracts

**Files:**
- Create: `src/fruitfly/ui/mujoco_fly_browser_viewer_contract.py`
- Create: `tests/ui/test_mujoco_fly_browser_viewer_contract.py`

**Goal:** Freeze the new page's payload schema before implementation.

**Step 1: Write failing contract tests**

Add tests for:
- valid bootstrap payload
- valid session payload
- valid pose stream payload
- rejection of index-only body payloads
- rejection of malformed quaternions

**Step 2: Implement the minimal validators**

Define validation helpers for:
- bootstrap payload
- session payload
- pose stream payload

**Step 3: Run focused tests**

Run:
```bash
PYTHONPATH=src ./.venv-flywire/bin/python -m pytest \
  tests/ui/test_mujoco_fly_browser_viewer_contract.py -q
```

**Step 4: Commit**

```bash
git add src/fruitfly/ui/mujoco_fly_browser_viewer_contract.py tests/ui/test_mujoco_fly_browser_viewer_contract.py
git commit -m "feat: add mujoco fly browser viewer contract"
```

---

### Task 2: Add the official runtime browser-viewer adapter

**Files:**
- Create: `src/fruitfly/ui/mujoco_fly_browser_viewer_runtime.py`
- Create: `tests/ui/test_mujoco_fly_browser_viewer_runtime.py`
- Reuse reference code from:
  - `src/fruitfly/ui/mujoco_fly_official_render_runtime.py`
  - `src/fruitfly/ui/mujoco_fly_official_render_backend.py`

**Goal:** Expose official runtime state as bootstrap + streamed body poses instead of rendered JPEG frames.

**Step 1: Write failing runtime tests**

Cover:
- bootstrap payload generation
- session payload generation
- emitted `body_poses` keyed by `body_name`
- unavailable state when official checkpoint is absent

**Step 2: Implement runtime adapter**

The adapter must:
- create the official `walk_imitation()` runtime
- load the official checkpoint
- expose `start`, `pause`, `reset`
- extract `body_name -> xpos/xquat`
- produce viewer-ready payloads

**Step 3: Run focused runtime tests**

Run:
```bash
PYTHONPATH=src ./.venv-flywire/bin/python -m pytest \
  tests/ui/test_mujoco_fly_browser_viewer_runtime.py -q
```

**Step 4: Commit**

```bash
git add src/fruitfly/ui/mujoco_fly_browser_viewer_runtime.py tests/ui/test_mujoco_fly_browser_viewer_runtime.py
git commit -m "feat: add mujoco fly browser viewer runtime"
```

---

### Task 3: Add bootstrap, session, and stream API endpoints

**Files:**
- Modify: `src/fruitfly/ui/console_api.py`
- Modify: `tests/ui/test_console_api.py`

**Goal:** Publish the new browser-viewer API surface without changing existing routes.

**Required endpoints:**
- `GET /api/mujoco-fly-browser-viewer/bootstrap`
- `GET /api/mujoco-fly-browser-viewer/session`
- `WS /api/mujoco-fly-browser-viewer/stream`
- `POST /api/mujoco-fly-browser-viewer/start`
- `POST /api/mujoco-fly-browser-viewer/pause`
- `POST /api/mujoco-fly-browser-viewer/reset`

**Step 1: Add failing API tests**

Verify:
- bootstrap endpoint payload
- session endpoint payload
- control endpoint transitions
- stream endpoint payload frames
- strict unavailable behavior

**Step 2: Implement endpoints**

Wire the new runtime into FastAPI.

**Step 3: Run API tests**

Run:
```bash
PYTHONPATH=src ./.venv-flywire/bin/python -m pytest \
  tests/ui/test_console_api.py -q
```

**Step 4: Commit**

```bash
git add src/fruitfly/ui/console_api.py tests/ui/test_console_api.py
git commit -m "feat: add mujoco fly browser viewer api"
```

---

### Task 4: Materialize bootstrap scene metadata for the browser

**Files:**
- Modify: `scripts/export_official_walk_imitation_scene.py`
- Modify: `tests/scripts/test_export_official_walk_imitation_scene.py`
- Update output bundle under: `apps/neural-console/public/mujoco-fly/flybody-official-walk/`

**Goal:** Extend the official scene export so the new viewer can bootstrap scene graph structure from official data.

**Step 1: Add failing exporter tests**

Verify output includes:
- `entry_xml`
- `scene_version`
- `body_manifest`
- `geom_manifest`

**Step 2: Implement mechanical export metadata**

Generate metadata from official exported scene structure.

**Step 3: Re-export the bundle**

Run the exporter and refresh the checked-in scene bundle.

**Step 4: Run exporter tests**

Run:
```bash
PYTHONPATH=src ./.venv-flywire/bin/python -m pytest \
  tests/scripts/test_export_official_walk_imitation_scene.py -q
```

**Step 5: Commit**

```bash
git add scripts/export_official_walk_imitation_scene.py tests/scripts/test_export_official_walk_imitation_scene.py apps/neural-console/public/mujoco-fly/flybody-official-walk/
git commit -m "feat: export browser viewer bootstrap metadata"
```

---

### Task 5: Add a dedicated front-end route and viewer client

**Files:**
- Modify: `apps/neural-console/src/App.tsx`
- Create: `apps/neural-console/src/pages/mujoco-fly-browser-viewer/mujoco-fly-browser-viewer-page.tsx`
- Create: `apps/neural-console/src/pages/mujoco-fly-browser-viewer/lib/mujoco-fly-browser-viewer-client.ts`
- Create tests under:
  - `apps/neural-console/src/pages/mujoco-fly-browser-viewer/**/*.test.ts`
  - `apps/neural-console/src/pages/mujoco-fly-browser-viewer/**/*.test.tsx`

**Goal:** Add a new route without changing existing page semantics.

**Step 1: Add failing route tests**

Verify:
- `/mujoco-fly-browser-viewer` resolves
- existing `/mujoco-fly` still resolves unchanged
- existing `/mujoco-fly-official-render` still resolves unchanged

**Step 2: Add the new viewer client**

Client responsibilities:
- fetch bootstrap
- fetch session
- connect WebSocket stream
- call `start/pause/reset`

**Step 3: Add page shell**

The new page should show:
- large Babylon viewport
- start/pause/reset controls
- local view-reset and local view presets
- strict unavailable state

**Step 4: Run front-end tests**

Run:
```bash
pnpm --dir apps/neural-console exec vitest run \
  src/pages/mujoco-fly-browser-viewer/**/*.test.ts \
  src/pages/mujoco-fly-browser-viewer/**/*.test.tsx \
  src/App.test.tsx
```

**Step 5: Commit**

```bash
git add apps/neural-console/src/App.tsx apps/neural-console/src/pages/mujoco-fly-browser-viewer/
git commit -m "feat: add mujoco fly browser viewer route"
```

---

### Task 6: Add Babylon scene graph and body-name sync

**Files:**
- Create: `apps/neural-console/src/pages/mujoco-fly-browser-viewer/lib/babylon-scene.ts`
- Create: `apps/neural-console/src/pages/mujoco-fly-browser-viewer/lib/mesh-sync.ts`
- Create: `apps/neural-console/src/pages/mujoco-fly-browser-viewer/components/mujoco-fly-browser-viewer-viewport.tsx`
- Add tests for scene mapping and update behavior

**Goal:** Render the official scene in Babylon and update it using `body_name` keyed pose payloads.

**Step 1: Add failing tests**

Verify:
- body nodes are created from `body_manifest`
- mesh attachments follow `geom_manifest`
- pose updates are keyed by `body_name`
- missing names fail visibly

**Step 2: Implement scene graph assembly**

Build:
- one `TransformNode` per body
- mesh attachments per geom
- local transform application from `geom_manifest`

**Step 3: Implement pose sync**

Per streamed payload:
- lookup by `body_name`
- update Babylon position
- update Babylon quaternion

**Step 4: Run focused tests**

Run:
```bash
pnpm --dir apps/neural-console exec vitest run \
  src/pages/mujoco-fly-browser-viewer/lib/*.test.ts \
  src/pages/mujoco-fly-browser-viewer/components/*.test.tsx
```

**Step 5: Commit**

```bash
git add apps/neural-console/src/pages/mujoco-fly-browser-viewer/lib/ apps/neural-console/src/pages/mujoco-fly-browser-viewer/components/
git commit -m "feat: add babylon scene sync for browser viewer"
```

---

### Task 7: Add strict unavailable handling and final verification

**Files:**
- Modify: `apps/neural-console/src/lib/messages.ts`
- Modify relevant browser-viewer tests

**Goal:** Ensure the new route never falls back to synthetic motion.

**Step 1: Add regression tests**

Verify unavailable states for:
- missing checkpoint
- invalid bootstrap payload
- invalid stream payload
- runtime initialization failure

**Step 2: Implement fail-closed UI**

Show explicit unavailable status instead of placeholder animation.

**Step 3: Run full verification**

Python:
```bash
PYTHONPATH=src ./.venv-flywire/bin/python -m pytest \
  tests/ui/test_mujoco_fly_browser_viewer_contract.py \
  tests/ui/test_mujoco_fly_browser_viewer_runtime.py \
  tests/ui/test_console_api.py \
  tests/scripts/test_export_official_walk_imitation_scene.py \
  -q
```

Front-end:
```bash
pnpm --dir apps/neural-console exec vitest run \
  src/pages/mujoco-fly-browser-viewer/**/*.test.ts \
  src/pages/mujoco-fly-browser-viewer/**/*.test.tsx \
  src/App.test.tsx
```

Build:
```bash
pnpm --dir apps/neural-console build
```

Manual smoke:
- open `/mujoco-fly-browser-viewer`
- verify drag / rotate / zoom
- verify `Start / Pause / Reset`
- verify body-pose-driven motion
- verify `/mujoco-fly` remains unchanged
- verify `/mujoco-fly-official-render` remains unchanged

**Step 4: Commit**

```bash
git add apps/neural-console/src/lib/messages.ts apps/neural-console/src/pages/mujoco-fly-browser-viewer/
git commit -m "fix: fail closed for browser viewer runtime"
```

---

## Delivery Notes

This plan intentionally treats the new route as additive. Existing MuJoCo fly routes must keep their current meanings and behavior. The new route must not introduce a local gait fallback or any non-official runtime authority.
