# Official Flybody MuJoCo Viewer Design

**Goal:** Redefine `/mujoco-fly` so it strictly follows the official `flybody（果蝇身体环境）` runtime path: the authoritative walking simulation runs in Python with `flybody + dm_control + MuJoCo（物理仿真引擎）`, while the browser page becomes a `Babylon.js（三维引擎）` 3D viewer driven by streamed official state.

**Scope:** This design defines the strict-official architecture, authoritative runtime boundary, scene export path, state-bridge contract, viewer contract, and explicit non-goals for the final `/mujoco-fly` route. It supersedes the earlier assumption that browser-side `MuJoCo WASM（网页端 MuJoCo 运行时）` would remain the final authoritative runtime for this page.

**Relationship to existing plans:**
- [/Users/zhuangwei/Downloads/coding/Fruitfly/docs/plans/2026-03-17-mujoco-fly-page-design.md](/Users/zhuangwei/Downloads/coding/Fruitfly/docs/plans/2026-03-17-mujoco-fly-page-design.md)
- [/Users/zhuangwei/Downloads/coding/Fruitfly/docs/plans/2026-03-17-live-inspector-design.md](/Users/zhuangwei/Downloads/coding/Fruitfly/docs/plans/2026-03-17-live-inspector-design.md)

---

## 1. Problem Statement

The repository currently has a standalone `/mujoco-fly` page prototype that:

- uses `Babylon.js`
- uses browser-side `MuJoCo WASM`
- loads local `flybody` mesh assets
- drives motion with a local open-loop actuator script
- pins the root pose every step

This prototype is useful for proving browser rendering and interaction, but it is not the strict official `flybody` path for walking.

The strict official path must instead follow:

- `flybody.fly_envs.walk_imitation()` for the walking scene
- `FruitFly.apply_action()` for actuator semantics
- official `MuJoCo` stepping inside the Python runtime
- official walking policy / checkpoint as the action source

This means the browser must not remain the authoritative walking runtime.

---

## 2. Approved Final Decision

The final strict-official `/mujoco-fly` route will be:

- a browser `Babylon.js` page with a large interactive 3D viewport
- a viewer driven by a local Python `flybody` runtime
- controlled by minimal transport commands:
  - `start`
  - `pause`
  - `reset`
- synchronized from a streamed `body pose（刚体位姿）` state contract

The final strict-official page will not:

- generate gait locally in the browser
- treat browser `MuJoCo WASM` as the authoritative walking runtime
- use hand-authored `tripod gait（程序化三脚架步态）` control
- use `stabilizeRootPose()` or any equivalent root-pinning logic
- treat bare `fruitfly.xml` as the authoritative walking scene

---

## 3. Official Source-of-Truth Chain

The strict-official chain is:

```text
flybody.walk_imitation()
-> FruitFly + floors.Floor + WalkImitation
-> official walking policy / checkpoint
-> FruitFly.apply_action()
-> MuJoCo stepping in Python
-> viewer state bridge
-> Babylon.js viewer
```

Key implications:

- scene truth belongs to `walk_imitation()`
- ground truth belongs to `floors.Floor()`
- action truth belongs to the official walking policy / checkpoint
- browser truth is display truth, not simulation truth

---

## 4. Official Runtime Contract

### 4.1 Authoritative runtime

The authoritative walking runtime must live in Python, not in the browser.

It is responsible for:

- constructing `walk_imitation()`
- loading the official walking policy / checkpoint
- producing the official `action vector（动作向量）`
- stepping `MuJoCo`
- exposing viewer-ready state

### 4.2 Why browser `MuJoCo WASM` is no longer authoritative

The browser-side `MuJoCo WASM` prototype is not the strict official runtime because:

- `flybody` officially defines walking through Python `dm_control` tasks
- `InferenceWalkingTrajectoryLoader` provides reference trajectory data, not control outputs
- official materials do not define a browser-native walking policy deployment path

Therefore, browser `MuJoCo WASM` may remain useful for experimentation, but it is not the final strict-official architecture for `/mujoco-fly`.

---

## 5. Official Scene Contract

### 5.1 Scene construction

The final scene must come from `walk_imitation()`, not from a manually maintained standalone XML.

This implies:

- `FruitFly` walker instantiation is official
- `floors.Floor()` ground is official
- `WalkImitation` task additions are official
- arena attachment structure is official

### 5.2 Scene export

The exporter must use official `dm_control.mjcf.export_with_assets()`.

The exported artifact bundle should contain:

- one exported walking XML
- all referenced mesh / texture assets
- optional manifest metadata for page bootstrapping

The manifest is convenience metadata only. The exported XML remains the authoritative scene definition.

### 5.3 Ground semantics

Ground semantics must follow the official `floors.Floor()` scene:

- physical ground is a `plane geom（平面地面几何）`
- visual semantics are the official checker-floor material

The browser may render this through Babylon-friendly materials, but it must remain semantically tied to the exported official ground definition.

---

## 6. Official Action Contract

### 6.1 Action source

The action source must be the official walking policy / checkpoint.

Not acceptable as final action sources:

- browser-authored open-loop sinusoidal control
- browser-authored tripod gait
- direct replay of arbitrary unverified actuator scripts

### 6.2 Action application

Actions must enter the walker through official `FruitFly.apply_action()`.

This preserves:

- official actuator grouping
- official control ranges
- official action-vector semantics

### 6.3 Reference trajectory is not action truth

`InferenceWalkingTrajectoryLoader` and `HDF5WalkingTrajectoryLoader` define reference walking motion for the task, reward, and ghost-tracking logic. They do not replace the policy action source.

The design must keep this distinction explicit.

---

## 7. Viewer State Bridge Contract

The browser should consume a viewer-ready state contract, not raw simulation internals.

### 7.1 Required payload

The minimum formal viewer payload is:

- `frame_id`
- `sim_time`
- `running_state`
- `scene_version`
- `body_poses[]`
  - `body_name`
  - `position`
  - `quaternion`

### 7.2 Formal key

`body_name` is the formal key for browser synchronization.

`body_index` may be used internally for optimization, but must not be the formal UI contract because export ordering can change as scene contents change.

### 7.3 Why not raw `qpos`

The viewer should not consume raw `qpos` as its formal contract because that would force Babylon to re-implement model interpretation and kinematic reconstruction.

Strict best practice requires:

- Python runtime computes the physical world state
- browser consumes viewer-ready poses

---

## 8. Babylon Viewer Contract

`Babylon.js` remains the official browser presentation layer for `/mujoco-fly`.

Its responsibilities are:

- create the canvas
- create lights and scene
- use `ArcRotateCamera（环绕相机）`
- support:
  - drag
  - rotate
  - zoom
  - reset camera
- map `body_name -> TransformNode`
- update node transforms from streamed viewer state

It must not:

- generate gait
- step the authoritative simulation
- reinterpret `qpos`
- invent scene truth

---

## 9. Control-Channel Contract

The browser sends only lifecycle controls to the authoritative runtime:

- `start`
- `pause`
- `reset`

It does not send low-level actuator control in the strict-official architecture.

This keeps control ownership entirely inside the official runtime.

---

## 10. Failure Semantics

The page must fail visibly instead of silently degrading into a fake simulation.

Unavailable states include:

- official runtime unavailable
- official policy / checkpoint unavailable
- scene export bundle unavailable
- state stream disconnected
- `body_name` mapping contract invalid

When unavailable:

- show explicit viewer-unavailable state
- do not fall back to browser-authored gait
- do not present the page as official walking if the official action chain is absent

---

## 11. Non-Goals

This design does not cover:

- public multi-user deployment
- checkpoint training workflows
- whole-brain coupling
- browser-side authoritative physics
- a second “demo” gait implementation

---

## 12. Final Summary

The strict-official `/mujoco-fly` route is not a browser simulation page first. It is a browser viewer for the official `flybody` walking runtime.

The authoritative stack is:

- Python `flybody`
- official `walk_imitation()` scene
- official policy / checkpoint
- official `MuJoCo` stepping

The browser stack is:

- `Babylon.js`
- interactive camera
- streamed `body pose` synchronization

This is the only route that satisfies the user's requirement to follow official best practice without introducing non-official control semantics.
