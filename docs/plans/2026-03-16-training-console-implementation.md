# Training Console Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a `Training Console（训练控制台）` that manages the full local training lifecycle for the fruit fly whole-brain research platform, with strict status semantics, complete artifact lineage, layered inspection, and no fake runtime data.

**Architecture:** Add a training-oriented backend contract that exposes dataset, graph, training, evaluation, and registry state separately from the experiment UI. Extend the frontend with a new console mode that renders lifecycle panels, expanded inspectors, raw snapshots, and stage-specific state machines. Use one shared `shadcn/ui（组件体系）` design system across both consoles, and implement shared theme + localization infrastructure so both pages stay visually and semantically aligned. Keep the implementation aligned with the current repository reality: `IL-only（仅模仿学习）` training, `straight_walking（稳定直行）` end-to-end support, and strict unavailable semantics where formal data does not yet exist.

**Tech Stack:** Python, existing Fruitfly training/evaluation scripts, FastAPI backend surface, React, `shadcn/ui（组件体系）`, TypeScript, Vitest, pytest, shared theme tokens, shared i18n message catalog.

**Design-system source:** Use the persisted console-family design system in:

- `/Users/zhuangwei/Downloads/coding/Fruitfly/design-system/MASTER.md`
- `/Users/zhuangwei/Downloads/coding/Fruitfly/design-system/pages/console-family.md`

---

### Task 1: Define the Training Console backend contract

**Files:**
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/training/console_contract.py`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/training/test_console_contract.py`
- Reference: `/Users/zhuangwei/Downloads/coding/Fruitfly/docs/plans/2026-03-16-training-console-design.md`

**Step 1: Write the failing test**

Write tests that define the minimal contract objects for:

- `DatasetPanelState`
- `GraphPanelState`
- `TrainPanelState`
- `EvalPanelState`
- `RegistryPanelState`
- `TrainingConsolePayload`

Also assert:

- all stage states are explicit strings
- primary fields exist
- nullable fields remain nullable instead of being invented

**Step 2: Run test to verify it fails**

Run:
```bash
./.venv-flywire/bin/python -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/training/test_console_contract.py -q
```

Expected: FAIL because the contract module does not exist yet.

**Step 3: Write minimal implementation**

Implement dataclasses or typed dicts for the training console payload and the five stage panels.

**Step 4: Run test to verify it passes**

Run the targeted test and confirm PASS.

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/training/console_contract.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/training/test_console_contract.py
git commit -m "feat: add training console backend contract"
```

---

### Task 2: Add training-side metadata readers for Data and Graph

**Files:**
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/training/console_metadata.py`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/training/test_console_metadata.py`
- Reference: `/Users/zhuangwei/Downloads/coding/Fruitfly/data/datasets/walking_il/straight_v1.jsonl`
- Reference: `/Users/zhuangwei/Downloads/coding/Fruitfly/outputs/compiled/flywire_public_full_v783`

**Step 1: Write the failing test**

Write tests asserting the metadata helpers can:

- inspect dataset path, sample count, and task fields
- inspect compiled graph directory existence
- read node counts and mask counts where available
- report `missing`, `ready`, `validated`, `compiling`, `inspected`, or `failed` using stage-specific semantics

**Step 2: Run test to verify it fails**

Run the targeted pytest file and confirm failure.

**Step 3: Write minimal implementation**

Implement helpers that:

- read JSONL dataset files
- inspect compiled graph artifact presence
- produce stage-specific state payloads

**Step 4: Run test to verify it passes**

Confirm PASS.

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/training/console_metadata.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/training/test_console_metadata.py
git commit -m "feat: add training console data and graph metadata readers"
```

---

### Task 3: Add training run state extraction

**Files:**
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/training/trainer.py`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/training/console_runs.py`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/training/test_console_runs.py`

**Step 1: Write the failing test**

Write tests asserting run-state extraction can report:

- output run name
- epochs
- batch size
- learning rate
- hidden dim when known
- train status
- current epoch
- last loss
- latest checkpoint path
- started and updated timestamps when available

Also assert that absent runtime data yields `null`/unavailable fields rather than invented values.

**Step 2: Run test to verify it fails**

Run the targeted test and confirm failure.

**Step 3: Write minimal implementation**

Add helpers that inspect training output directories and checkpoints.

Only add trainer-side persistence if necessary and minimal. Prefer reading existing artifact shapes first.

**Step 4: Run test to verify it passes**

Confirm PASS.

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/training/trainer.py /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/training/console_runs.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/training/test_console_runs.py
git commit -m "feat: expose training run state for console"
```

---

### Task 4: Add evaluation artifact extraction for Training Console

**Files:**
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/training/console_eval.py`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/training/test_console_eval.py`
- Reference: `/Users/zhuangwei/Downloads/coding/Fruitfly/outputs/eval/full_graph_straight_v1_video_smoke_v2/summary.json`

**Step 1: Write the failing test**

Write tests asserting evaluation extraction reports:

- checkpoint path
- task variant
- eval status
- steps completed
- `has_nan_action`
- `terminated_early`
- reward / velocity / upright metrics
- summary path
- video path

Also assert:

- `completed` does not imply acceptable behavior quality
- missing eval artifacts remain unavailable

**Step 2: Run test to verify it fails**

Run the targeted test and confirm failure.

**Step 3: Write minimal implementation**

Implement summary readers that map evaluation artifacts into stage-specific UI payloads.

**Step 4: Run test to verify it passes**

Confirm PASS.

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/training/console_eval.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/training/test_console_eval.py
git commit -m "feat: expose eval artifacts for training console"
```

---

### Task 5: Add registry and lineage payload generation

**Files:**
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/training/console_registry.py`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/training/test_console_registry.py`

**Step 1: Write the failing test**

Write tests asserting registry payloads contain:

- run name
- dataset ref
- graph ref
- checkpoint ref
- eval ref
- registration status
- research label
- validation path when available

Also assert that runs are not upgraded to formal labels without explicit evidence.

**Step 2: Run test to verify it fails**

Run the targeted pytest file and confirm failure.

**Step 3: Write minimal implementation**

Implement registry payload builders that join training, evaluation, and validation references without inventing missing lineage.

**Step 4: Run test to verify it passes**

Confirm PASS.

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/training/console_registry.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/training/test_console_registry.py
git commit -m "feat: add training console registry payload"
```

---

### Task 6: Add Training Console API endpoints

**Files:**
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/ui/console_api.py`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/scripts/serve_neural_console_api.py`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_training_console_api.py`

**Step 1: Write the failing test**

Write tests asserting the backend exposes separate endpoints for:

- training console summary payload
- stage-specific stage states
- raw config/status snapshots
- unavailable semantics when artifacts are missing

Also assert that the existing experiment console behavior remains strict and unchanged.

**Step 2: Run test to verify it fails**

Run:
```bash
./.venv-flywire/bin/python -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_training_console_api.py -q
```

Expected: FAIL because the endpoints do not exist yet.

**Step 3: Write minimal implementation**

Add backend routes that serve:

- `training/data`
- `training/graph`
- `training/train`
- `training/eval`
- `training/registry`
- `training/raw`

or a single structured payload plus raw snapshots, as long as the stage boundaries remain explicit.

**Step 4: Run test to verify it passes**

Confirm PASS.

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/ui/console_api.py /Users/zhuangwei/Downloads/coding/Fruitfly/scripts/serve_neural_console_api.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_training_console_api.py
git commit -m "feat: add training console api"
```

---

### Task 7: Define frontend Training Console types and mock payloads

**Files:**
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/types/console.ts`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/data/mockTrainingConsoleData.ts`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/lib/training-console-api.ts`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/hooks/use-training-console-data.ts`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/App.training.test.tsx`

**Step 1: Write the failing test**

Write frontend tests asserting:

- training console types reflect the five stage panels
- strict unavailable states render properly
- no fake values are shown when runtime data is absent

**Step 2: Run test to verify it fails**

Run:
```bash
zsh -lic 'cd /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console && pnpm test -- --run'
```

Expected: FAIL because the new training-console layer is not implemented.

**Step 3: Write minimal implementation**

Add:

- TypeScript types for training console payloads
- API fetch helpers
- hook for loading and shaping training console state
- mock payloads only for explicit development fallback

**Step 4: Run test to verify it passes**

Confirm PASS.

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/types/console.ts /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/data/mockTrainingConsoleData.ts /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/lib/training-console-api.ts /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/hooks/use-training-console-data.ts /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/App.training.test.tsx
git commit -m "feat: add training console frontend data layer"
```

---

### Task 8: Add shared theme and localization infrastructure

**Files:**
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/lib/theme.ts`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/lib/i18n.ts`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/data/messages/en.ts`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/data/messages/zh-Hans.ts`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/data/messages/zh-Hant.ts`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/data/messages/ja.ts`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/theme-language-controls.tsx`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/App.theme-i18n.test.tsx`

**Step 1: Write the failing test**

Write frontend tests asserting:

- the app supports `light`, `dark`, and `system` theme modes
- the app supports `English`, `简体中文`, `繁體中文`, and `日本語`
- the default UI language is `English`
- supported system language detection can override the default
- both consoles read the same theme and language state

**Step 2: Run test to verify it fails**

Run:
```bash
zsh -lic 'cd /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console && pnpm test -- --run'
```

Expected: FAIL because the shared theme/i18n layer does not exist yet.

**Step 3: Write minimal implementation**

Implement:

- shared theme mode state
- shared language state
- supported-language detection with `English` fallback
- message catalogs for the four approved languages
- top-level controls reusable across both consoles

**Step 4: Run test to verify it passes**

Confirm PASS.

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/lib/theme.ts /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/lib/i18n.ts /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/data/messages/en.ts /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/data/messages/zh-Hans.ts /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/data/messages/zh-Hant.ts /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/data/messages/ja.ts /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/theme-language-controls.tsx /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/App.theme-i18n.test.tsx
git commit -m "feat: add shared theme and i18n system"
```

---

### Task 9: Build the Training Console shell UI

**Files:**
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/App.tsx`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/training-console.tsx`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/training-console-inspector.tsx`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/training-console-raw-tabs.tsx`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/training-console-state-flow.tsx`

**Step 1: Write the failing test**

Extend frontend tests to assert the page renders:

- top-level `Experiment Console` / `Training Console` switch
- shared theme/language controls
- five training lifecycle panels
- run navigator
- inspector
- raw snapshot/log tabs

**Step 2: Run test to verify it fails**

Run the training-specific frontend tests and confirm failure.

**Step 3: Write minimal implementation**

Build the `shadcn/ui（组件体系）` shell using the approved layout:

- top tabs
- left run navigator
- center stage workspace
- right inspector
- bottom logs/raw tabs

Keep the component vocabulary and state presentation aligned with the experiment page:

- same card language
- same badge semantics
- same form control tone
- same tooltip pattern
- same theme behavior

Keep the styling restrained and state-heavy, not showy.

Use the approved design-system outputs:

- visual direction: `scientific operations console（科研运维控制台）`
- palette: blue-slate operational neutrals with amber warning accents and green/red validation states
- typography: `Fira Sans` + `Fira Code`

**Step 4: Run test to verify it passes**

Confirm PASS.

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/App.tsx /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/training-console.tsx /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/training-console-inspector.tsx /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/training-console-raw-tabs.tsx /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/training-console-state-flow.tsx
git commit -m "feat: add training console shell ui"
```

---

### Task 10: Add field definitions and tooltip system

**Files:**
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/data/trainingFieldDefinitions.ts`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/training-console.tsx`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/training-console-inspector.tsx`
- Create: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/field-definition-tooltip.tsx`

**Step 1: Write the failing test**

Write tests asserting that:

- key parameters, statuses, and metrics expose `(?)`
- tooltip content follows the approved structure:
  - `Definition`
  - `Source`
  - `Update`
  - `Null semantics`
- obvious file-path fields are not polluted with unnecessary tooltips

**Step 2: Run test to verify it fails**

Run targeted frontend tests and confirm failure.

**Step 3: Write minimal implementation**

Implement:

- centralized field-definition manifest
- reusable tooltip component
- selective application to key fields only

**Step 4: Run test to verify it passes**

Confirm PASS.

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/data/trainingFieldDefinitions.ts /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/field-definition-tooltip.tsx /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/training-console.tsx /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/training-console-inspector.tsx
git commit -m "feat: add training console field definitions"
```

---

### Task 11: Wire Training Console to existing artifact lineage and document it

**Files:**
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/README.md`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/App.tsx`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/ui/console_api.py`
- Test: `/Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_training_console_api.py`

**Step 1: Write the failing test**

Add tests that verify:

- training and experiment consoles can switch without semantic leakage
- checkpoint lineage remains traceable
- experiment console still refuses fake formal brain activity data

**Step 2: Run test to verify it fails**

Run backend and frontend tests and confirm failure.

**Step 3: Write minimal implementation**

Wire:

- shared checkpoint references
- eval artifact references
- training-to-experiment navigation
- experiment-to-training lineage lookup
- shared theme and language controls across both consoles

Update README with:

- current supported training scope
- distinction between training console and experiment console
- current strict-mode limitations
- shared design-system, theme, and localization behavior

**Step 4: Run test to verify it passes**

Run:
```bash
./.venv-flywire/bin/python -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_training_console_api.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_console_api.py -q
zsh -lic 'cd /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console && pnpm test -- --run'
zsh -lic 'cd /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console && pnpm build'
```

Expected: PASS for tests and successful frontend build.

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/README.md /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/App.tsx /Users/zhuangwei/Downloads/coding/Fruitfly/src/fruitfly/ui/console_api.py /Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui/test_training_console_api.py
git commit -m "feat: wire training console lineage into runtime"
```

---

### Task 12: Final verification sweep

**Files:**
- No new files required

**Step 1: Run Python regression**

Run:
```bash
./.venv-flywire/bin/python -m pytest /Users/zhuangwei/Downloads/coding/Fruitfly/tests/training /Users/zhuangwei/Downloads/coding/Fruitfly/tests/ui -q
```

Expected: PASS.

**Step 2: Run frontend tests**

Run:
```bash
zsh -lic 'cd /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console && pnpm test -- --run'
```

Expected: PASS.

**Step 3: Run frontend build**

Run:
```bash
zsh -lic 'cd /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console && pnpm build'
```

Expected: build succeeds, even if chunk-size warnings remain.

**Step 4: Smoke the API**

Run the local API and verify training console unavailable semantics work without fake values.

Example:
```bash
./.venv-flywire/bin/python /Users/zhuangwei/Downloads/coding/Fruitfly/scripts/serve_neural_console_api.py \
  --compiled-graph-dir /Users/zhuangwei/Downloads/coding/Fruitfly/outputs/compiled/flywire_public_full_v783 \
  --eval-dir /Users/zhuangwei/Downloads/coding/Fruitfly/outputs/eval/full_graph_straight_v1_video_smoke_v2 \
  --checkpoint /Users/zhuangwei/Downloads/coding/Fruitfly/outputs/train/full_graph_straight_v1/checkpoints/epoch_0001.pt
```

Then inspect the training endpoints and confirm:

- no fake values
- stage status is explicit
- missing fields remain unavailable

**Step 5: Commit**

```bash
git add -A
git commit -m "feat: complete training console v1"
```
