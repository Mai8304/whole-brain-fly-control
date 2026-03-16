# Neural Console UI Refinement Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refine the neural console UI implementation so the brain view uses a FlyWire-first shell/ROI/top-neuron model and the body video uses a kitchen-tabletop presentation with restrained scientific HUD overlays.

**Architecture:** Keep the base UI architecture from the existing neural console plan. Add a brain asset manifest layer, a conservative ROI/top-neuron payload path, and a refined body-video presentation policy that cleanly separates physical rendering from overlay information. The frontend remains fixed to `React（前端框架） + shadcn/ui（组件体系） + react-three-fiber（React 的 Three.js 3D 渲染层）`.

**Tech Stack:** Existing Fruitfly Python stack, React, `shadcn/ui`, `react-three-fiber`, `FlyWire（果蝇连接组平台）`-aligned brain assets, `MuJoCo（物理引擎）` / `dm_control（DeepMind 控制环境库）` body rendering, JSON manifests, video artifacts.

---

### Task 1: Add a brain asset manifest contract

**Files:**
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/brain_asset_manifest.py`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_brain_asset_manifest.py`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/docs/plans/2026-03-16-neural-console-ui-refinement-design.md`

**Step 1: Write the failing test**

Write a test for a manifest loader that validates:
- `roi_id`
- `short_label`
- `display_name`
- `display_name_zh`
- `group`
- `description_zh`
- `default_color`
- `priority`

**Step 2: Run test to verify it fails**

Run:
```bash
python3 -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_brain_asset_manifest.py -q
```

Expected: FAIL because the module does not exist yet.

**Step 3: Write minimal implementation**

Implement a minimal manifest contract and loader for ROI metadata.

**Step 4: Run test to verify it passes**

Re-run the targeted test and confirm PASS.

---

### Task 2: Refine the brain view payload for shell + ROI + top-neuron layering

**Files:**
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/brain_view_contract.py`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_brain_view_refined_contract.py`

**Step 1: Write the failing test**

Write tests asserting that the payload distinguishes:
- `shell`
- `roi_activity`
- `top_neurons`
- `mapping_coverage`
- `view_mode`

**Step 2: Run test to verify it fails**

Run the targeted test and confirm failure.

**Step 3: Write minimal implementation**

Refine the payload contract so UI code can render the shell, ROI glow, and top-neuron layer independently.

**Step 4: Run test to verify it passes**

Confirm PASS.

---

### Task 3: Add ROI selection policy for V1 representative regions

**Files:**
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/roi_selection.py`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_roi_selection.py`

**Step 1: Write the failing test**

Test that ROI selection supports:
- `input-associated`
- `core-processing`
- `output-associated`
- bounded V1 ROI count

**Step 2: Run test to verify it fails**

Run the new test.

**Step 3: Write minimal implementation**

Implement a deterministic selector that can filter or rank candidate ROIs into the three V1 groups.

**Step 4: Run test to verify it passes**

Confirm PASS.

---

### Task 4: Add body video HUD metadata contract

**Files:**
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/video_hud.py`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_video_hud.py`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/scripts/eval_flybody_closed_loop.py`

**Step 1: Write the failing test**

Add tests for a HUD payload that splits:
- top-strip environment values
- bottom-right runtime status values
- visible in-scene effect flags (rain only)

**Step 2: Run test to verify it fails**

Run the targeted test and confirm failure.

**Step 3: Write minimal implementation**

Implement the minimal HUD metadata builder and include it in evaluation outputs.

**Step 4: Run test to verify it passes**

Confirm PASS.

---

### Task 5: Encode the kitchen-tabletop presentation policy

**Files:**
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/video_scene_policy.py`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_video_scene_policy.py`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/docs/plans/2026-03-16-neural-console-ui-refinement-design.md`

**Step 1: Write the failing test**

Test that the scene policy exposes:
- tabletop style name
- material palette
- camera choices
- allowed decorative props
- forbidden V1 scene features

**Step 2: Run test to verify it fails**

Run the targeted test and confirm failure.

**Step 3: Write minimal implementation**

Implement a simple scene-style contract that the UI or rendering layer can reference without adding direct rendering complexity now.

**Step 4: Run test to verify it passes**

Confirm PASS.

---

### Task 6: Thread the refined metadata into the UI-facing backend path

**Files:**
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/__init__.py`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/scripts/neural_console_ui.py` or the eventual runtime entry if already created
- Test: add or modify a small backend-facing integration test as needed

**Step 1: Write the failing test**

Write a test that verifies the UI-facing layer can surface:
- refined brain-view payload
- ROI manifest-backed labels
- refined HUD metadata

**Step 2: Run test to verify it fails**

Run the targeted integration test and confirm failure.

**Step 3: Write minimal implementation**

Thread the metadata builders into the UI-facing backend layer.

The UI-facing layer should assume:
- 2D controls and panels are rendered with `shadcn/ui`
- 3D brain rendering is isolated to the `react-three-fiber` layer
- visual design follows the repository UI design-system note rather than ad-hoc component styling

**Step 4: Run test to verify it passes**

Confirm PASS.

---

### Task 7: Verification and documentation pass

**Files:**
- Review all files touched in Tasks 1-6
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/README.md`

**Step 1: Run the relevant refined test set**

```bash
python3 -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation -q
```

Expected: PASS.

**Step 2: Run the full suite**

```bash
python3 -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests -q
```

Expected: PASS.

**Step 3: Update README**

Add a short note explaining:
- brain view uses FlyWire-first shell/ROI/top-neuron layering
- body video uses restrained kitchen-tabletop styling and scientific HUD overlays

**Step 4: Commit**

Create a focused commit once tests are green.
