# Console UI Optimization Design

**Goal:** Refine `Experiment Console（实验控制台）` and `Training Console（训练控制台）` so both pages look and behave like one coherent research platform while preserving all existing functionality, data semantics, and scientific guardrails.

**Scope:** UI-only optimization. No functional changes, no backend data-contract changes, no field removals, no new fake data, no mutation of brain or video data paths.

**Design principle:** use `shadcn/ui（组件体系）` more strictly, reduce visual nesting, improve hierarchy, preserve information completeness.

**Design source:** use `ui-ux-pro-max（界面设计技能）` guidance with a `Data-Dense Dashboard` / operations-console direction, but expressed through `shadcn/ui` official component semantics and the repository’s approved theme/i18n system.

**Official component references:**
- [Card](https://ui.shadcn.com/docs/components/card)
- [Button](https://ui.shadcn.com/docs/components/button)
- [Sonner](https://ui.shadcn.com/docs/components/sonner)
- The same rule applies to `Badge / Tabs / Tooltip / Input / Select / Separator`.

---

## 1. Product-Level Objective

The current UI already has the right information, but too much of it is wrapped in custom visual chrome. That makes the site feel heavier than a research console should feel and creates avoidable white space, repeated borders, and card-in-card structures.

The optimization goal is not to redesign the product. It is to:

- preserve every existing page’s role
- preserve all current data semantics
- preserve current scientific strictness
- tighten layout rhythm
- reduce decorative nesting
- increase readability and scan speed
- make `Experiment Console` and `Training Console` feel like two pages of the same site

This work must remain UI-only.

---

## 2. Shared Constraints

### 2.1 Functional constraints

Do not change:
- page responsibilities
- field lists
- runtime data sources
- API semantics
- experiment behavior
- training behavior
- brain-view semantics
- video playback semantics

Do not add:
- fake metrics
- fake panels
- fake status
- new workflow logic

### 2.2 Design-system constraints

Both pages must:
- use `shadcn/ui` for the 2D UI surface
- share one visual system
- share one theme system (`light / dark / system`)
- share one language system (`English / 简体中文 / 繁體中文 / 日本語`)
- use one icon set only: `lucide-react`
- use one tooltip pattern for `(?)` definitions
- use one spacing rhythm
- use one status-color language

### 2.3 Scientific-platform constraints

All unavailable states must remain explicit.
UI optimization must not cause unavailable scientific data to appear complete.
If real brain activity or formal `neuropil（神经纤维区）` truth is unavailable, the UI must still say so clearly.

---

## 3. Page-Level Visual Strategy

### 3.1 Experiment Console

`Experiment Console` should become a more `data-dense live experiment surface（高密度实时实验台）`.

It should:
- compress top-level chrome
- compress left-side control cards
- compress the pipeline strip
- compress auxiliary timeline space
- give more breathing room to the two primary visual outputs:
  - right-top brain shell / brain-view region
  - right-bottom MuJoCo fly video region

It should feel closer to a real-time instrument panel than a hero-style product page.

### 3.2 Training Console

`Training Console` should become a more `structured research workbench（结构化科研工作台）`.

It should:
- reduce repeated containers
- reduce heavy visual wrappers
- keep parameter/state/artifact readability high
- keep raw snapshots and logs easy to inspect
- preserve the three-layer model:
  - primary view
  - expanded inspector
  - raw snapshot / logs

It should feel systematic, inspectable, and restrained.

---

## 4. Structural Cleanup: Reduce Nesting

The biggest visual issue in the current UI is unnecessary nesting.

### 4.1 Current anti-pattern

Examples currently visible include:
- main card
- nested visual shell
- nested content shell
- nested frame
- content

This creates:
- extra border noise
- inflated padding
- wasted height
- excessive white space
- weaker hierarchy

### 4.2 New rule

For both pages:
- one major section = one primary `Card`
- internal grouping should prefer:
  - `Separator`
  - spacing
  - text hierarchy
  - subtle tone shifts
- not more nested bordered containers

In practice:
- avoid card-inside-card unless the inner unit is truly independent
- avoid multi-layer framed video/viewport containers
- avoid duplicate chrome around the same information block

---

## 5. Official shadcn/ui Component Semantics

### 5.1 Card

Use `Card` exactly as the primary section container.

Preferred internal structure:
- `CardHeader`
- `CardContent`
- optional `CardFooter`

Do not build pseudo-cards inside cards unless the nested content is truly a separate artifact.

### 5.2 Button

Use official `Button` variants for:
- primary action
- secondary action
- page switch actions

Do not introduce visually custom button shells that break consistency.

### 5.3 Badge

Use `Badge` only for:
- state
- source
- type
- lineage tag

Do not use badges as paragraph containers or long-callout wrappers.

### 5.4 Tabs

Use `Tabs` only when content actually switches.
Do not use them as decorative navigation chips.

### 5.5 Tooltip

All `(?)` definitions must use one tooltip style.
It must support:
- term label
- definition
- optional source/update/null semantics

### 5.6 Toast / Sonner

Where notifications are used, use official `Sonner`/toast patterns only.
Do not invent a second notification system.

### 5.7 Input / Select

If a field is read-only, the styling should clearly read as read-only.
Do not make every field feel editable.

---

## 6. Color Rules

Use a neutral-first system with restrained accents.

### 6.1 Base surfaces

- page background: neutral
- cards: neutral surface
- borders: subtle neutral contrast

### 6.2 Accent colors

- primary: selection, primary actions, progress
- success/warning/destructive: status only
- brain and video blocks may keep light atmospheric tone, but must remain within the shared site palette

### 6.3 Avoid

- per-section decorative color systems
- multiple competing accent colors
- vivid panel backgrounds without semantic reason

Color should communicate structure and state first.

---

## 7. Spacing Rules

Use one consistent spacing rhythm.

Recommended baseline:
- section-to-section gap: `gap-4`
- card padding: `p-4`
- compact card internal gaps: `gap-2` to `gap-3`
- field row spacing: `gap-2`
- micro spacing: `gap-1` to `gap-1.5`

Page distinction:
- `Experiment Console`: slightly tighter
- `Training Console`: slightly calmer

But both must still sit on the same spacing scale.

---

## 8. Border, Shadow, and Radius Rules

### 8.1 Borders

Use borders as structural guides, not decoration.

Rules:
- one border for a primary card is enough
- prefer separators or spacing for internal grouping
- avoid stacked borders around the same content

### 8.2 Shadows

Use restrained shadow only to separate primary layers.
Avoid stacked glow/shadow effects.

### 8.3 Radius

Use the same radius family site-wide.
Large radius may remain, but must not multiply through unnecessary wrappers.

---

## 9. Typography and Weight Rules

### 9.1 Typography family

Keep the current shared family consistent with the approved site baseline:
- technical accent / code-facing headings may use `Fira Code`
- body and standard labels use `Fira Sans`

### 9.2 Weight hierarchy

Use stable weight roles:
- page title: `font-semibold`
- section title: `font-semibold`
- values: `font-medium`
- body/support text: default weight
- meta labels: smaller size, muted foreground, optional uppercase tracking

Do not solve hierarchy by making everything heavier.

---

## 10. Icon Rules

Use one icon set only:
- `lucide-react`

Icons may be used for:
- action affordance
- status indicator
- structural cues

Do not mix icon families, illustration styles, or emoji-like symbols.

---

## 11. Experiment Console Optimization Targets

### 11.1 Compress

Compress:
- utility/header chrome
- left control cards
- pipeline strip
- timeline block

### 11.2 Relax

Give more space and visual priority to:
- brain viewport
- fly video viewport

### 11.3 Video section cleanup

The fly video section should be simplified into:
- one main `Card`
- one media region
- one side summary region
- one log region

Avoid multi-layer frame-on-frame structure.

---

## 12. Training Console Optimization Targets

### 12.1 Compress

Compress:
- top callout heaviness
- left navigator padding
- repeated card shells

### 12.2 Relax

Keep readability high for:
- parameter groups
- status groups
- inspector fields
- raw logs and snapshots

The page should remain structured and inspectable rather than merely dense.

---

## 13. Success Criteria

The optimization is successful if:
- both pages still expose the same information and behavior as before
- no scientific semantics are weakened
- the experiment page no longer wastes vertical space or stretches sections unnecessarily
- the training page is cleaner without losing completeness
- the UI uses fewer nested shells
- the visual system feels more aligned with official `shadcn/ui` semantics
- theme and localization behavior remains shared across both pages

---

## 14. Non-Goals

This work does not include:
- changing backend contracts
- changing experiment logic
- changing training logic
- adding new features
- changing scientific data flow
- replacing the 3D renderer
- introducing a custom component library outside `shadcn/ui`
