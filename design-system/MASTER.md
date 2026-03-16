# UI/UX Pro Max Design System

Project: Fruitfly Research Console
Source: `ui-ux-pro-max（界面设计技能）` global installation from `nextlevelbuilder/ui-ux-pro-max-skill`

This master file records the approved console-family design baseline for both:

- `Experiment Console（实验控制台）`
- `Training Console（训练控制台）`

The recommendation below is derived from the real upstream skill outputs, interpreted for a research-platform console rather than a marketing landing page.

## Approved Visual Direction

- Product framing from skill output: `Data-Dense Dashboard（高密度数据控制台）`
- Interaction tone from skill output: `operations / monitoring（运维 / 监控）`
- Final interpretation for this project: `scientific operations console（科研运维控制台）`

This means:

- dense but readable information surfaces
- strong emphasis on stage state and artifact lineage
- high contrast, low decorative noise
- audit-first information hierarchy

## Core Principles

- State first, decoration second
- Use consistent status semantics across both consoles
- Keep dense information scannable
- Make logs, lineage, validation, and failures visible
- Preserve a strict distinction between execution state and scientific judgment

## Color Strategy

Use a restrained console palette based on the upstream skill’s `Analytics Dashboard` and `Operations`-style recommendations.

### Light theme

- Primary: `#2563EB`
- Secondary: `#3B82F6`
- Accent / warning: `#F97316`
- Background: `#F8FAFC`
- Foreground: `#1E293B`
- Muted background: `#E9EEF6`
- Muted foreground: `#64748B`
- Border: `#DBEAFE`
- Destructive: `#DC2626`

### Dark theme

- Background base: `#0F172A`
- Card surface: `#1B2336`
- Foreground: `#F8FAFC`
- Muted surface: `#272F42`
- Muted foreground: `#94A3B8`
- Border: `#475569`

### State colors

- Active / running: blue-cyan family
- Warning / pending / not yet validated: amber-orange family
- Validated / good state: green family
- Failed / destructive: red family

Do not use decorative gradients as the main information carrier.

## Typography

Use the upstream skill’s `Dashboard Data` / `Developer Mono` direction:

- Headings: `Fira Code`
- Body: `Fira Sans`
- Dense metrics and logs: `Fira Code`

Why:

- technical and precise tone
- strong support for tables, metrics, and operational UI
- consistent fit for dashboard/admin/control surfaces

Fallback strategy:

- Latin primary: `Fira Sans`, `Fira Code`
- CJK fallback stack should be added in implementation for Simplified Chinese, Traditional Chinese, and Japanese

## Shared shadcn/ui System

Both consoles must use the same `shadcn/ui（组件体系）` primitives for:

- cards
- badges
- tabs
- accordions
- dialogs
- buttons
- tables
- form controls
- tooltips

Rules:

- one badge/status vocabulary across both consoles
- one tooltip schema across both consoles
- one spacing scale across both consoles
- one theme source across both consoles
- one language source across both consoles

## Tooltip System

All meaning-rich fields should use one shared tooltip structure:

- `Definition`
- `Source`
- `Update`
- `Null semantics`

Optional:

- `Unit`

Do not invent different tooltip styles per page.

## Theme Rules

Both consoles must support:

- `light（亮色）`
- `dark（暗色）`
- `system（跟随系统）`

Rules:

- theme state is global
- the two consoles must not diverge in theme behavior
- all badges and state colors must remain accessible in both light and dark themes

## Localization Rules

Both consoles must support:

- `English（英文）`
- `简体中文`
- `繁體中文`
- `日本語（日文）`

Rules:

- default UI language is `English`
- if the system language is supported, follow it
- raw JSON, file paths, and raw logs remain untranslated
- translated UI labels must remain semantically aligned

## Anti-Patterns

- marketing-style hero composition
- glossy glassmorphism over data-heavy surfaces
- mixed component languages between consoles
- success wording that collapses training, evaluation, and formal validation into one label
- visual clutter that hides failure state or lineage state
