# Right-Panel Grouped Neuropil Summary Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Align the experiment console right-side brain detail panel with the active grouped 3D neuropil glow by making grouped summary data the default view and moving fine-grained formal neuropil ranking into a collapsed detail section.

**Architecture:** This is a frontend-only UI restructuring that reuses existing backend payloads. The primary section will consume `display_region_activity` and grouped 3D asset metadata, while the secondary collapsible section will preserve the existing fine-grained `top_regions` view for scientific inspection.

**Tech Stack:** React, TypeScript, shadcn/ui cards and disclosure primitives, Vitest, Testing Library

---

### Task 1: Add grouped-summary view helpers and failing tests

**Files:**
- Modify: `apps/neural-console/src/components/experiment-console-page.tsx`
- Modify: `apps/neural-console/src/components/experiment-console-page.test.tsx`
- Test: `apps/neural-console/src/App.test.tsx`

**Step 1: Write the failing test**

Add a test in `apps/neural-console/src/components/experiment-console-page.test.tsx` that renders a brain view containing:

- grouped `display_region_activity` entries such as `AL` and `FB`
- fine-grained `top_regions` entries such as `ME_R`

Assert that the default visible grouped summary shows `AL` / `FB` and does not show the fine-grained formal detail list until expanded.

**Step 2: Run test to verify it fails**

Run:

```bash
pnpm --dir apps/neural-console exec vitest run src/components/experiment-console-page.test.tsx
```

Expected: FAIL because the current panel still renders `brainView.top_regions` as the default summary.

**Step 3: Write minimal implementation**

In `apps/neural-console/src/components/experiment-console-page.tsx`:

- add a helper that sorts `brainView.display_region_activity` by `raw_activity_mass`
- prepare grouped summary rows from that sorted list
- keep the existing fine-grained formatting helper, but stop using it in the default section

**Step 4: Run test to verify it passes**

Run:

```bash
pnpm --dir apps/neural-console exec vitest run src/components/experiment-console-page.test.tsx
```

Expected: PASS

**Step 5: Commit**

```bash
git add apps/neural-console/src/components/experiment-console-page.tsx apps/neural-console/src/components/experiment-console-page.test.tsx
git commit -m "feat: show grouped neuropil summary by default"
```

### Task 2: Add collapsible formal detail section

**Files:**
- Modify: `apps/neural-console/src/components/experiment-console-page.tsx`
- Modify: `apps/neural-console/src/components/experiment-console-page.test.tsx`

**Step 1: Write the failing test**

Add a test that verifies:

- a `Formal Neuropil Detail（正式神经纤维区明细）` section exists
- it is collapsed by default
- expanding it reveals fine-grained `top_regions` entries such as `ME_R`

**Step 2: Run test to verify it fails**

Run:

```bash
pnpm --dir apps/neural-console exec vitest run src/components/experiment-console-page.test.tsx
```

Expected: FAIL because the current UI has no dedicated collapsible formal detail section.

**Step 3: Write minimal implementation**

In `apps/neural-console/src/components/experiment-console-page.tsx`:

- add a lightweight collapsible section for formal detail
- move the existing `brainView.top_regions` rendering into that section
- add a short explanatory note stating that this section is fine-grained formal data and not the grouped 3D layer

Use the project’s existing shadcn/ui-friendly patterns; do not invent a separate mini design system.

**Step 4: Run test to verify it passes**

Run:

```bash
pnpm --dir apps/neural-console exec vitest run src/components/experiment-console-page.test.tsx
```

Expected: PASS

**Step 5: Commit**

```bash
git add apps/neural-console/src/components/experiment-console-page.tsx apps/neural-console/src/components/experiment-console-page.test.tsx
git commit -m "feat: collapse formal neuropil detail in brain panel"
```

### Task 3: Update labels and grouped metric copy

**Files:**
- Modify: `apps/neural-console/src/lib/messages.ts`
- Modify: `apps/neural-console/src/components/experiment-console-page.tsx`
- Modify: `apps/neural-console/src/components/experiment-console-page.test.tsx`
- Test: `apps/neural-console/src/App.test.tsx`

**Step 1: Write the failing test**

Add or extend tests to assert:

- the primary section title reflects grouped activity summary semantics
- the manifest count row is labeled as grouped 3D manifest rather than generic region count
- the grouped summary helper text indicates alignment with the 3D glow layer

**Step 2: Run test to verify it fails**

Run:

```bash
pnpm --dir apps/neural-console exec vitest run src/components/experiment-console-page.test.tsx src/App.test.tsx
```

Expected: FAIL because the current messages still use generic labels such as `Neuropil Explanation` / `区域清单`.

**Step 3: Write minimal implementation**

Update `apps/neural-console/src/lib/messages.ts` and the panel rendering to use copy such as:

- `Neuropil Activity Summary（神经纤维区活动摘要）`
- `与 3D 发光层一致的 8 区分组活动摘要`
- `Formal Neuropil Detail（正式神经纤维区明细）`
- `3D 分组清单`

Keep all supported languages consistent with the repo’s i18n contract.

**Step 4: Run test to verify it passes**

Run:

```bash
pnpm --dir apps/neural-console exec vitest run src/components/experiment-console-page.test.tsx src/App.test.tsx
```

Expected: PASS

**Step 5: Commit**

```bash
git add apps/neural-console/src/lib/messages.ts apps/neural-console/src/components/experiment-console-page.tsx apps/neural-console/src/components/experiment-console-page.test.tsx apps/neural-console/src/App.test.tsx
git commit -m "feat: relabel brain panel for grouped display semantics"
```

### Task 4: Run regression tests and browser smoke

**Files:**
- Modify: none unless a failing regression requires a fix
- Test: `apps/neural-console/src/components/experiment-console-page.test.tsx`
- Test: `apps/neural-console/src/App.test.tsx`
- Test: `apps/neural-console/src/lib/console-api.test.ts`

**Step 1: Run targeted frontend tests**

Run:

```bash
pnpm --dir apps/neural-console exec vitest run src/lib/console-api.test.ts src/components/experiment-console-page.test.tsx src/App.test.tsx
```

Expected: PASS

**Step 2: Run frontend build**

Run:

```bash
pnpm --dir apps/neural-console build
```

Expected: PASS, with at most existing chunk-size warnings

**Step 3: Run browser smoke**

Start the local API and frontend, then open:

```bash
http://127.0.0.1:4173/
```

Verify:

- the 3D viewport still shows grouped glow
- the right-panel primary summary shows grouped ids such as `AL`, `FB`, `GNG`
- the formal fine-grained ids such as `ME_R` are only visible after expanding the formal detail section
- the provenance row remains visible and unchanged

**Step 4: Commit**

If no fixes were needed, no new commit is required for this task. If a regression fix was needed, create a focused follow-up commit describing only that fix.

### Task 5: Optional documentation touch-up

**Files:**
- Modify: `README.md`
- Modify: `docs/sot/flywire-neuron-roster-sot.md`

**Step 1: Decide if docs changed materially**

Only touch docs if the implemented UI wording changes would otherwise leave the README or SoT note misleading.

**Step 2: If needed, add a minimal clarification**

Document that:

- the experiment console right panel defaults to grouped summary semantics
- fine-grained formal neuropil detail remains available in a secondary expanded section

**Step 3: Verify docs diff is minimal**

Run:

```bash
git diff -- README.md docs/sot/flywire-neuron-roster-sot.md
```

Expected: either no diff or a small targeted clarification

**Step 4: Commit**

```bash
git add README.md docs/sot/flywire-neuron-roster-sot.md
git commit -m "docs: clarify grouped and formal brain panel semantics"
```
