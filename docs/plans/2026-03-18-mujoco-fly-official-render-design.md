# MuJoCo Fly Official Render Page Design

**Goal:** Add a new `/mujoco-fly-official-render` route that displays a strict-official `MuJoCo render（MuJoCo 原生渲染）` page driven by the Python `flybody（果蝇身体环境） + dm_control（环境与任务框架） + MuJoCo（物理仿真引擎）` runtime, without changing the existing `/mujoco-fly` page.

**Scope:** This design defines the strict-official render chain, page responsibilities, control contract, frame transport contract, unavailable semantics, and testing boundaries for a new official render page. It explicitly excludes browser-authored 3D physics, browser-side gait generation, and any requirement to preserve the earlier Babylon viewer semantics for this new route.

**Relationship to existing plans:**
- [/Users/zhuangwei/Downloads/coding/Fruitfly/docs/plans/2026-03-18-official-flybody-mujoco-viewer-design.md](/Users/zhuangwei/Downloads/coding/Fruitfly/docs/plans/2026-03-18-official-flybody-mujoco-viewer-design.md)
- [/Users/zhuangwei/Downloads/coding/Fruitfly/docs/plans/2026-03-17-live-inspector-design.md](/Users/zhuangwei/Downloads/coding/Fruitfly/docs/plans/2026-03-17-live-inspector-design.md)

---

## 1. Problem Statement

The repository currently has two separate ideas in tension:

- a browser-facing `/mujoco-fly` route built around `Babylon.js（三维引擎）`
- a strict-official requirement that behavior and rendering follow the mature `flybody + dm_control + MuJoCo` path

After reviewing the official runtime chain, the strict-official conclusion is:

- `walk_imitation()` defines the official walking scene
- `FruitFly.apply_action()` defines official actuator application semantics
- `composer.Environment.step()` and `physics.step()` define the official step lifecycle
- `physics.render(...)` or the native `simulate（原生查看器）` path define the mature official render route

Therefore, a strict-official render page should not be built around Babylon as the primary renderer. Babylon can still be useful for browser 3D viewing in other routes, but it is not the strict-official render chain.

---

## 2. Approved Final Decision

The repository will add a new page:

- route: `/mujoco-fly-official-render`

This page will:

- use a large viewport
- show frames produced by the authoritative Python `flybody` runtime
- control the authoritative runtime through minimal page controls
- fail closed when the official runtime chain is unavailable

This page will not:

- modify `/mujoco-fly`
- use browser-side `MuJoCo WASM（网页端 MuJoCo 运行时）` as the authoritative simulator
- use `Babylon.js` as the primary render path
- generate gait in the browser
- reinterpret raw `qpos（广义坐标）` in the browser

---

## 3. Official Source-of-Truth Chain

The strict-official render chain is:

```text
official flybody policy / checkpoint
-> walk_imitation()
-> FruitFly.apply_action()
-> composer.Environment.step()
-> MuJoCo physics.step()
-> physics.render(...)
-> browser page
```

Key implications:

- scene truth belongs to `walk_imitation()`
- ground truth belongs to `floors.Floor()`
- action truth belongs to the official policy / checkpoint
- frame truth belongs to `physics.render(...)`
- the browser only displays and controls the authoritative runtime

---

## 4. Why Babylon Is Not the Strict-Official Render Path

`Babylon.js` is acceptable for:

- interactive browser viewing
- camera interaction
- presentation-oriented 3D

But it is not the strict-official render path because:

- the official `flybody` walking stack is defined in Python
- official stepping happens through `composer.Environment.step()`
- official render in the repository already uses `physics.render(...)`
- browser 3D engines do not reproduce MuJoCo's mature render stack pixel-for-pixel

This means:

- Babylon can represent official state
- Babylon cannot be labeled as the official mature render path

For this new route, strict-official requirements take priority over browser-native 3D presentation.

---

## 5. Page Architecture

### 5.1 Page identity

`/mujoco-fly-official-render` is a dedicated official render observer page.

Its job is to:

- show a large official render surface
- control the runtime lifecycle
- switch official camera presets
- expose strict unavailable status when the runtime chain is absent

### 5.2 Page layout

The page should contain:

- `Hero Render Surface（主渲染视窗）`
- `Minimal Controls（最小控制栏）`
- `Camera Presets（相机预设）`
- `Runtime Status（运行状态）`

The page should not contain:

- scientific side panels
- brain-view data
- Babylon scene controls
- free-form browser camera controls

---

## 6. Official Runtime Contract

The authoritative runtime must live in Python.

It is responsible for:

- constructing `walk_imitation()`
- loading the official walking policy / checkpoint
- producing the official `action vector（动作向量）`
- stepping the environment
- rendering the current frame through `physics.render(...)`

The browser is not allowed to:

- host the authoritative simulation
- generate replacement controls
- synthesize fallback gait

---

## 7. Control Contract

The page sends only lifecycle and camera controls to the authoritative runtime:

- `start`
- `pause`
- `reset`
- `set_camera_preset`

Control semantics:

- `start`: begin or resume continuous official stepping
- `pause`: stop stepping while keeping the current official state
- `reset`: reset the official environment and any policy state to the initial episode state
- `set_camera_preset`: switch the authoritative render camera used by `physics.render(...)`

The browser must not implement:

- local playback timers pretending to be runtime stepping
- free camera transforms that bypass official camera presets

---

## 8. Frame Transport Contract

### 8.1 Required frame path

The displayed image must come from:

- `physics.render(width=..., height=..., camera_id=...)`

This should follow the same mature render path already used by the replay renderer.

### 8.2 Transport choice

For the first strict-official implementation, the page should use:

- HTTP control endpoints
- HTTP single-frame render endpoint
- optional lightweight status polling

This keeps the transport aligned with the repository's existing render model and avoids introducing a second speculative streaming protocol before the official page exists.

### 8.3 Camera contract

The page must only expose runtime-supported camera presets.

If a camera preset is unsupported:

- the runtime must reject it explicitly
- the browser must show an unavailable or error state
- no client-side approximation is allowed

---

## 9. Runtime Status Contract

The page needs a small runtime status payload that can answer:

- `available`
- `running_state`
- `current_camera`
- `checkpoint_loaded`
- `reason`

This status payload is operational metadata.

It does not replace the rendered frame and does not become a new scientific data source.

---

## 10. Strict Unavailable Semantics

The page must fail closed when any required official dependency is missing, including:

- official walking checkpoint not found
- official runtime cannot initialize
- official scene cannot be constructed
- official render call cannot execute

In these cases the page must:

- show a clear unavailable state
- disable controls that cannot operate
- avoid any fallback to:
  - mock motion
  - old MP4 playback
  - browser-authored gait
  - Babylon replacement rendering

---

## 11. Non-Goals

This design does not:

- replace `/mujoco-fly`
- remove the Babylon viewer route
- add browser-native 3D interaction to the official render page
- define the final public deployment architecture
- define a generic render-streaming protocol for all runtime views

---

## 12. Acceptance Criteria

The new page is successful only if all of the following are true:

- opening `/mujoco-fly-official-render` shows a dedicated official render page
- the displayed image comes from the authoritative `physics.render(...)` path
- `Start / Pause / Reset / Camera preset` control the official runtime
- missing official checkpoint results in strict unavailable behavior
- the implementation does not modify the behavior contract of `/mujoco-fly`

---

## 13. Implementation Direction

The implementation should build on the repository's existing official render path rather than inventing a new visual stack.

The most relevant prior art is:

- [replay_renderer.py](/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/replay_renderer.py)

That file already demonstrates the mature repository pattern:

- restore authoritative state
- call `physics.render(...)`
- return encoded frame bytes

The new official render page should reuse this pattern at the runtime boundary, while adding lifecycle controls and a dedicated page route.
