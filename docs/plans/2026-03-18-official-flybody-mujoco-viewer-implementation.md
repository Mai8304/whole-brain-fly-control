# Official Flybody MuJoCo Viewer Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the browser-authoritative `/mujoco-fly` runtime with a strict-official viewer architecture: Python `flybody（果蝇身体环境）` owns the walking runtime, exported official scene assets define the viewer scene, and the browser `Babylon.js（三维引擎）` page consumes a streamed `body pose（刚体位姿）` contract.

**Architecture:** Keep strict official ownership boundaries. `walk_imitation()` and the official policy / checkpoint live in Python. The browser route remains `/mujoco-fly`, but becomes a state-driven viewer instead of an authoritative gait/runtime host.

**Tech Stack:** Python, `flybody`, `dm_control`, `MuJoCo`, FastAPI, WebSocket, React, TypeScript, Vite, Vitest, Babylon.js.

---

### Task 1: Add an official walk-scene exporter

**Files:**
- Create: `scripts/export_official_walk_imitation_scene.py`
- Create: `tests/scripts/test_export_official_walk_imitation_scene.py`
- Create or update: `apps/neural-console/public/mujoco-fly/flybody-official-walk/`

**Goal:** Export the authoritative `walk_imitation()` scene with `dm_control.mjcf.export_with_assets()`.

**Steps:**
1. Write a focused script test that asserts:
   - the exporter instantiates `walk_imitation()`
   - it writes one XML file and referenced assets to an output directory
   - it produces a small `manifest.json` with `entry_xml` and `scene_version`
2. Implement the exporter so it:
   - creates the environment
   - forces scene initialization through the normal environment lifecycle
   - exports `env.task.root_entity.mjcf_model`
   - writes the asset bundle into `apps/neural-console/public/mujoco-fly/flybody-official-walk/`
3. Run the focused script test.
4. Materialize the checked-in official scene bundle.

**Commit:** `feat: export official flybody walk scene`

---

### Task 2: Add a strict-official local runtime service for `/mujoco-fly`

**Files:**
- Create: `src/fruitfly/ui/mujoco_fly_runtime.py`
- Create: `tests/ui/test_mujoco_fly_runtime.py`
- Modify: `src/fruitfly/ui/console_api.py`
- Modify: `tests/ui/test_console_api.py`

**Goal:** Stand up a local authoritative runtime that owns:
- `walk_imitation()`
- official action stepping
- viewer-state emission

**Steps:**
1. Define a runtime object that can:
   - initialize the official environment
   - load the official policy / checkpoint
   - `start`
   - `pause`
   - `reset`
   - return viewer-ready `body_poses`
2. Add focused tests for:
   - initial state
   - lifecycle state transitions
   - emitted payload shape
   - unavailable state when policy / checkpoint is missing
3. Expose HTTP control endpoints:
   - `POST /api/mujoco-fly/start`
   - `POST /api/mujoco-fly/pause`
   - `POST /api/mujoco-fly/reset`
4. Expose a WebSocket or equivalent state stream endpoint for viewer-state updates.

**Commit:** `feat: add official flybody runtime service`

---

### Task 3: Define and test the viewer-state contract

**Files:**
- Create: `src/fruitfly/ui/mujoco_fly_contract.py`
- Create: `tests/ui/test_mujoco_fly_contract.py`

**Goal:** Freeze the browser-facing state schema.

**Required contract fields:**
- `frame_id`
- `sim_time`
- `running_state`
- `scene_version`
- `body_poses[]`
  - `body_name`
  - `position`
  - `quaternion`

**Steps:**
1. Add schema helpers / validators for the formal payload.
2. Write tests that reject:
   - missing `body_name`
   - index-only payloads
   - malformed quaternions
3. Ensure the runtime service emits only viewer-ready state, not raw `qpos`.

**Commit:** `feat: add mujoco fly viewer state contract`

---

### Task 4: Convert `/mujoco-fly` from browser-authoritative runtime to viewer mode

**Files:**
- Modify: `apps/neural-console/src/pages/mujoco-fly/mujoco-fly-page.tsx`
- Modify: `apps/neural-console/src/pages/mujoco-fly/components/mujoco-fly-viewport.tsx`
- Replace or heavily modify: `apps/neural-console/src/pages/mujoco-fly/lib/mujoco-fly-runtime.ts`
- Create: `apps/neural-console/src/pages/mujoco-fly/lib/mujoco-fly-viewer-client.ts`
- Modify: `apps/neural-console/src/pages/mujoco-fly/*.test.tsx`

**Goal:** Make the page consume streamed official state instead of stepping its own authoritative gait/runtime.

**Steps:**
1. Remove the browser-side open-loop gait loop as the authoritative path.
2. Add a client for:
   - start/pause/reset control calls
   - viewer-state subscription
3. Keep `Babylon` scene, camera, drag, rotate, zoom, and reset-camera behavior.
4. Update `body_name -> TransformNode` sync to consume streamed `body_poses`.
5. Add UI tests for:
   - loading
   - ready
   - unavailable
   - start/pause/reset control wiring

**Commit:** `refactor: make mujoco fly page runtime-driven`

---

### Task 5: Handle official scene identities and Babylon mesh mapping

**Files:**
- Create or modify: `apps/neural-console/src/pages/mujoco-fly/lib/body-manifest.ts`
- Create or modify: `apps/neural-console/src/pages/mujoco-fly/lib/mesh-sync.ts`
- Add tests under: `apps/neural-console/src/pages/mujoco-fly/lib/*.test.ts`

**Goal:** Ensure Babylon mapping is keyed by `body_name`, not export-order indices.

**Steps:**
1. Build a stable `body_name -> mesh/transform-node` manifest.
2. Ensure missing names fail visibly.
3. Reject index-only synchronization logic in tests.

**Commit:** `feat: key mujoco fly viewer sync by body name`

---

### Task 6: Add strict-official unavailable handling

**Files:**
- Modify: `apps/neural-console/src/pages/mujoco-fly/mujoco-fly-page.tsx`
- Modify: `apps/neural-console/src/lib/messages.ts`
- Modify tests accordingly

**Goal:** Prevent the page from silently pretending official walking is active when the official runtime chain is absent.

**Steps:**
1. Show an explicit unavailable state when:
   - official runtime is not running
   - official policy / checkpoint is unavailable
   - scene export bundle is missing
   - state-stream mapping is invalid
2. Ensure there is no fallback to browser-authored gait.
3. Add regression tests for all unavailable states.

**Commit:** `fix: fail closed when official mujoco fly runtime is unavailable`

---

### Task 7: Verification and final integration

**Commands:**
- Python tests:
```bash
PYTHONPATH=src ./.venv-flywire/bin/python -m pytest \
  tests/scripts/test_export_official_walk_imitation_scene.py \
  tests/ui/test_mujoco_fly_contract.py \
  tests/ui/test_mujoco_fly_runtime.py \
  tests/ui/test_console_api.py \
  -q
```

- Front-end tests:
```bash
pnpm --dir apps/neural-console exec vitest run \
  src/pages/mujoco-fly/**/*.test.ts \
  src/pages/mujoco-fly/**/*.test.tsx \
  src/App.test.tsx
```

- Build:
```bash
pnpm --dir apps/neural-console build
```

- Manual smoke:
  - export official scene bundle
  - start the local runtime service
  - open `/mujoco-fly`
  - verify camera interaction
  - verify start/pause/reset
  - verify body-pose-driven motion
  - verify unavailable state when the official runtime chain is absent

**Commit:** `chore: verify official mujoco fly viewer`

---

## Delivery Notes

This plan intentionally does not add a non-official gait fallback. If the official walking policy / checkpoint cannot be resolved, implementation must stop with an explicit unavailable state rather than substituting browser-authored control logic.
