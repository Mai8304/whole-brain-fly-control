# Neural Console UI Refinement Design

**Goal:** Refine the Phase 1 neural console UI so the brain panel uses a FlyWire-first 3D asset strategy and the body video uses a stylized-but-scientifically-honest kitchen tabletop presentation.

**Scope:** This is a refinement layer on top of `2026-03-16-neural-console-ui-design.md`. It does not replace the base UI design; it narrows down visualization assets, ROI display policy, and video HUD policy.

**Frontend component policy:** Use `shadcn/ui（组件体系）` for all 2D UI structure and controls. Use `react-three-fiber（React 的 Three.js 3D 渲染层）` only for the 3D brain panel. The visual system should follow a restrained `scientific console（科学实验控制台）` direction rather than generic SaaS dashboard styling.

---

## 1. Brain Asset Strategy

### 1.1 V1 asset source

V1 should prefer `FlyWire brain mesh（FlyWire 果蝇脑网格）` as the whole-brain shell asset.

Why:
- It matches the project's primary connectome source.
- It keeps the structural story coherent across snapshot export, compiled graph, and UI.
- It avoids introducing an unrelated atlas stack as the first presentation layer.

Fallbacks if needed later:
- `Virtual Fly Brain（果蝇虚拟脑平台）` standard brain template
- self-generated ROI meshes from atlas volumes

### 1.2 Recommended visualization stack

The brain view should use three visual layers:

1. `whole-brain shell（整脑外壳）`
2. `ROI activity glow（脑区活动发光）`
3. `top active neurons overlay（最活跃神经元叠加）`

This is explicitly preferred over:
- embedding `FlyWire Codex（FlyWire 连接组可视化工具）` as an external window
- rendering all 139k neurons as a real-time point cloud

---

## 2. ROI and Top-Neuron Policy

### 2.1 Why not “all ROIs equally bright” in V1

V1 should not treat every mapped ROI as equally prominent. That tends to create a noisy, hard-to-read display.

Instead:
- the shell provides spatial context
- ROI glow is the primary explanatory layer
- top-neuron points provide local evidence

### 2.2 ROI selection principle

V1 ROIs should be selected by information-flow role, not by arbitrary popularity.

Three groups:
- `input-associated ROIs（输入相关脑区）`
- `core-processing ROIs（核心处理中间脑区）`
- `output-associated ROIs（输出相关脑区）`

Target V1 ROI count:
- `6-12` representative ROIs total

### 2.3 Display hierarchy

Within the selected ROI set:
- most-active `3-5` ROIs are the primary highlighted layer
- the rest remain visible but visually subordinate

### 2.4 Top-neuron overlay policy

The brain panel should include `top active neurons（最活跃神经元）`, but in a conservative form.

V1 rules:
- show only `20-50` top neurons
- render them as lightweight points / sprites
- do not render full neuron morphologies in V1
- keep ROI glow visually dominant over the neuron point layer

---

## 3. ROI Naming and Explanation

### 3.1 Naming system

ROI naming should use dual-level labels.

In the 3D brain view:
- show only short labels, e.g. `MB`, `FB`, `LAL`

In the explanation panel and tooltips:
- `short label + English full name + Chinese explanation`

Example:
- `MB — Mushroom Body（蘑菇体，学习/整合相关）`

### 3.2 Configuration-driven naming

ROI labels and explanations must be driven by a manifest/config file, not hard-coded inside UI components.

Recommended fields:
- `roi_id`
- `short_label`
- `display_name`
- `display_name_zh`
- `group`
- `description_zh`
- `default_color`
- `priority`

Why:
- easier curation
- easier extension
- cleaner multilingual handling

---

## 4. Brain Visualization Data Layers

V1 brain rendering should consume three data layers.

### 4.1 Shell layer
Static:
- `mesh_id`
- `opacity`
- `base_color`

### 4.2 ROI activity layer
Dynamic per ROI:
- `roi_id`
- `roi_name`
- `activity_value`
- `activity_delta`
- `node_count`

### 4.3 Top-neuron layer
Dynamic per neuron point:
- `node_idx`
- `source_id`
- `x`
- `y`
- `z`
- `activity_value`
- `flow_role`
- `roi_name`

This keeps the UI payload lightweight while preserving interpretability.

---

## 5. Mapping Asset Policy

The project already has dynamic activity values from the whole-brain model.

The missing static asset layers are:
- `node -> ROI（节点到脑区）`
- `node -> 3D position（节点到三维坐标）`

V1 recommendation:
- do not require perfect full-brain geometric coverage
- do require a stable shell + a representative ROI mapping subset + top-neuron point positions
- always surface `mapping coverage（映射覆盖度）` in the UI

This keeps the interface honest and avoids implying complete anatomical coverage where it does not yet exist.

---

## 6. Body Video Visual Style

### 6.1 Target style

The body video should look `stylized but real（有展示感但仍真实）`.

V1 should not aim for a full cinematic kitchen. It should use a `kitchen tabletop stage（厨房桌面实验台）`.

### 6.2 Recommended scene composition

Physical scene elements:
- a real tabletop walking surface
- a backsplash / back wall
- soft warm overhead lighting
- optional edge trim for scale

Decorative reference props:
- a mug silhouette
- a plate / utensil silhouette
- small static references kept visually secondary

### 6.3 Material palette

Recommended V1 style:
- `matte warm neutral tabletop（哑光暖中性桌面）`

Reason:
- kitchen-like without being flashy
- preserves contrast for the fly body
- does not visually compete with the brain panel or overlays

Not recommended for V1:
- glossy white kitchen
- heavy wood grain hero surface
- dense prop clutter
- mirror-like reflections

---

## 7. Video HUD Policy

The body video must not contain brain glow or any suggestion that the brain is literally visible inside the fly video panel.

The brain panel and body panel are synchronized, but visually separate.

### 7.1 HUD philosophy

The video HUD should be a restrained `scientific camera overlay（科学相机叠加层）`, not a game HUD and not a weather app.

The HUD should be implemented with the same design-system rules as the left console:
- restrained use of `shadcn/ui` surface patterns
- low-ornament typography
- clear focus on readability
- overlays weaker than behavior motion itself

### 7.2 HUD layout

Recommended V1 split:

Top strip:
- `Terrain`
- `Friction`
- `Wind`
- `Rain`
- `Temp`
- `Odor`

Bottom-right small status block:
- `step`
- `reward`
- `terminated`

### 7.3 Overlay visibility policy by variable

Visible in-scene effect allowed:
- `Rain（降雨）`: light rain streaks only

HUD-only variables:
- `Wind（风）`
- `Temperature（温度）`
- `Odor（气味）`

Why:
- wind, temperature, and odor are not naturally camera-visible in this stage
- fake visual dramatization would reduce scientific credibility

### 7.4 Things explicitly avoided in V1

- no brain glow inside body video
- no full-screen heat tinting
- no cartoon odor smoke
- no heavy wind particle effects
- no large decorative HUD graphics

---

## 8. Best-Practice Summary

The refined V1 UI should follow this principle:

- the brain panel is structurally grounded in `FlyWire`
- the body panel remains a physically truthful `MuJoCo / dm_control` render
- the brain and body are synchronized by time and causal interpretation
- the body video does not pretend that invisible variables are literally visible
- the interface explains the experiment rather than theatrically exaggerating it
