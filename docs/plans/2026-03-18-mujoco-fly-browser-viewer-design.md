# MuJoCo Fly Browser Viewer Design

**Goal:** Add a new browser-native `Babylon.js（三维引擎）` page that visualizes the authoritative `flybody（果蝇身体环境）` walking runtime through streamed official body poses, without modifying the existing `/mujoco-fly` or `/mujoco-fly-official-render` routes.

**Scope:** This design defines the strict-official `方案 B` architecture: official Python runtime ownership, browser bootstrap contract, streamed `body pose（刚体位姿）` contract, Babylon scene-graph responsibilities, control boundaries, and explicit non-goals.

**Relationship to existing plans:**
- [/Users/zhuangwei/Downloads/coding/Fruitfly/docs/plans/2026-03-17-mujoco-fly-page-design.md](/Users/zhuangwei/Downloads/coding/Fruitfly/docs/plans/2026-03-17-mujoco-fly-page-design.md)
- [/Users/zhuangwei/Downloads/coding/Fruitfly/docs/plans/2026-03-18-official-flybody-mujoco-viewer-design.md](/Users/zhuangwei/Downloads/coding/Fruitfly/docs/plans/2026-03-18-official-flybody-mujoco-viewer-design.md)
- [/Users/zhuangwei/Downloads/coding/Fruitfly/docs/plans/2026-03-18-mujoco-fly-official-render-design.md](/Users/zhuangwei/Downloads/coding/Fruitfly/docs/plans/2026-03-18-mujoco-fly-official-render-design.md)

---

## 1. Problem Statement

The repository now has two separate MuJoCo fly pages:

- `/mujoco-fly`
  - browser-authoritative `MuJoCo WASM（网页端 MuJoCo 运行时）` experiment page
  - good for local experimentation
  - not strict official runtime behavior

- `/mujoco-fly-official-render`
  - strict-official `physics.render(...)` observer
  - behavior and rendering both remain on the official Python runtime path
  - visually behaves like a render-feed page, not a browser-native 3D scene

The user-approved new requirement is a third page:

- browser-native 3D
- `Babylon.js` viewport with drag / rotate / zoom
- strict official runtime behavior
- no contamination of the two existing pages

This requires a new route whose browser view is driven by authoritative official state, not by browser-authored gait logic and not by frame images.

---

## 2. Approved Final Decision

The new page will follow:

```text
official flybody runtime（官方 flybody 运行时）
-> walk_imitation()（官方步行环境）
-> official policy / checkpoint（官方策略 / 权重）
-> env.step(action)（官方步进）
-> viewer bootstrap + body pose stream（启动包 + 刚体位姿流）
-> Babylon.js browser viewer（浏览器 3D 观察器）
```

The new page is:

- strict official for behavior and runtime truth
- browser-native for rendering and interaction
- separate from existing pages

The new page will not:

- redefine the walking scene in the browser
- generate gait locally
- use browser `MuJoCo WASM` as the authoritative walking runtime
- replace `/mujoco-fly`
- replace `/mujoco-fly-official-render`

---

## 3. New Route and Ownership Boundary

### 3.1 New route

The new viewer will use a dedicated route:

- `/mujoco-fly-browser-viewer`

This route is additive only.

### 3.2 Existing routes remain unchanged

- `/mujoco-fly`
  remains the browser-authoritative experiment page

- `/mujoco-fly-official-render`
  remains the strict-official render-feed observer

The new route must not reuse those page semantics or silently change their meaning.

### 3.3 Runtime ownership

The authoritative walking runtime remains in Python.

The browser owns only:

- Babylon scene construction
- local viewer camera interaction
- mesh attachment and transform updates
- UI controls that call the authoritative runtime

---

## 4. Official Runtime Contract

### 4.1 Authoritative source

The authoritative runtime must be based on:

- `flybody.fly_envs.walk_imitation()`
- official walking policy / checkpoint
- official `env.step(action)` loop
- official `MuJoCo` state

### 4.2 Runtime outputs

The runtime must produce two distinct outputs:

- low-frequency bootstrap identity
- high-frequency body pose stream

It must not expose browser-facing gait logic, synthetic motion, or non-official state reconstruction.

### 4.3 Behavior truth

Behavior truth remains:

- official action source
- official actuator application through `FruitFly.apply_action()`
- official physical stepping

The browser cannot become a second simulation authority.

---

## 5. Bootstrap Contract

The browser viewer needs a static scene identity payload at startup.

### 5.1 Required fields

- `scene_version`
- `runtime_mode`
- `entry_xml`
- `checkpoint_loaded`
- `default_camera`
- `camera_presets[]`
- `body_manifest[]`
- `geom_manifest[]`

### 5.2 `body_manifest`

Each body entry should include at minimum:

- `body_name`
- `parent_body_name`

`body_name` is the formal synchronization key.

### 5.3 `geom_manifest`

Each geom entry should include at minimum:

- `geom_name`
- `body_name`
- `mesh_asset`
- `local_position`
- `local_quaternion`

This manifest exists only to let Babylon construct scene graph attachments. It is not a behavior source-of-truth.

### 5.4 Source-of-truth rule

The authoritative source remains the official exported scene / runtime identity.

The bootstrap payload is a viewer-facing representation derived mechanically from official scene data.

---

## 6. Pose Stream Contract

The dynamic browser contract is a `body pose（刚体位姿）` stream.

### 6.1 Required fields

- `frame_id`
- `sim_time`
- `running_state`
- `current_camera`
- `scene_version`
- `body_poses[]`

Each `body_pose` must contain:

- `body_name`
- `position`
- `quaternion`

### 6.2 Why `body_name`

`body_name` must be the formal key because:

- export ordering can change
- index-only contracts are brittle
- Babylon node lookup needs a stable semantic identifier

### 6.3 Why not raw `qpos`

The browser should not consume raw `qpos` as its formal contract because that would force the Babylon page to reconstruct model semantics and kinematics.

Strict best practice requires:

- official runtime computes the world state
- browser consumes viewer-ready poses

---

## 7. Interface Shape

The new page should use three interface classes:

### 7.1 Bootstrap endpoint

- `GET /api/mujoco-fly-browser-viewer/bootstrap`

Used once to build the scene graph and mesh attachments.

### 7.2 Session endpoint

- `GET /api/mujoco-fly-browser-viewer/session`

Used for:

- availability
- running state
- current camera
- checkpoint-loaded state
- explicit unavailable reason

### 7.3 Pose stream endpoint

- `WS /api/mujoco-fly-browser-viewer/stream`

Used for continuous `body_poses`.

### 7.4 Control endpoints

- `POST /api/mujoco-fly-browser-viewer/start`
- `POST /api/mujoco-fly-browser-viewer/pause`
- `POST /api/mujoco-fly-browser-viewer/reset`

These must control only the authoritative runtime.

---

## 8. Babylon Viewer Contract

### 8.1 Scene responsibilities

Babylon is responsible for:

- engine / scene creation
- `ArcRotateCamera（环绕相机）`
- lights
- optional visual ground layer
- mesh loading
- scene graph assembly
- transform updates from streamed body poses

### 8.2 Scene graph structure

The viewer should have:

- one `TransformNode` per `body_name`
- geom meshes attached under the corresponding body node
- mesh local transforms sourced from `geom_manifest`

### 8.3 Update model

Per pose-stream frame:

- find node by `body_name`
- update `position`
- update `rotationQuaternion`

No browser-side gait, kinematic, or policy logic is allowed.

---

## 9. Interaction Boundary

Two interaction classes must remain separate.

### 9.1 Local viewer interaction

Handled purely in Babylon:

- drag
- rotate
- zoom
- reset viewer camera
- local view presets

These do not modify authoritative runtime behavior.

### 9.2 Runtime control interaction

Handled through official control endpoints:

- `Start`
- `Pause`
- `Reset`

These do modify the authoritative runtime.

### 9.3 Non-goal

The browser must not:

- synthesize running state
- synthesize gait
- mutate authoritative body poses
- turn local camera movement into runtime state mutation

---

## 10. Strict Unavailable Semantics

The new route must fail closed.

Unavailable conditions include:

- official checkpoint unavailable
- bootstrap contract invalid
- body-name mapping invalid
- stream payload invalid
- official runtime initialization failure

In those cases the page must show explicit unavailable state, not fallback motion.

---

## 11. Testing and Verification

### 11.1 Python-side tests

Validate:

- bootstrap payload shape
- session payload shape
- body pose stream payload shape
- unavailable behavior when official runtime chain is incomplete

### 11.2 Front-end tests

Validate:

- route loads
- Babylon viewer bootstraps from bootstrap payload
- body-name keyed transform updates
- start / pause / reset control wiring
- explicit unavailable state

### 11.3 Manual smoke

Manual verification must confirm:

- browser-native 3D viewport appears
- drag / rotate / zoom works
- start / pause / reset controls work
- pose stream updates visible motion
- unavailable state is explicit and strict when official runtime is absent

---

## 12. Summary

The new route is the browser-native strict-official viewer variant:

- official behavior stays in Python `flybody`
- browser rendering stays in Babylon
- bootstrap defines scene identity
- pose stream defines body motion
- existing `/mujoco-fly` and `/mujoco-fly-official-render` remain untouched
