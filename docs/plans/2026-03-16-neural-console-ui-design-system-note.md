# Neural Console UI Design-System Note

**Purpose:** Freeze the V1 `design system（设计系统）` seam for the `neural console（神经控制台）` so implementation stays consistent with the approved console-family design direction.

## Core Stack

- `shadcn/ui（组件体系）` is the default surface system for all 2D UI:
  - cards
  - panels
  - buttons
  - forms
  - tabs
  - logs
  - status blocks
- `react-three-fiber（React 的 Three.js 3D 渲染层）` is reserved for the right-top 3D brain panel.

Do not duplicate a parallel ad-hoc component library for standard controls.

## Visual Direction

The V1 console should look like a restrained `scientific console（科学实验控制台）`, not a generic `SaaS dashboard（软件后台面板）`.

That means:

- strong layout hierarchy
- calm surfaces
- low ornamentation
- clear state feedback
- emphasis colors only where meaning changes

Avoid:

- loud gradients as the main background
- decorative dashboard chrome
- marketing-site hero styling
- component density that overwhelms the brain/body panels

## Color Policy

Use neutral surfaces for the application frame and reserve emphasis colors for:

- pipeline execution state
- ROI activity
- environment overlay cues
- error/warning states

The right-bottom body video remains the motion focus; overlays must stay visually weaker than body behavior itself.

## Component Hierarchy

The page should reflect this hierarchy:

1. run state and pipeline
2. experiment controls
3. synchronized brain/body views
4. explanations and logs

`shadcn/ui` components should be composed to preserve this hierarchy instead of producing a flat wall of cards.

## Interaction States

The design system must make these states explicit:

- `idle（空闲）`
- `pending changes（待应用改动）`
- `applying（正在应用）`
- `running（运行中）`
- `paused（暂停）`
- `error（错误）`

Focus, loading, and disabled states should be visible without relying on color alone.

## Accessibility and Density

The interface should favor:

- readable typography
- consistent spacing
- obvious keyboard focus
- labels that explain whether a control changes:
  - physics
  - sensory input
  - run behavior

No control should imply direct body steering.

## Phase 1 Guardrail

The left console controls experiment conditions only.

It must never present:

- direct action sliders
- per-joint overrides
- body-part steering controls

The design system should reinforce that all visible behavior is model-generated from approved experiment inputs.
