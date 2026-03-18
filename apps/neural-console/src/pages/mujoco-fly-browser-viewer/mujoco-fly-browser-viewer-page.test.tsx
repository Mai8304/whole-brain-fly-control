import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ConsolePreferencesProvider } from '@/providers/console-preferences-provider'

import { MujocoFlyBrowserViewerPage } from './mujoco-fly-browser-viewer-page'

const createViewerClientMock = vi.fn()
const resetViewFromViewport = vi.fn()
const setViewPresetFromViewport = vi.fn()

vi.mock('@/pages/mujoco-fly-browser-viewer/components/mujoco-fly-browser-viewer-viewport', () => ({
  MujocoFlyBrowserViewerViewport: ({
    onViewerControlsRef,
  }: {
    onViewerControlsRef: (controls: { resetView: () => void; setViewPreset: (preset: string) => void }) => void
  }) => {
    onViewerControlsRef({
      resetView: resetViewFromViewport,
      setViewPreset: setViewPresetFromViewport,
    })
    return <div data-testid="mujoco-fly-browser-viewer-viewport" />
  },
}))

vi.mock('@/pages/mujoco-fly-browser-viewer/lib/mujoco-fly-browser-viewer-client', () => ({
  createMujocoFlyBrowserViewerClient: (...args: unknown[]) => createViewerClientMock(...args),
}))

function createViewerClientDouble(options: { checkpointLoaded?: boolean; available?: boolean } = {}) {
  const checkpointLoaded = options.checkpointLoaded ?? true
  const available = options.available ?? true
  let status: 'loading' | 'paused' | 'running' | 'unavailable' | 'error' = 'loading'
  let bootstrap = null as null | {
    scene_version: string
    runtime_mode: string
    entry_xml: string
    checkpoint_loaded: boolean
    default_camera: string
    camera_presets: string[]
    body_manifest: Array<{ body_name: string; parent_body_name: string | null }>
    geom_manifest: Array<{
      geom_name: string
      body_name: string
      mesh_asset: string
      mesh_scale: [number, number, number]
    }>
  }
  let session = null as null | {
    available: boolean
    running_state: string
    checkpoint_loaded: boolean
    current_camera: string
    scene_version: string
    reason: string | null
  }
  let viewerState = null as null | {
    frame_id: number
    sim_time: number
    running_state: string
    current_camera: string
    scene_version: string
    body_poses: Array<{ body_name: string; position: number[]; quaternion: number[] }>
  }
  const listeners = new Set<() => void>()
  const emit = () => {
    for (const listener of listeners) {
      listener()
    }
  }

  return {
    client: {
      bootstrap: vi.fn(async () => {
        status = available ? 'paused' : 'unavailable'
        bootstrap = {
          scene_version: 'flybody-walk-imitation-v1',
          runtime_mode: 'official-flybody-browser-viewer',
          entry_xml: 'walk_imitation.xml',
          checkpoint_loaded: checkpointLoaded,
          default_camera: 'track',
          camera_presets: ['track', 'side', 'back', 'top'],
          body_manifest: [
            {
              body_name: 'walker/thorax',
              parent_body_name: 'walker/',
            },
          ],
          geom_manifest: [
            {
              geom_name: 'walker/thorax',
              body_name: 'walker/thorax',
              mesh_asset: '/mujoco-fly/flybody-official-walk/thorax.obj',
              mesh_scale: [0.1, 0.1, 0.1],
            },
          ],
        }
        session = {
          available,
          running_state: available ? 'paused' : 'unavailable',
          checkpoint_loaded: checkpointLoaded,
          current_camera: 'track',
          scene_version: 'flybody-walk-imitation-v1',
          reason: checkpointLoaded ? null : 'Official walking policy checkpoint is unavailable',
        }
        viewerState = available
          ? {
              frame_id: 1,
              sim_time: 0.1,
              running_state: 'paused',
              current_camera: 'track',
              scene_version: 'flybody-walk-imitation-v1',
              body_poses: [],
            }
          : null
        emit()
      }),
      start: vi.fn(async () => {
        status = 'running'
        if (session) {
          session = { ...session, running_state: 'running' }
        }
        if (viewerState) {
          viewerState = { ...viewerState, running_state: 'running' }
        }
        emit()
      }),
      pause: vi.fn(async () => {
        status = 'paused'
        if (session) {
          session = { ...session, running_state: 'paused' }
        }
        if (viewerState) {
          viewerState = { ...viewerState, running_state: 'paused' }
        }
        emit()
      }),
      reset: vi.fn(async () => {
        status = available ? 'paused' : 'unavailable'
        if (session) {
          session = { ...session, running_state: available ? 'paused' : 'unavailable' }
        }
        if (viewerState) {
          viewerState = { ...viewerState, running_state: 'paused' }
        }
        emit()
      }),
      dispose: vi.fn(),
      subscribe: vi.fn((listener: () => void) => {
        listeners.add(listener)
        return () => listeners.delete(listener)
      }),
      getStatus: vi.fn(() => status),
      getBootstrap: vi.fn(() => bootstrap),
      getSession: vi.fn(() => session),
      getViewerState: vi.fn(() => viewerState),
    },
  }
}

describe('MujocoFlyBrowserViewerPage', () => {
  beforeEach(() => {
    createViewerClientMock.mockReset()
    resetViewFromViewport.mockReset()
    setViewPresetFromViewport.mockReset()
  })

  it('renders the official browser viewer page and wires runtime + local viewer controls', async () => {
    const { client } = createViewerClientDouble()
    createViewerClientMock.mockReturnValue(client)
    const user = userEvent.setup()

    render(
      <ConsolePreferencesProvider>
        <MujocoFlyBrowserViewerPage />
      </ConsolePreferencesProvider>,
    )

    await waitFor(() => {
      expect(client.bootstrap).toHaveBeenCalledTimes(1)
      expect(screen.getByRole('button', { name: /start/i })).toBeEnabled()
    })

    expect(
      screen.getByRole('heading', { name: /mujoco fly browser viewer|mujoco 果蝇浏览器观察器/i }),
    ).toBeInTheDocument()
    expect(screen.getByTestId('mujoco-fly-browser-viewer-viewport')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /track/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /side/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /back/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /top/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /reset view/i })).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /start/i }))
    expect(client.start).toHaveBeenCalledTimes(1)

    await user.click(screen.getByRole('button', { name: /pause/i }))
    expect(client.pause).toHaveBeenCalledTimes(1)

    await user.click(screen.getByRole('button', { name: /^reset$/i }))
    expect(client.reset).toHaveBeenCalledTimes(1)

    await user.click(screen.getByRole('button', { name: /reset view/i }))
    expect(resetViewFromViewport).toHaveBeenCalledTimes(1)

    await user.click(screen.getByRole('button', { name: /^side$/i }))
    expect(setViewPresetFromViewport).toHaveBeenCalledWith('side')
  })

  it('keeps the viewer visible but disables start when the official checkpoint is absent', async () => {
    const { client } = createViewerClientDouble({ checkpointLoaded: false })
    createViewerClientMock.mockReturnValue(client)

    render(
      <ConsolePreferencesProvider>
        <MujocoFlyBrowserViewerPage />
      </ConsolePreferencesProvider>,
    )

    await waitFor(() => {
      expect(client.bootstrap).toHaveBeenCalledTimes(1)
    })

    expect(screen.getByTestId('mujoco-fly-browser-viewer-viewport')).toBeInTheDocument()
    expect(screen.getAllByText(/official walking policy checkpoint is unavailable/i).length).toBe(
      2,
    )
    expect(screen.getByRole('button', { name: /start/i })).toBeDisabled()
    expect(screen.getByRole('button', { name: /track/i })).toBeEnabled()
    expect(screen.getByRole('button', { name: /reset view/i })).toBeEnabled()
  })
})
