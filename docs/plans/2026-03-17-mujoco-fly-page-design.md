# MuJoCo Fly Page Design

**Goal:** Define a new standalone `/mujoco-fly` route that renders a real browser-side `MuJoCo WASM（网页端 MuJoCo 运行时）` fruit-fly simulation using `Babylon.js（三维引擎）` and `flybody（果蝇身体与 MuJoCo 模型资源）`, with no scientific data-chain integration in V1.

**Scope:** This design covers the V1 local UI-only route, runtime architecture, asset packaging, interaction contract, failure semantics, and testing strategy for a standalone `MuJoCo` fruit-fly page inside the existing Vite/React app. It intentionally does not cover live research data, replay synchronization, or whole-brain coupling.

**Relationship to existing plans:**
- `/Users/zhuangwei/Downloads/coding/Fruitfly/docs/plans/2026-03-17-live-inspector-design.md`
- `/Users/zhuangwei/Downloads/coding/Fruitfly/docs/plans/2026-03-17-live-inspector-implementation.md`

---

## 1. Problem Statement

The repository already has:

- a working web console shell
- a `react-three-fiber（React 的 Three.js 3D 渲染层）` brain viewport
- a `Fly Body Live（果蝇身体实时区）` body card that currently shows replay images or video
- a local `flybody` installation with `fruitfly.xml` and `OBJ（网格文件）` assets

The repository does not yet have:

- a standalone browser page that runs real `MuJoCo WASM` physics
- a `Babylon.js` rendering path
- a packaged front-end asset bundle for `flybody`
- a route dedicated to real-time 3D fruit-fly viewing without research-data UI coupling

The user-approved product target is not a video player, not JPEG polling, and not a fake front-end-only animation layer. The target is a genuine browser-side 3D page where `MuJoCo` owns simulation state and `Babylon` owns presentation.

---

## 2. Approved Product Decision

The approved V1 product is:

- a new standalone route: `/mujoco-fly`
- one dominant full-width 3D viewport
- real browser-side `MuJoCo WASM` stepping
- `Babylon.js` rendering
- `flybody` fruit-fly assets as the model source
- minimal controls only
- no research data chain integration in V1
- no reuse of the existing `react-three-fiber` viewport framework

Explicitly approved:

- `Start`
- `Pause`
- `Reset`
- `Reset Camera`
- `drag to orbit（拖拽绕视）`
- `rotate camera（镜头旋转）`
- `zoom（镜头缩放）`
- packaging `flybody` assets into repository-owned static files

Explicitly not in scope for V1:

- whole-brain inputs or outputs
- replay timeline integration
- formal scientific provenance UI
- parameter side panels
- HUD-style research metrics
- replacing `MuJoCo` with a fake browser animation runtime

---

## 3. Approach Comparison

### Approach A: Static Model Viewer

Render the `flybody` meshes in `Babylon.js` but do not run real `MuJoCo`.

Pros:

- fastest to build
- lowest implementation risk

Cons:

- fails the approved requirement
- not a real `MuJoCo WASM` page

### Approach B: Browser `MuJoCo WASM` + `Babylon.js` Sync

Run `MuJoCo` in the browser with official web bindings, load `fruitfly.xml`, step the simulation every frame, and synchronize `MuJoCo` state into Babylon transform nodes.

Pros:

- directly matches the approved product goal
- preserves clear responsibility boundaries
- follows official `MuJoCo` and `Babylon` best-practice separation

Cons:

- requires explicit runtime synchronization work
- needs stable asset packaging and transform mapping

### Approach C: Asset Conversion First

Convert `flybody` assets into a new scene-friendly format first, then use `MuJoCo` only for hidden physics state.

Pros:

- can simplify rendering later
- may allow nicer material control

Cons:

- adds an unnecessary conversion layer
- weakens the “strictly use flybody model resources” requirement

### Recommended approach

Recommend **Approach B**.

This is the only approach that directly satisfies the approved constraints:

- official `MuJoCo` web runtime
- official `Babylon` interaction model
- original `flybody` model source
- no fake animation layer

---

## 4. Route and Page Architecture

The new route lives inside the existing Vite/React app but behaves as an independent page:

- route: `/mujoco-fly`
- page component: dedicated page, not a console card
- layout: near full-bleed viewport, minimal chrome

The page should not inherit the existing experiment-console card structure. It may remain inside the application provider tree for shared app bootstrapping, but the page layout and runtime should be independent.

Approved V1 layout:

```text
┌──────────────────────────────────────────────────────────────────────┐
│  [Start] [Pause] [Reset] [Reset Camera]                 status      │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                                                                │  │
│  │                       Babylon 3D canvas                        │  │
│  │                                                                │  │
│  │                  MuJoCo-driven fruit-fly view                  │  │
│  │                                                                │  │
│  └────────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
```

Layout rules:

- the canvas is the dominant element
- controls remain visually lightweight
- the status indicator is small and non-intrusive
- no explanatory block or source note is rendered in V1

---

## 5. Runtime Architecture

### 5.1 Responsibility split

The runtime must follow this separation:

- `MuJoCo WASM`
  - owns model loading
  - owns `MjModel（MuJoCo 模型实例）`
  - owns `MjData（MuJoCo 状态实例）`
  - owns `mj_step（物理步进）`

- `Babylon.js`
  - owns canvas creation
  - owns scene, lights, and camera
  - owns drag/rotate/zoom interactions
  - owns final frame rendering

This follows the official `MuJoCo` visualization principle that model/state handling and renderer choice are separable.

### 5.2 Main loop

V1 should use one browser render loop:

`requestAnimationFrame`
`-> if running: step MuJoCo`
`-> sync MuJoCo transforms into Babylon nodes`
`-> render Babylon scene`

There must not be two unsynchronized loops.

### 5.3 Transform synchronization

The core integration layer is:

`MuJoCo body / geom id`
`-> Babylon transform node`

Every visible fruit-fly body part should be represented by a Babylon node whose transform is updated from `MuJoCo` every frame.

The integration must not:

- let Babylon invent animation state
- use decorative interpolation as if it were simulation truth

### 5.4 Simulation controls

Approved control behavior:

- `Start`: begin continuous stepping
- `Pause`: stop stepping, keep current pose
- `Reset`: reset `MjData` to the initial pose or approved keyframe
- `Reset Camera`: restore the default Babylon camera framing

Initial page state should be:

- assets load automatically
- runtime initializes automatically
- simulation starts in `paused（暂停）`

This keeps startup deterministic and gives the user explicit control over stepping.

---

## 6. Official Best-Practice Constraints

V1 must follow these best-practice rules:

- use the official `@mujoco/mujoco` web bindings
- use Babylon-native camera control patterns rather than custom pointer math
- keep simulation state ownership exclusively in `MuJoCo`
- keep presentation ownership exclusively in `Babylon`
- preserve original `flybody` asset semantics rather than replacing them with fabricated placeholders
- fail visibly when runtime bootstrapping or assets are invalid

V1 must not:

- quietly fall back to static images
- replace missing meshes with a fake fruit-fly stand-in
- present a front-end-only animation as if it were `MuJoCo`

---

## 7. Asset Packaging and File Organization

The page must not depend on `.venv-flybody` at runtime. Instead, `flybody` assets should be materialized into repository-owned static assets.

Recommended structure:

- `public/mujoco-fly/fruitfly/fruitfly.xml`
- `public/mujoco-fly/fruitfly/assets/*.obj`
- `src/pages/mujoco-fly/mujoco-fly-page.tsx`
- `src/pages/mujoco-fly/components/mujoco-fly-viewport.tsx`
- `src/pages/mujoco-fly/lib/load-mujoco.ts`
- `src/pages/mujoco-fly/lib/load-fruitfly-model.ts`
- `src/pages/mujoco-fly/lib/babylon-scene.ts`
- `src/pages/mujoco-fly/lib/transform-sync.ts`
- `src/pages/mujoco-fly/lib/mujoco-fly-runtime.ts`

The repository should also include a repeatable preparation script, for example:

- `scripts/prepare_mujoco_fly_assets.py`

This script should copy the required `flybody` XML and mesh assets into `public/mujoco-fly/fruitfly/` in a deterministic way.

The runtime asset rule is:

`virtualenv flybody install（虚拟环境 flybody 安装）` is the source
`public/mujoco-fly/fruitfly` is the page runtime package

---

## 8. Interaction Contract

V1 interaction must support:

- drag to orbit
- rotate around the subject
- zoom in and out
- reset camera

The preferred Babylon camera is `ArcRotateCamera（Babylon 环绕相机）` or an equivalent official orbit-camera pattern.

Interaction rules:

- camera reset affects only the camera
- simulation reset affects only `MuJoCo` state
- dragging and zooming must remain available while paused
- interaction feedback should remain smooth even if stepping is paused

---

## 9. Failure Semantics

V1 should fail closed and visibly.

If any of the following fail:

- `MuJoCo WASM` bootstrap
- XML loading
- mesh loading
- transform mapping creation

the page must show:

- a clear runtime error state
- disabled simulation controls where appropriate

It must not:

- show a fake static fruit fly
- silently switch to the old replay-image path
- pretend the simulation is running

---

## 10. Testing Strategy

### 10.1 Unit and integration tests

V1 should test:

- route resolution for `/mujoco-fly`
- page shell rendering
- presence of the viewport container
- presence of the control buttons
- state transitions: `loading -> ready -> paused -> running -> error`
- button wiring for `Start`, `Pause`, `Reset`, and `Reset Camera`

The first automated test layer should not attempt pixel-perfect 3D verification.

### 10.2 Asset preparation tests

The asset preparation script should be tested for:

- copying `fruitfly.xml`
- copying required `OBJ` files
- preserving directory layout expected by the XML

### 10.3 Manual smoke test

The first implementation is only successful if a manual local smoke test confirms:

- `/mujoco-fly` opens
- the fruit fly is visible in Babylon
- the page can orbit, rotate, and zoom
- `Start` causes visible `MuJoCo`-driven motion
- `Pause` freezes the pose
- `Reset` restores the initial pose
- `Reset Camera` restores the default framing

---

## 11. Non-Goals for V1

V1 intentionally does not include:

- whole-brain data integration
- replay or timeline synchronization
- UI reuse from the old `Fly Body Live` card
- multi-camera presets beyond the default orbit camera if not needed
- research dashboards or body telemetry overlays
- networked sessions or server-side streaming

The V1 bar is narrower and stricter:

build one clean standalone route that proves

- official `MuJoCo` web runtime
- Babylon-rendered fruit-fly scene
- original `flybody` asset usage
- stable interactive camera controls

without mixing in unrelated platform concerns.
