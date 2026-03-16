# Live Inspector Design

**Goal:** Replace the current `Fly Body Live（果蝇身体实时区）` fixed-video presentation with an in-console `live inspector（实时观察器）` that lets researchers observe a real `flybody（果蝇身体与 MuJoCo 环境）` rollout in `live / replay / artifact（实时 / 回放 / 归档）` modes while preserving the scientific truth path.

**Scope:** Phase 1 design only. This design assumes the existing checkpoint loading, `flybody` closed-loop rollout, `MuJoCo（物理仿真引擎）` rendering, and neural-console backend/frontend shells already exist.

**Current pain points:** The current body panel renders a saved `rollout.mp4（闭环视频产物）` at `320x240` and stretches it inside a video-first layout. The result is visually blurry, too far away from the fruit fly, and not suitable for inspection or replay from alternate cameras.

---

## 1. Approved Product Decision

The body panel should stop behaving like a media player and start behaving like an `inspector（观察器）`.

Approved decisions:

- keep the `flybody + MuJoCo` render path as the single scientific truth source
- embed the inspector in the existing web console rather than opening a separate desktop viewer
- support `live（实时观察）` and `replay（回放复盘）` as first-class modes
- keep `rollout.mp4` as an optional `artifact（归档产物）`, not the primary viewing surface
- remove the large status strip shown in the old body area mock
- remove visual nesting in the body panel so the viewport gets the maximum amount of space
- place `Behavior Summary（行为摘要）` under the viewport rather than in a separate right rail

Not approved for Phase 1:

- a front-end-only fake 3D fly renderer
- replacing `flybody` with a different embodiment stack
- multi-user streaming or cloud-hosted long-running inspector sessions
- movie-style post-processing or a full nonlinear editor timeline

---

## 2. Body Panel Layout

The approved body-area layout is:

```text
┌──────────────────────────────────────────────────────────────────────┐
│ 果蝇身体实时区                                                       │
│  [Live/Replay] [Start/Pause] [Hero/Side/Back] [Follow/Free] [HD]    │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────────┐  │
│  │                        实时观察窗                              │  │
│  │                                                                │  │
│  │                                                                │  │
│  │                                                                │  │
│  └────────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  行为摘要                                                            │
│  步数 32/64   奖励 1.00   速度 0.94   姿态 0.98   提前终止 false      │
└──────────────────────────────────────────────────────────────────────┘
```

Layout rules:

- the inspector toolbar sits above the viewport
- the viewport is the dominant element in the body panel
- the behavior summary sits directly below the viewport
- the previous body-area right rail is removed
- the previous body-area status strip is removed
- the body card should feel like one continuous surface, not nested `panel / shell / frame` boxes

---

## 3. Runtime Architecture

The body inspector should use a three-layer architecture:

1. `simulation runtime（仿真运行层）`
   - owns the real `flybody` environment
   - owns the active policy wrapper
   - advances `env.step(...)`
   - renders frames through `environment.physics.render(...)`

2. `inspection service（观察服务层）`
   - creates and manages `inspector session（观察会话）`
   - stores current run state and camera state
   - publishes the latest frame and summary
   - records replay snapshots into a bounded `ring buffer（环形缓冲）`

3. `console UI（控制台界面层）`
   - displays the body inspector toolbar, viewport, and summary
   - issues play/pause/camera/quality/replay controls
   - never fabricates body frames when real runtime data is missing

### 3.1 Truth Path

The scientific truth path remains:

`checkpoint（模型检查点）`
`-> policy wrapper（策略包装器）`
`-> flybody env（果蝇身体环境）`
`-> MuJoCo render（MuJoCo 渲染）`
`-> inspector frame（观察器帧）`
`-> optional rollout.mp4（可选归档视频）`

This design does not permit an alternate front-end body renderer to silently replace the `MuJoCo` truth path.

---

## 4. Live / Replay / Artifact Modes

### 4.1 Live

`live（实时观察）` means the session is stepping the real environment and the body viewport is showing newly rendered `MuJoCo` frames.

Expected controls:

- `Start`
- `Pause`
- `Resume`
- `Stop`
- camera preset switch
- `Follow / Free`
- quality selection

### 4.2 Replay

`replay（回放复盘）` means the environment is restored to recorded `MuJoCo` states and re-rendered on demand from the currently selected camera.

Replay requirements:

- pause at any step
- seek to any recorded step
- switch camera while staying on the same recorded state
- keep `Behavior Summary` synchronized with the selected step

Replay must not degrade into “play back the same mp4 file”.

### 4.3 Artifact

`artifact（归档产物）` keeps:

- `summary.json`
- optional `rollout.mp4`
- replay trace files

The artifact path remains important for reproducibility, but it is not the primary interaction model.

---

## 5. Session Model

Each `inspector session（观察会话）` should expose:

- `session_id`
- `mode`: `live | replay`
- `status`: `idle | starting | running | paused | completed | failed`
- `quality`: `fast | balanced | inspect`
- `camera`: `hero | side | back | bottom | free`
- `follow_target`: default `thorax`
- `current_step`
- `max_steps`
- `eval_dir`
- `created_at`
- `error_message`

Phase 1 assumption:

- one active `live` session per local console runtime

---

## 6. Transport Strategy

Phase 1 should use `MJPEG（连续 JPEG 帧流）` or single-frame JPEG polling rather than jumping directly to a heavier streaming stack.

Why:

- simple FastAPI integration
- easy browser support
- low implementation risk
- good enough for local single-user scientific inspection

Future upgrade path:

- `WebSocket（二进制帧流）`
- lower-latency streaming
- richer bidirectional synchronization

---

## 7. Replay Snapshot Format

To support true replay inspection, each run should persist:

- `session.json`
- `state_traces.npz`
- `events.jsonl`

### 7.1 session.json

Stores immutable session metadata:

- `session_id`
- `task`
- `checkpoint`
- `quality`
- `steps_completed`
- `created_at`

### 7.2 state_traces.npz

Stores per-step numerical state:

- `step_id[T]`
- `sim_time[T]`
- `qpos[T, nq]`
- `qvel[T, nv]`
- `ctrl[T, nu]`
- `reward[T]`
- `terminated[T]`
- `body_upright[T]`
- `forward_velocity[T]`

### 7.3 events.jsonl

Stores sparse timeline events:

- `pause`
- `resume`
- `camera_change`
- `terminated_early`
- optional annotation events later

This format is required because replay needs to re-render arbitrary cameras from the same state. An `mp4` alone cannot support that.

---

## 8. Camera Policy

Phase 1 camera support should use the `flybody` camera assets that already exist in `fruitfly.xml`:

- `hero`
- `side`
- `back`
- `bottom`
- track-style presets as needed

Phase 1 camera controls:

- preset switch
- `Follow`
- `Free-lite`
- zoom in/out

`Free-lite（轻量自由相机）` means:

- the user can change `yaw / pitch / distance`
- the camera still orbits a stable follow target
- no fully unconstrained fly-through camera yet

---

## 9. Image Quality Policy

The body inspector must treat image clarity as a first-class requirement.

### 9.1 Quality tiers

- `Fast`: `640x480`
- `Balanced`: `960x720`
- `Inspect`: `1280x960`

### 9.2 Display rules

- do not crop the body frame with a `video player` style `object-cover`
- display the viewport using the source frame aspect ratio
- prefer a close default camera so the fly occupies a meaningful share of the frame
- keep `rollout.mp4` encoding decisions independent from the `live` viewing path

### 9.3 Minimum acceptable bar

Phase 1 is not acceptable if:

- the default body viewport still ships at `320x240`
- the fly is still only a tiny object in the middle of the frame
- the main UI still behaves like a fixed `video` player

---

## 10. Error Handling

The body inspector must preserve `research strict mode（科研严格模式）`.

Allowed states:

- `idle`
- `starting`
- `running`
- `paused`
- `completed`
- `failed`
- `unavailable`

Rules:

- if `flybody` or `MuJoCo` runtime is unavailable, show explicit unavailable state
- do not substitute mock body video
- if the selected camera is invalid, fall back to `hero`
- if a requested quality tier is too expensive, degrade one level and surface that change
- if replay traces are missing, show `replay unavailable`

---

## 11. Performance Guardrails

Phase 1 targets:

- single local user
- one active live session
- `10-20 fps` is acceptable
- bounded replay ring buffer of roughly `1000-2000` steps
- body summary refresh may be slower than frame refresh

Out of scope for Phase 1:

- cloud fan-out streaming
- multi-user synchronized observation
- 60 fps guarantee

---

## 12. Validation Criteria

The design is considered successfully implemented when all of the following are true:

- the console can start a real live inspector session
- the body panel shows a real `MuJoCo` body frame, not a fixed embedded video player
- the viewport is visually dominant and the old status strip is gone
- `Behavior Summary` sits below the viewport
- users can switch at least `hero / side / back`
- users can pause and resume a live run
- users can enter replay mode after a run completes
- replay can seek to a step and re-render the current camera from stored state
- the default image quality is visibly sharper than the old `320x240` artifact path

