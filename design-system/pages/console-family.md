# Console Family Override

This page-specific override applies to the console family only:

- `Experiment Console（实验控制台）`
- `Training Console（训练控制台）`

Use it together with [MASTER.md](/Users/zhuangwei/Downloads/coding/Fruitfly/design-system/MASTER.md).

## Family Distinction

Both consoles share the same design system, but their tonal emphasis differs:

### Experiment Console

- slightly more visual
- still restrained
- supports brain/body observation
- uses the same cards, badges, tooltips, and state colors as Training Console

### Training Console

- more operational
- more metadata-dense
- emphasizes lineage, logs, validation, and raw snapshots
- uses the same cards, badges, tooltips, and state colors as Experiment Console

## Shared Requirements

- same `shadcn/ui（组件体系）` component language
- same theme switcher
- same language switcher
- same tooltip schema
- same state color semantics
- same typography system

## Layout Tone

### Experiment Console

- more panel-based observation surfaces
- strong visual tie between `neuropil（神经纤维区）` view and body view
- avoid making the left-side control column too dense

### Training Console

- stronger emphasis on:
  - stage status
  - structured metadata
  - raw artifact inspection
  - progress and validation

## Status Surface Rules

Use one status-color map:

- running / active: blue-cyan
- pending / unvalidated: amber-orange
- validated / ready: green
- failed / destructive: red
- unavailable / missing: muted slate

Do not invent page-specific color interpretations.

## Typography Override

For this console family:

- section headings: `Fira Code`
- body and labels: `Fira Sans`
- logs, paths, dense metrics: `Fira Code`

This keeps the family visibly technical and consistent.
