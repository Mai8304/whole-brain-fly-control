# Console UI Optimization Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Refine the existing `Experiment Console（实验控制台）` and `Training Console（训练控制台）` so they follow stricter `shadcn/ui（组件体系）` semantics, reduce unnecessary nesting, improve hierarchy and density, and remain visually unified without changing any functionality or data behavior.

**Architecture:** Treat this as a UI-only refactor. Keep the current data hooks, API contracts, metrics, fields, and runtime semantics intact. Improve layout, spacing, card structure, viewport framing, and status/tooltip presentation by moving closer to official `shadcn/ui` usage and a clearer research-console hierarchy.

**Tech Stack:** React, TypeScript, `shadcn/ui`, `lucide-react`, existing shared theme/i18n provider, Vitest, Vite.

**References:**
- `/Users/zhuangwei/Downloads/coding/Fruitfly/docs/plans/2026-03-16-console-ui-optimization-design.md`
- [Card](https://ui.shadcn.com/docs/components/card)
- [Button](https://ui.shadcn.com/docs/components/button)
- [Sonner](https://ui.shadcn.com/docs/components/sonner)

---

### Task 1: Lock the current no-functional-change boundary with UI regression tests

**Files:**
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/App.test.tsx`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/experiment-console-page.test.tsx`
- Create if needed: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/training-console-page.test.tsx`

**Step 1: Write failing tests**

Add tests that assert:
- home page still renders brain and fly-body sections
- `/training` still renders training console shell
- no page loses existing major sections due to layout cleanup
- experiment layout does not rely on stretched rows for right-side content

**Step 2: Run tests to verify failure**

Run:
```bash
zsh -lic 'cd /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console && pnpm test --run src/App.test.tsx src/components/experiment-console-page.test.tsx src/components/training-console-page.test.tsx'
```

Expected: FAIL on missing assertions or missing structure markers.

**Step 3: Write minimal code support if required**

Add stable `data-testid` markers only where needed for layout regression coverage.

**Step 4: Re-run tests to green**

Confirm targeted tests pass.

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/App.test.tsx /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/experiment-console-page.test.tsx /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/training-console-page.test.tsx
git commit -m "test: lock console ui structure before refinement"
```

---

### Task 2: Reduce Experiment Console header and section nesting

**Files:**
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/console-site-toolbar.tsx`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/console-page-header.tsx`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/experiment-console-page.tsx`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/index.css`

**Step 1: Write the failing test**

Add or extend tests to assert that experiment page retains one primary card per major area and avoids repeated nested framed shells around the same content.

**Step 2: Run the targeted test and watch it fail**

Run the experiment-page test file.

**Step 3: Implement minimal UI changes**

Refactor experiment page so that:
- header chrome remains compact
- each major region uses a primary `Card`
- internal grouping uses spacing and `Separator` more often than nested card-like wrappers
- the brain viewport and fly video areas become visually primary again

**Step 4: Run targeted test**

Confirm PASS.

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/console-site-toolbar.tsx /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/console-page-header.tsx /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/experiment-console-page.tsx /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/index.css
git commit -m "refactor: simplify experiment console shell"
```

---

### Task 3: Simplify the fly video region to official card semantics

**Files:**
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/experiment-console-page.tsx`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/index.css`
- Test: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/experiment-console-page.test.tsx`

**Step 1: Write the failing test**

Add a regression test asserting the fly video region no longer depends on extra nested shell wrappers for layout.

**Step 2: Run the test to verify failure**

Run the targeted test.

**Step 3: Write minimal implementation**

Refactor the fly video area to:
- keep one outer `Card`
- keep one actual media frame
- keep summary/log blocks readable
- reduce inner framed wrapper layers

Do not change HUD data, video source, or summary fields.

**Step 4: Re-run the test**

Confirm PASS.

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/experiment-console-page.tsx /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/index.css /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/experiment-console-page.test.tsx
git commit -m "refactor: simplify fly video region layout"
```

---

### Task 4: Tighten Training Console hierarchy without reducing information

**Files:**
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/training-console-page.tsx`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/index.css`
- Test: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/training-console-page.test.tsx`

**Step 1: Write the failing test**

Add tests asserting training page still includes:
- Data
- Graph
- Train
- Eval
- Registry
- Raw snapshot area

and that the page remains information-complete after reducing visual wrappers.

**Step 2: Run test to verify failure**

Run the targeted test file and confirm failure.

**Step 3: Write minimal implementation**

Refactor training page so that:
- left navigator is visually tighter
- repeated card shells are reduced
- primary sections remain readable
- inspector and raw tabs still expose full information

**Step 4: Re-run the test**

Confirm PASS.

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/training-console-page.tsx /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/index.css /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/training-console-page.test.tsx
git commit -m "refactor: tighten training console hierarchy"
```

---

### Task 5: Normalize spacing, border, and typography tokens

**Files:**
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/index.css`
- Reference: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/experiment-console-page.tsx`
- Reference: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/training-console-page.tsx`

**Step 1: Write the failing test**

If practical, add a small regression test for key layout classes or page snapshots; otherwise define exact class expectations in existing component tests.

**Step 2: Run the test to verify failure**

Run targeted frontend tests.

**Step 3: Write minimal implementation**

Update tokens so that:
- spacing is more consistent
- borders are less repetitive
- shadows are restrained
- typography weights follow a stable hierarchy
- visual emphasis relies more on official component semantics and less on custom nesting

**Step 4: Re-run tests**

Confirm PASS.

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/index.css /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/experiment-console-page.tsx /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/training-console-page.tsx
git commit -m "style: normalize console spacing and hierarchy"
```

---

### Task 6: Standardize icons and definition affordances

**Files:**
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/definition-hint.tsx`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/console-site-toolbar.tsx`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/experiment-console-page.tsx`
- Modify: `/Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/training-console-page.tsx`

**Step 1: Write the failing test**

Add tests asserting `(?)` definition affordances remain visible where required and continue using a single tooltip pattern.

**Step 2: Run test to verify failure**

Run targeted component tests.

**Step 3: Write minimal implementation**

Ensure all new or visible icons come from `lucide-react`, and all definition hints visually align with one tooltip style.

Do not add decorative icon clutter.

**Step 4: Re-run tests**

Confirm PASS.

**Step 5: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/definition-hint.tsx /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/console-site-toolbar.tsx /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/experiment-console-page.tsx /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console/src/components/training-console-page.tsx
git commit -m "refactor: standardize console icon and tooltip affordances"
```

---

### Task 7: Full verification

**Files:**
- Verify only

**Step 1: Run focused frontend tests**

```bash
zsh -lic 'cd /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console && pnpm test --run'
```

Expected: PASS.

**Step 2: Run production build**

```bash
zsh -lic 'cd /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console && pnpm build'
```

Expected: build succeeds. Existing chunk-size warnings may remain unless explicitly addressed.

**Step 3: Manual spot-check**

Open:
- `http://127.0.0.1:5173/`
- `http://127.0.0.1:5173/training`

Verify:
- shared theme/language still works
- experiment page keeps brain and video visible
- training page keeps all five lifecycle sections plus raw snapshots
- no major nested chrome remains around primary regions

**Step 4: Commit**

```bash
git add /Users/zhuangwei/Downloads/coding/Fruitfly/apps/neural-console
git commit -m "refactor: optimize console ui hierarchy"
```
