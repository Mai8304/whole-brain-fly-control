# MuJoCo Fly Page Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a standalone `/mujoco-fly` route that runs a real browser-side `MuJoCo WASM（网页端 MuJoCo 运行时）` fruit-fly simulation, renders it with `Babylon.js（三维引擎）`, and supports orbit/rotate/zoom plus `Start / Pause / Reset / Reset Camera`.

**Architecture:** Keep `MuJoCo` as the sole owner of simulation state and `Babylon` as the sole owner of rendering and camera interaction. Materialize `flybody（果蝇身体与 MuJoCo 模型资源）` assets into `apps/neural-console/public/mujoco-fly/fruitfly/`, then build a dedicated page/runtime stack under `apps/neural-console/src/pages/mujoco-fly/` without reusing the existing `react-three-fiber（React 的 Three.js 3D 渲染层）` brain/body viewport path.

**Tech Stack:** Python asset-prep script, pytest, React, TypeScript, Vite, Vitest, `@mujoco/mujoco`, `@babylonjs/core`, `@babylonjs/loaders`, browser `requestAnimationFrame`.

---

### Task 1: Add a repeatable `flybody` asset-prep script for the new page

**Files:**
- Create: `scripts/prepare_mujoco_fly_assets.py`
- Create: `tests/scripts/test_prepare_mujoco_fly_assets.py`
- Create: `apps/neural-console/public/mujoco-fly/.gitkeep`

**Step 1: Write the failing script test**

Create `tests/scripts/test_prepare_mujoco_fly_assets.py` with a minimal contract:

```python
from pathlib import Path


def test_prepare_mujoco_fly_assets_copies_xml_and_meshes(tmp_path: Path, monkeypatch) -> None:
    from scripts import prepare_mujoco_fly_assets

    source_dir = tmp_path / "flybody_assets"
    source_dir.mkdir(parents=True)
    (source_dir / "fruitfly.xml").write_text('<mujoco><asset/></mujoco>', encoding="utf-8")
    (source_dir / "thorax_body.obj").write_text("o thorax\n", encoding="utf-8")

    monkeypatch.setattr(
        prepare_mujoco_fly_assets,
        "_default_flybody_asset_dir",
        lambda: source_dir,
    )

    output_dir = tmp_path / "public" / "mujoco-fly" / "fruitfly"
    exit_code = prepare_mujoco_fly_assets.main(["--output-dir", str(output_dir), "--json"])

    assert exit_code == 0
    assert (output_dir / "fruitfly.xml").exists()
    assert (output_dir / "assets" / "thorax_body.obj").exists()
    assert (output_dir / "manifest.json").exists()
```

**Step 2: Run the focused script test and verify it fails**

Run:

```bash
PYTHONPATH=src ./.venv-flywire/bin/python -m pytest \
  tests/scripts/test_prepare_mujoco_fly_assets.py \
  -q
```

Expected: FAIL because the script does not exist yet.

**Step 3: Implement the minimal asset-prep script**

Create `scripts/prepare_mujoco_fly_assets.py` with:

- a `_default_flybody_asset_dir()` helper that points to `.venv-flybody/.../flybody/fruitfly/assets`
- a `prepare_mujoco_fly_assets(source_dir: Path, output_dir: Path) -> dict[str, object]`
- a `main(argv: list[str] | None = None) -> int`

Minimal implementation shape:

```python
def prepare_mujoco_fly_assets(source_dir: Path, output_dir: Path) -> dict[str, object]:
    output_dir.mkdir(parents=True, exist_ok=True)
    assets_dir = output_dir / "assets"
    assets_dir.mkdir(parents=True, exist_ok=True)

    shutil.copy2(source_dir / "fruitfly.xml", output_dir / "fruitfly.xml")
    copied = []
    for mesh_path in sorted(source_dir.glob("*.obj")):
        target = assets_dir / mesh_path.name
        shutil.copy2(mesh_path, target)
        copied.append(mesh_path.name)

    manifest = {
        "entry_xml": "fruitfly.xml",
        "mesh_dir": "assets",
        "mesh_count": len(copied),
        "meshes": copied,
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest
```

The script should support:

```bash
python scripts/prepare_mujoco_fly_assets.py --output-dir apps/neural-console/public/mujoco-fly/fruitfly --json
```

**Step 4: Run the script test again and make sure it passes**

Run:

```bash
PYTHONPATH=src ./.venv-flywire/bin/python -m pytest \
  tests/scripts/test_prepare_mujoco_fly_assets.py \
  -q
```

Expected: PASS.

**Step 5: Materialize the checked-in page assets**

Run:

```bash
python scripts/prepare_mujoco_fly_assets.py \
  --output-dir apps/neural-console/public/mujoco-fly/fruitfly \
  --json
```

Expected: `fruitfly.xml`, `assets/*.obj`, and `manifest.json` appear under `apps/neural-console/public/mujoco-fly/fruitfly/`.

**Step 6: Commit**

```bash
git add scripts/prepare_mujoco_fly_assets.py \
  tests/scripts/test_prepare_mujoco_fly_assets.py \
  apps/neural-console/public/mujoco-fly
git commit -m "feat: add mujoco fly asset preparation"
```

---

### Task 2: Add the standalone `/mujoco-fly` route and page shell

**Files:**
- Modify: `apps/neural-console/package.json`
- Modify: `apps/neural-console/src/App.tsx`
- Modify: `apps/neural-console/src/App.test.tsx`
- Modify: `apps/neural-console/src/lib/messages.ts`
- Create: `apps/neural-console/src/pages/mujoco-fly/mujoco-fly-page.tsx`
- Create: `apps/neural-console/src/pages/mujoco-fly/mujoco-fly-page.test.tsx`

**Step 1: Write the failing route test**

Add a new test in `apps/neural-console/src/App.test.tsx`:

```tsx
it('renders the standalone mujoco fly page on /mujoco-fly', async () => {
  vi.spyOn(globalThis, 'fetch').mockRejectedValue(new Error('offline'))
  window.history.replaceState(null, '', '/mujoco-fly')

  render(<App />)

  expect(await screen.findByRole('heading', { name: /mujoco fly/i })).toBeInTheDocument()
  expect(screen.getByTestId('mujoco-fly-page')).toBeInTheDocument()
  expect(screen.queryByRole('heading', { name: /whole-brain fly console/i })).not.toBeInTheDocument()
})
```

Add a focused page-shell test in `apps/neural-console/src/pages/mujoco-fly/mujoco-fly-page.test.tsx`:

```tsx
it('renders the viewport shell and minimal controls', () => {
  render(<MujocoFlyPage />)

  expect(screen.getByTestId('mujoco-fly-page')).toBeInTheDocument()
  expect(screen.getByTestId('mujoco-fly-viewport-shell')).toBeInTheDocument()
  expect(screen.getByRole('button', { name: /start/i })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: /pause/i })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: /reset camera/i })).toBeInTheDocument()
})
```

**Step 2: Run the focused front-end tests and verify they fail**

Run:

```bash
pnpm --dir apps/neural-console exec vitest run \
  src/App.test.tsx \
  src/pages/mujoco-fly/mujoco-fly-page.test.tsx
```

Expected: FAIL because the route and page do not exist yet.

**Step 3: Add route, strings, and minimal page shell**

Implement:

- `apps/neural-console/package.json`
  - add `@babylonjs/core`
  - add `@babylonjs/loaders`
  - add `@mujoco/mujoco`
- `apps/neural-console/src/lib/messages.ts`
  - add keys for page title, status labels, and button labels
- `apps/neural-console/src/pages/mujoco-fly/mujoco-fly-page.tsx`
  - render heading, control rail, status pill, and viewport shell
- `apps/neural-console/src/App.tsx`
  - add a pathname branch for `/mujoco-fly`
  - do not render the existing console toolbar on this route

Minimal route logic:

```tsx
if (currentPage === 'mujoco-fly') {
  return <MujocoFlyPage />
}
```

Update `readPageFromLocation()` to return `'mujoco-fly'` when `window.location.pathname === '/mujoco-fly'`.

**Step 4: Run the focused front-end tests again**

Run:

```bash
pnpm --dir apps/neural-console exec vitest run \
  src/App.test.tsx \
  src/pages/mujoco-fly/mujoco-fly-page.test.tsx
```

Expected: PASS.

**Step 5: Commit**

```bash
git add apps/neural-console/package.json \
  apps/neural-console/src/App.tsx \
  apps/neural-console/src/App.test.tsx \
  apps/neural-console/src/lib/messages.ts \
  apps/neural-console/src/pages/mujoco-fly
git commit -m "feat: add standalone mujoco fly route shell"
```

---

### Task 3: Add a MuJoCo runtime controller with explicit lifecycle states

**Files:**
- Create: `apps/neural-console/src/pages/mujoco-fly/lib/load-mujoco.ts`
- Create: `apps/neural-console/src/pages/mujoco-fly/lib/load-fruitfly-model.ts`
- Create: `apps/neural-console/src/pages/mujoco-fly/lib/mujoco-fly-runtime.ts`
- Create: `apps/neural-console/src/pages/mujoco-fly/lib/mujoco-fly-runtime.test.ts`
- Modify: `apps/neural-console/src/pages/mujoco-fly/mujoco-fly-page.tsx`

**Step 1: Write the failing runtime-state test**

Create `apps/neural-console/src/pages/mujoco-fly/lib/mujoco-fly-runtime.test.ts`:

```ts
import { describe, expect, it, vi } from 'vitest'

import { createMujocoFlyRuntime } from './mujoco-fly-runtime'

describe('createMujocoFlyRuntime', () => {
  it('transitions from loading to paused after bootstrap and toggles running state', async () => {
    const runtime = createMujocoFlyRuntime({
      loadMujoco: vi.fn().mockResolvedValue({ version: 'stub' }),
      loadModelXml: vi.fn().mockResolvedValue('<mujoco/>'),
    })

    expect(runtime.getStatus()).toBe('loading')
    await runtime.bootstrap()
    expect(runtime.getStatus()).toBe('paused')

    runtime.start()
    expect(runtime.getStatus()).toBe('running')

    runtime.pause()
    expect(runtime.getStatus()).toBe('paused')
  })
})
```

**Step 2: Run the focused runtime test and verify it fails**

Run:

```bash
pnpm --dir apps/neural-console exec vitest run \
  src/pages/mujoco-fly/lib/mujoco-fly-runtime.test.ts
```

Expected: FAIL because the runtime module does not exist yet.

**Step 3: Implement the minimal runtime controller**

Create `load-mujoco.ts`:

```ts
import loadMujoco from '@mujoco/mujoco'

export async function loadMujocoModule() {
  return loadMujoco()
}
```

Create `load-fruitfly-model.ts`:

```ts
export async function loadFruitflyXml(): Promise<string> {
  const response = await fetch('/mujoco-fly/fruitfly/fruitfly.xml')
  if (!response.ok) throw new Error(`Failed to load fruitfly.xml: ${response.status}`)
  return response.text()
}
```

Create `mujoco-fly-runtime.ts` with:

- status union:
  - `'loading' | 'paused' | 'running' | 'error'`
- `bootstrap()`
- `start()`
- `pause()`
- `reset()`
- `getStatus()`

Keep the first green implementation simple:

```ts
export function createMujocoFlyRuntime(deps = {
  loadMujoco: loadMujocoModule,
  loadModelXml: loadFruitflyXml,
}) {
  let status: MujocoFlyRuntimeStatus = 'loading'

  return {
    async bootstrap() {
      try {
        await deps.loadMujoco()
        await deps.loadModelXml()
        status = 'paused'
      } catch (error) {
        status = 'error'
        throw error
      }
    },
    start() { if (status !== 'error') status = 'running' },
    pause() { if (status === 'running') status = 'paused' },
    reset() { if (status !== 'error') status = 'paused' },
    getStatus() { return status },
  }
}
```

Wire `MujocoFlyPage` to use this runtime for button enablement and visible status.

**Step 4: Run the runtime tests again**

Run:

```bash
pnpm --dir apps/neural-console exec vitest run \
  src/pages/mujoco-fly/lib/mujoco-fly-runtime.test.ts \
  src/pages/mujoco-fly/mujoco-fly-page.test.tsx
```

Expected: PASS.

**Step 5: Commit**

```bash
git add apps/neural-console/src/pages/mujoco-fly/lib \
  apps/neural-console/src/pages/mujoco-fly/mujoco-fly-page.tsx \
  apps/neural-console/src/pages/mujoco-fly/lib/mujoco-fly-runtime.test.ts \
  apps/neural-console/src/pages/mujoco-fly/mujoco-fly-page.test.tsx
git commit -m "feat: add mujoco fly runtime controller"
```

---

### Task 4: Add the Babylon viewport and camera interaction contract

**Files:**
- Create: `apps/neural-console/src/pages/mujoco-fly/components/mujoco-fly-viewport.tsx`
- Create: `apps/neural-console/src/pages/mujoco-fly/components/mujoco-fly-viewport.test.tsx`
- Create: `apps/neural-console/src/pages/mujoco-fly/lib/babylon-scene.ts`
- Modify: `apps/neural-console/src/pages/mujoco-fly/mujoco-fly-page.tsx`

**Step 1: Write the failing viewport contract test**

Create `apps/neural-console/src/pages/mujoco-fly/components/mujoco-fly-viewport.test.tsx`:

```tsx
import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { MujocoFlyViewport } from './mujoco-fly-viewport'

describe('MujocoFlyViewport', () => {
  it('renders a canvas host and exposes reset-camera wiring', () => {
    const onResetCamera = vi.fn()

    render(
      <MujocoFlyViewport
        status="paused"
        onReady={vi.fn()}
        onError={vi.fn()}
        onResetCameraRef={(reset) => reset()}
      />,
    )

    expect(screen.getByTestId('mujoco-fly-viewport-shell')).toBeInTheDocument()
  })
})
```

**Step 2: Run the focused viewport test and verify it fails**

Run:

```bash
pnpm --dir apps/neural-console exec vitest run \
  src/pages/mujoco-fly/components/mujoco-fly-viewport.test.tsx
```

Expected: FAIL because the viewport component does not exist yet.

**Step 3: Implement the Babylon scene shell**

Create `babylon-scene.ts` with a helper:

```ts
export function createBabylonScene(canvas: HTMLCanvasElement) {
  const engine = new Engine(canvas, true)
  const scene = new Scene(engine)
  const camera = new ArcRotateCamera('fruitfly-camera', 0, 1.2, 220, Vector3.Zero(), scene)
  camera.attachControl(canvas, true)
  camera.lowerRadiusLimit = 40
  camera.upperRadiusLimit = 420

  const hemi = new HemisphericLight('hemi', new Vector3(0, 1, 0), scene)
  hemi.intensity = 0.9

  return {
    engine,
    scene,
    camera,
    resetCamera() {
      camera.setPosition(new Vector3(0, 120, 220))
      camera.setTarget(Vector3.Zero())
    },
    dispose() {
      scene.dispose()
      engine.dispose()
    },
  }
}
```

Create `mujoco-fly-viewport.tsx` so it:

- renders a large canvas container
- creates the Babylon engine/scene in `useEffect`
- exposes a reset-camera callback back to the page shell
- reports boot errors through `onError`

Wire the page so `Reset Camera` calls the viewport’s registered reset handler.

**Step 4: Run the viewport tests again**

Run:

```bash
pnpm --dir apps/neural-console exec vitest run \
  src/pages/mujoco-fly/components/mujoco-fly-viewport.test.tsx \
  src/pages/mujoco-fly/mujoco-fly-page.test.tsx
```

Expected: PASS.

**Step 5: Commit**

```bash
git add apps/neural-console/src/pages/mujoco-fly/components \
  apps/neural-console/src/pages/mujoco-fly/lib/babylon-scene.ts \
  apps/neural-console/src/pages/mujoco-fly/mujoco-fly-page.tsx
git commit -m "feat: add babylon viewport shell for mujoco fly page"
```

---

### Task 5: Connect real `MuJoCo` stepping to Babylon transform sync

**Files:**
- Create: `apps/neural-console/src/pages/mujoco-fly/lib/transform-sync.ts`
- Modify: `apps/neural-console/src/pages/mujoco-fly/lib/mujoco-fly-runtime.ts`
- Modify: `apps/neural-console/src/pages/mujoco-fly/components/mujoco-fly-viewport.tsx`
- Modify: `apps/neural-console/src/pages/mujoco-fly/mujoco-fly-page.tsx`
- Modify: `apps/neural-console/src/pages/mujoco-fly/mujoco-fly-page.test.tsx`

**Step 1: Write the failing integration-facing runtime test**

Extend `apps/neural-console/src/pages/mujoco-fly/lib/mujoco-fly-runtime.test.ts`:

```ts
it('runs a single animation tick only while in running state', async () => {
  const step = vi.fn()
  const sync = vi.fn()
  const render = vi.fn()

  const runtime = createMujocoFlyRuntime({
    loadMujoco: vi.fn().mockResolvedValue({}),
    loadModelXml: vi.fn().mockResolvedValue('<mujoco/>'),
    createSimulation: vi.fn().mockResolvedValue({ step, reset: vi.fn() }),
    syncFrame: sync,
    renderFrame: render,
  })

  await runtime.bootstrap()
  runtime.start()
  runtime.tick()

  expect(step).toHaveBeenCalledTimes(1)
  expect(sync).toHaveBeenCalledTimes(1)
  expect(render).toHaveBeenCalledTimes(1)
})
```

**Step 2: Run the focused test and verify it fails**

Run:

```bash
pnpm --dir apps/neural-console exec vitest run \
  src/pages/mujoco-fly/lib/mujoco-fly-runtime.test.ts
```

Expected: FAIL because tick/sync integration does not exist yet.

**Step 3: Implement minimal MuJoCo-to-Babylon sync**

In `mujoco-fly-runtime.ts`:

- add dependency injection for:
  - `createSimulation`
  - `syncFrame`
  - `renderFrame`
- add `tick()`
- keep `requestAnimationFrame` ownership in the viewport/page layer

Shape:

```ts
tick() {
  if (status !== 'running' || simulation == null) return
  simulation.step()
  deps.syncFrame(simulation)
  deps.renderFrame()
}
```

Create `transform-sync.ts` with a minimal contract:

```ts
export interface MujocoVisualNodeMap {
  sync(): void
}

export function createTransformSync(): MujocoVisualNodeMap {
  return {
    sync() {
      // first green implementation: no-op structure, then replace with real body/geom sync
    },
  }
}
```

In `mujoco-fly-viewport.tsx`:

- wire the page animation loop with `requestAnimationFrame`
- call `runtime.tick()` only while mounted
- keep Babylon render ownership in the viewport

For the first green version, it is acceptable if the fruit fly is loaded and stepped with a basic pose update path, as long as the architecture keeps:

- `MuJoCo` state ownership
- explicit `tick -> sync -> render` ordering

**Step 4: Run the focused front-end tests and the full page suite**

Run:

```bash
pnpm --dir apps/neural-console exec vitest run \
  src/pages/mujoco-fly/lib/mujoco-fly-runtime.test.ts \
  src/pages/mujoco-fly/components/mujoco-fly-viewport.test.tsx \
  src/pages/mujoco-fly/mujoco-fly-page.test.tsx \
  src/App.test.tsx
```

Expected: PASS.

**Step 5: Run build verification**

Run:

```bash
pnpm --dir apps/neural-console build
```

Expected: PASS.

**Step 6: Manual smoke test**

Run the app locally and verify:

```bash
pnpm --dir apps/neural-console dev --host 127.0.0.1 --port 4173
```

Then open `http://127.0.0.1:4173/mujoco-fly` and confirm:

- the page loads the fruit fly
- drag rotates/orbits the view
- scroll zooms
- `Start` produces visible motion
- `Pause` freezes motion
- `Reset` restores the initial pose
- `Reset Camera` restores the default framing

**Step 7: Commit**

```bash
git add apps/neural-console/src/pages/mujoco-fly \
  apps/neural-console/src/App.tsx \
  apps/neural-console/src/App.test.tsx
git commit -m "feat: connect mujoco fly simulation to babylon viewport"
```
