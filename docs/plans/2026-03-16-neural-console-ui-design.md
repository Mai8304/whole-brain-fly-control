# Neural Console UI Design

**Goal:** Design a long-lived local UI for the digital fruit fly project that shows experiment controls on the left, brain activity on the upper-right, and body behavior video on the lower-right, while making it clear that users control experiment conditions rather than directly commanding motion.

**Scope:** Phase 1 UI design only. This design assumes the existing full-brain `FlyWire（果蝇连接组平台）` snapshot, `compiled graph（训练编译图）`, `flybody（果蝇身体与 MuJoCo 物理环境）` closed-loop rollout, and checkpoint loading pipeline already work.

**Frontend stack decision:** The UI frontend should use `React（前端框架） + shadcn/ui（组件体系） + react-three-fiber（React 的 Three.js 3D 渲染层）`. The backend control path remains Python-based and feeds the frontend through a lightweight UI-facing API/runtime bridge.

**Design-system decision:** The console family should follow the local `ui-ux-pro-max（界面设计技能）` design-system output persisted at:

- [MASTER.md](/Users/zhuangwei/Downloads/coding/Fruitfly/design-system/MASTER.md)
- [console-family.md](/Users/zhuangwei/Downloads/coding/Fruitfly/design-system/pages/console-family.md)

---

## 1. Product Goal

The UI should feel like a `digital fly experiment console（数字果蝇实验控制台）`, not a robot remote control.

The core user story is:

1. The user sets experiment conditions.
2. The system applies physical and sensory inputs.
3. Inputs propagate through `afferent / intrinsic / efferent（输入 / 中间 / 输出）` neural structure.
4. The model decodes actions.
5. The fruit fly body responds.
6. The user sees both brain-side and body-side changes in one synchronized interface.

The UI must explicitly prevent the impression that the user is directly editing `59`-dimensional actions or joint trajectories.

---

## 2. Layout

The top-level layout is:

- Left: parameter console
- Right top: brain-region visualization + explanation
- Right bottom: fly behavior video + behavior summary
- Top banner: pipeline execution state
- Bottom log: execution log
- Shared timeline: synchronizes the top-right and bottom-right views

### 2.2 UI system guardrails

The frontend should follow these guardrails:

- use `shadcn/ui` for console panels, cards, buttons, form controls, tabs, logs, and status surfaces
- use `react-three-fiber` for the right-top 3D brain view
- `Experiment Console（实验控制台）` and `Training Console（训练控制台）` must share one visual design system rather than diverging into separate styles
- keep the page style in a restrained `scientific console（科学实验控制台）` direction
- avoid generic dashboard boilerplate styling
- keep emphasis colors for:
  - pipeline state
  - ROI activity
  - controlled environmental overlays
- treat layout, spacing, accessibility, and state feedback as a first-class design system concern rather than ad-hoc page styling

### 2.3 Theme and localization requirements

Both consoles must support the same global presentation controls.

#### Theme modes

Required:

- `light（亮色）`
- `dark（暗色）`
- `system（跟随系统）`

The active theme must be shared across both consoles and resolved from one common state source.

#### Languages

Required:

- `English（英文）`
- `简体中文`
- `繁體中文`
- `日本語（日文）`

Behavior:

- follow the system language when supported
- default to `English` if the system language is unsupported or unavailable
- keep terminology, status labels, and tooltips semantically aligned across all supported languages

#### Design consistency

The page family must behave like one product:

- same component primitives
- same typography scale
- same state color semantics
- same tooltip structure
- same theme and localization switch behavior

### 2.4 Approved visual system

The approved console-family design system is:

- Visual direction: `scientific operations console（科研运维控制台风格）`
- Palette: blue-slate operational neutrals with amber warning accents and green/red validation states
- Typography:
  - headings: `Fira Code`
  - body: `Fira Sans`
  - mono/logs: `Fira Code`

The visual rules are:

- state first, decoration second
- high-contrast typography on low-noise surfaces
- shared badge/card/table/tooltip primitives across both consoles
- no glass-heavy decorative treatment over core data surfaces
- no marketing-style hero language or ornamental gradients on operational views

### 2.1 ASCII Layout

```text
+======================================================================================================================+
| WHOLE-BRAIN FLY CONSOLE                                                                                              |
+======================================================================================================================+
| Mode: [ Demo ] [ Experiment ]      Session: straight_walking_v1      Status: IDLE / RUNNING / PAUSED               |
|                                                                                                                      |
| Pending Changes: N      [Apply & Run] [Discard]      Run: [Start] [Stop] [Reset] [Step] [Save MP4]                |
+======================================================================================================================+
| PIPELINE STATUS                                                                                                      |
| [ Environment / Sensory Input ] -> [ Afferent ] -> [ Whole-Brain ] -> [ Efferent ] -> [ Decoder ] -> [ Body ]    |
+======================================================================================================================+
| LEFT: PARAMETER CONSOLE                             | RIGHT TOP: BRAIN ACTIVITY                                       |
|                                                     |                                                                 |
| Session                                             | Brain View                                                      |
| Model                                               | Brain Explanation                                               |
| Environment Physics                                 |                                                                 |
| Sensory Inputs                                      |                                                                 |
| Run                                                 |                                                                 |
| Intervention Log                                    |                                                                 |
+-----------------------------------------------------+-----------------------------------------------------------------+
| RIGHT BOTTOM: FLY BODY BEHAVIOR                                                                                      |
| Fly Body Live                                                                                                        |
| Behavior Summary                                                                                                     |
| Shared Timeline                                                                                                      |
+======================================================================================================================+
| EXECUTION LOG                                                                                                        |
+======================================================================================================================+
```

---

## 3. Left Console Design

The left console is split into six panels.

### 3.1 Session

Fields:
- `Mode（模式）`: `Demo` / `Experiment`
- `Run name（运行名）`
- `Seed（随机种子）`

Purpose:
- Manage reproducibility and presentation mode.

### 3.2 Model

Fields:
- `Checkpoint（模型检查点）`
- `Task（任务）`: first version uses only `straight_walking（稳定直行）`
- `Policy mode（策略模式）`: `Deterministic（确定性）` / `Sampled（采样）`

Purpose:
- Select which brain model drives the body.

### 3.3 Environment Physics

Fields:
- `Terrain（地形）`: `flat（平地）`, `rough（粗糙地形）`
- `Friction（摩擦）`: continuous slider
- `Wind（风）`: continuous signed slider
- `Rain / Wetness（降雨 / 湿滑程度）`: continuous slider

Purpose:
- Control physical perturbations applied to the body environment.

Interpretation rules:
- `Rain` is a `physical perturbation proxy（物理扰动代理变量）`, not a full fluid/weather simulator.
- `Rain` primarily affects effective slip / friction and optional contact instability.

### 3.4 Sensory Inputs

Fields:
- `Temperature（温度）`: continuous scalar
- `Odor（气味）`: continuous scalar

Purpose:
- Represent abstract sensory inputs injected into `afferent neurons（输入神经元）`.

Interpretation rules:
- These are `sensory input scalars（感觉输入标量）` in V1.
- They are not yet claims of biologically complete thermosensory or olfactory circuit reconstruction.

Panel note:
- `Temperature / Odor are injected as sensory inputs to afferent neurons. They are not direct action controls.`

### 3.5 Run

Fields:
- `Max steps（最大步数）`
- `Run mode（运行模式）`: `Single Run（单轮运行）` / `Loop Demo（循环演示）`
- `Camera（相机）`
- `Render FPS（渲染帧率）`

Actions:
- `Apply & Run（应用并运行）`
- `Stop`
- `Reset`
- `Step`
- `Save MP4`

Rules:
- Parameter changes first enter `Pending Changes（待应用改动）`.
- Changes only take effect after `Apply & Run`.

### 3.6 Intervention Log

Read-only panel.

Displays:
- which parameters changed
- whether changes are `physical` or `sensory`
- `No direct action override（无直接动作覆盖）`
- `No joint override（无关节覆盖）`
- `Actions are model-generated（动作由模型生成）`

Purpose:
- Prevent the interface from feeling like a direct motion puppeteer.

---

## 4. Parameter Semantics

A hybrid parameter design is used.

### 4.1 Physical parameters

- `Terrain`: enum
- `Friction`: `0.3 ~ 1.5`
- `Wind`: `-1.0 ~ 1.0`
- `Rain`: `0.0 ~ 1.0`

These are interpreted as physical environment controls or physical perturbation proxies.

### 4.2 Sensory parameters

- `Temperature`: `-1.0 ~ 1.0`
- `Odor`: `0.0 ~ 1.0`

These are interpreted as abstract sensory input strengths entering `afferent neurons（输入神经元）`.

This avoids falsely implying fully biologically grounded units in V1 while keeping the UI scientifically honest.

---

## 5. Pipeline Execution Model

When the user clicks `Apply & Run`, the system should expose a visible six-stage execution chain.

1. `Apply Inputs（应用输入）`
2. `Reset Environment（重置环境）`
3. `Inject Sensory Inputs（注入感觉输入）`
4. `Propagate Whole-Brain State（全脑传播）`
5. `Decode Actions（解码动作）`
6. `Roll Out Body（身体闭环展开）`

Each stage has one of four states:
- `idle（未开始）`
- `queued（已排队）`
- `running（执行中）`
- `done（已完成）`

Why this matters:
- The user should perceive a causal neural pipeline, not a button directly driving body motion.

Latency goals:
- Small parameter changes: first visual response within `0.2s ~ 1.0s`
- Heavier resets / checkpoint changes: first visual response within `1s ~ 3s`

---

## 6. Right-Top Brain Activity Design

### 6.1 Visualization approach

Recommended V1 approach:
- `ROI / neuropil（脑区 / 神经纤维区）` region glow
- optional `top active neurons overlay（最活跃神经元叠加）`
- no full 139k-neuron point-cloud flicker in V1

Why:
- Region-level activation is more interpretable than full-node flashing.
- It aligns better with `neuPrint ROI（neuPrint 脑区）`-style region reasoning.
- It is more suitable for real-time or near-real-time UI.

### 6.2 Brain Explanation panel

Display:
- `afferent activity（输入层活动）`
- `intrinsic activity（中间层活动）`
- `efferent activity（输出层活动）`
- `Top active ROIs（最活跃脑区）`
- `Mapping coverage（映射覆盖度）`
- `View mode（当前视图模式）`: region-aggregated

Purpose:
- Make the brain view explanatory, not just decorative.

### 6.3 Brain view payload contract

The UI-facing backend should emit a deterministic payload with this shape:

```json
{
  "view_mode": "region-aggregated",
  "mapping_coverage": {
    "roi_mapped_nodes": 118320,
    "total_nodes": 139244
  },
  "region_activity": [
    {
      "roi_id": "MB",
      "roi_name": "Mushroom Body",
      "activity_value": 0.81,
      "activity_delta": 0.12,
      "node_count": 1240
    }
  ],
  "top_regions": [
    {
      "roi_id": "MB",
      "roi_name": "Mushroom Body",
      "activity_value": 0.81,
      "activity_delta": 0.12,
      "node_count": 1240
    }
  ],
  "top_nodes": [
    {
      "node_idx": 8211,
      "activity_value": 1.14,
      "flow_role": "efferent"
    }
  ]
}
```

This contract is intentionally conservative:

- `region_activity` is the full region-level list available to the UI
- `top_regions` is a sorted subset for explanation panels
- `top_nodes` is optional and limited to a small overlay set

---

## 7. Right-Bottom Fly Behavior Design

### 7.1 Live body view

Show a live or quasi-live rendered `flybody` rollout.

Modes:
- `Single Run（单轮运行）`
- `Loop Demo（循环演示）`

Defaults:
- `Experiment` mode defaults to `Single Run`
- `Demo` mode defaults to `Loop Demo`

### 7.2 Behavior Summary

V1 should display:
- `steps_completed（完成步数）`
- `terminated_early（是否提前终止）`
- `has_nan_action（动作是否含 NaN）`
- `mean_action_norm（平均动作幅度）`
- `final_reward（最终奖励）`
- `final_heading_delta（最终朝向漂移代理）`

Later versions should replace or augment this with stronger behavior metrics such as:
- `forward_velocity_mean（平均前向速度）`
- `forward_velocity_std（前向速度波动）`
- `termination_rate（提前终止率）`
- `reward_mean（平均奖励）`
- `body_upright_mean（身体直立程度）`

---

## 8. Brain-Body Synchronization

The right-top and right-bottom panels must be synchronized.

### 8.1 Time sync
- Brain activity and body behavior share the same `step_id（时间步编号）`

### 8.2 Event sync
- Key rollout events appear on a shared timeline
- Clicking an event moves both panels to the same step

### 8.3 Explanation sync
- A small explanation panel summarizes how current inputs and current neural changes relate to current body behavior

Example explanation:
- `Wind increased at step 12`
- `Afferent activity rose first`
- `Intrinsic state reorganized over steps 13-15`
- `Efferent activity increased before heading drift`
- `Body deviated laterally at step 16`

---

## 9. Shared Timeline

The UI includes a shared timeline under the right-side panes.

Shows:
- step markers
- event markers
- synchronized playback position

Purpose:
- Make the brain-side and body-side views feel causally connected rather than separate clips.

---

## 10. V1 Scope Boundaries

### In V1
- `straight_walking（稳定直行）`
- `flat / rough terrain（平地 / 粗糙地形）`
- `friction（摩擦）`
- `wind（风）`
- `rain（降雨 / 湿滑代理）`
- `temperature（温度感觉输入标量）`
- `odor（气味感觉输入标量）`
- `Single Run / Loop Demo（单轮运行 / 循环演示）`
- `summary.json + MP4`
- pipeline state visualization
- region-level brain activation display

### Not in V1
- direct joint editing
- direct action editing
- turning / gait initiation / flight tasks
- neural ablation controls
- per-neuron full-brain real-time rendering
- biologically complete temperature/odor/rain modeling claims

---

## 11. Best-Practice Rationale

This design follows a long-lived experimental UI approach:
- the left panel controls experiment conditions, not motor outputs
- the top pipeline makes the neural causal chain explicit
- the top-right brain view is interpretable, not merely decorative
- the bottom-right body view grounds the result in actual behavior
- the intervention log protects the scientific story from looking like puppeteering
