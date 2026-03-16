# Neural Console UI Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a Phase 1 local neural console UI that lets users configure experiment conditions, watch brain-region activity, and watch flybody rollout behavior in a synchronized interface.

**Architecture:** Add a Python-backed UI layer on top of the existing full-brain evaluation pipeline while fixing the frontend stack to `React（前端框架） + shadcn/ui（组件体系） + react-three-fiber（React 的 Three.js 3D 渲染层）`. Keep the training stack untouched. Use the existing checkpoint loader, policy wrapper, and flybody closed-loop rollout as the execution backend, then expose a read-only brain/body visualization pipeline with a left-side experiment console.

**Tech Stack:** Python, existing Fruitfly core modules, `flybody（果蝇身体与 MuJoCo 物理环境）`, `dm_control（DeepMind 控制环境库）`, React, `shadcn/ui`, `react-three-fiber`, JSON summaries, MP4 artifacts.

---

### Task 1: Freeze the V1 frontend stack and design-system seam

**Files:**
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/docs/plans/2026-03-16-neural-console-ui-design.md`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/docs/plans/2026-03-16-neural-console-ui-runtime-note.md`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/docs/plans/2026-03-16-neural-console-ui-design-system-note.md`

**Step 1: Write down the fixed V1 frontend stack**

Document that the frontend stack is fixed to:
- `React（前端框架）`
- `shadcn/ui（组件体系）`
- `react-three-fiber（React 的 Three.js 3D 渲染层）`

**Step 2: Record the runtime split**

Write a short runtime note that freezes:
- frontend: React + shadcn/ui + react-three-fiber
- backend: existing Python evaluation/control path

**Step 3: Add a UI design-system note**

Create a short design-system note that treats `ui-ux-pro-max（界面设计技能）` guidance as mandatory input for:
- component hierarchy
- visual density
- spacing
- focus/error/loading states
- non-generic console-family presentation

**Step 4: Define the integration seam**

Document that the UI backend consumes only:
- checkpoint path
- compiled graph directory
- environment/sensory parameter bundle
- closed-loop summary and rollout frames/video

**Step 5: Sanity review**

Read both docs and confirm they do not introduce direct action editing or joint controls.

---

### Task 2: Extend closed-loop evaluation output for behavior analysis

**Files:**
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/walking_eval.py`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/scripts/eval_flybody_closed_loop.py`
- Test: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_closed_loop_summary.py`
- Test: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/scripts/test_eval_flybody_closed_loop.py`

**Step 1: Write failing tests for new summary fields**

Add tests for the presence and correctness of:
- `reward_mean`
- `forward_velocity_mean`
- `forward_velocity_std`
- `body_upright_mean`

**Step 2: Run the targeted tests and confirm failure**

Run:
```bash
python3 -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_closed_loop_summary.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/scripts/test_eval_flybody_closed_loop.py -q
```

Expected: FAIL because the new fields do not yet exist.

**Step 3: Implement minimal summary extensions**

Update `summarize_closed_loop_rollout(...)` and the closed-loop script to collect and summarize:
- per-step reward
- per-step forward velocity from `walker/velocimeter`
- per-step uprightness from `walker/world_zaxis`

**Step 4: Re-run targeted tests**

Run the same test command and confirm PASS.

**Step 5: Commit checkpoint**

Stage the modified files and create a commit once green.

---

### Task 3: Add rollout video capture as a first-class evaluation artifact

**Files:**
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/scripts/eval_flybody_closed_loop.py`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/walking_eval.py`
- Test: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/scripts/test_eval_flybody_closed_loop.py`

**Step 1: Write failing tests for video artifact behavior**

Add tests that assert:
- when video saving is enabled, evaluation writes a predictable output video path into the output directory metadata
- failures still preserve `summary.json`

**Step 2: Run tests and confirm failure**

Run the targeted script tests.

**Step 3: Implement minimal video capture**

Capture rollout frames from `environment.physics.render(...)` and write:
- `rollout.mp4`

Also include the saved video path in the summary or sidecar metadata.

**Step 4: Re-run targeted tests**

Confirm PASS.

**Step 5: Manual smoke**

Run one real closed-loop evaluation from `.venv-flybody` and verify both:
- `summary.json`
- `rollout.mp4`

---

### Task 4: Surface neural activity snapshots for the UI backend

**Files:**
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/models/rate_model.py`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/policy_wrapper.py`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/neural_activity.py`
- Test: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_policy_wrapper.py`
- Test: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_neural_activity.py`

**Step 1: Write failing tests for activity export**

Add tests for a helper that converts hidden state into:
- `afferent activity`
- `intrinsic activity`
- `efferent activity`
- `top active nodes`

**Step 2: Run tests and confirm failure**

Run the new evaluation tests.

**Step 3: Implement minimal activity extraction**

Expose a read-only activity snapshot path that derives aggregated values from model state without changing model output semantics.

**Step 4: Re-run tests**

Confirm PASS.

**Step 5: Keep the interface conservative**

Do not expose editable action vectors or editable joint states anywhere in this layer.

---

### Task 5: Define region-level brain visualization data contract

**Files:**
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/brain_view_contract.py`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_brain_view_contract.py`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/docs/plans/2026-03-16-neural-console-ui-design.md`

**Step 1: Write failing tests for a region-aggregated brain view payload**

The payload should contain:
- `view_mode`
- `mapping_coverage`
- `region_activity`
- `top_regions`
- optional `top_nodes`

**Step 2: Run the new tests and confirm failure**

Run the targeted test.

**Step 3: Implement the minimal payload builder**

Create a deterministic function that converts available activity summaries into a brain-view payload suitable for a UI layer.

**Step 4: Re-run tests**

Confirm PASS.

**Step 5: Update design doc with the exact payload shape**

Make the design doc explicit enough that a later UI task can consume the payload without rediscovering structure.

---

### Task 6: Build a read-only console session schema for UI controls

**Files:**
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/console_session.py`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_console_session.py`

**Step 1: Write failing tests for session state**

Define a schema that stores:
- mode
- checkpoint
- task
- environment physics values
- sensory input values
- pending changes
- intervention log entries

**Step 2: Run tests and confirm failure**

Run the new test file.

**Step 3: Implement the minimal session schema**

Build a read-only oriented session object that distinguishes:
- current applied state
- pending state
- read-only action provenance markers

**Step 4: Re-run tests**

Confirm PASS.

**Step 5: Review for scientific guardrails**

Check the schema and tests to ensure the session model never includes direct action editing fields.

---

### Task 7: Add a shared timeline and event log contract

**Files:**
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/evaluation/timeline.py`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/evaluation/test_timeline.py`

**Step 1: Write failing tests for timeline/event payloads**

The timeline should support:
- `step_id`
- event markers
- synchronized references to body and brain views

**Step 2: Run tests and confirm failure**

Run the targeted tests.

**Step 3: Implement the minimal timeline contract**

Build a simple payload generator that UI code can later use to synchronize top-right and bottom-right panels.

**Step 4: Re-run tests**

Confirm PASS.

---

### Task 8: Implement the first local UI shell

**Files:**
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/scripts/neural_console_ui.py`
- Create or Modify: runtime-specific UI files depending on the runtime chosen in Task 1
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/README.md`
- Test: add smoke tests if the chosen runtime allows cheap testing

**Step 1: Start with a minimal shell**

The shell must show:
- left-side console sections
- top pipeline status
- top-right brain summary placeholder from real payloads
- bottom-right body video / summary from real evaluation artifacts

**Step 2: Bind controls to the session model**

Allow edits only to:
- checkpoint
- task
- terrain
- friction
- wind
- rain
- temperature
- odor
- run settings

No direct action editing must exist.

**Step 3: Bind `Apply & Run` to the evaluation backend**

The UI should run the existing evaluation path and then refresh:
- summary
- video
- brain payload
- intervention log

**Step 4: Manual smoke**

Open the UI locally and verify:
- controls render
- evaluation can run
- right-side views update

**Step 5: Update README**

Add a short “How to run the neural console UI” section.

---

### Task 9: Full verification and cleanup

**Files:**
- Review all files touched in Tasks 1-8

**Step 1: Run the full test suite**

```bash
python3 -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests -q
```

Expected: PASS.

**Step 2: Run one real closed-loop evaluation in `.venv-flybody`**

Expected artifacts:
- `summary.json`
- `rollout.mp4`
- behavior metrics present

**Step 3: Run the UI shell manually**

Verify the left controls, top pipeline status, top-right brain explanation area, bottom-right body video area, and intervention log all behave coherently.

**Step 4: Commit**

Create a clear commit for the finished V1 neural console UI foundation.
