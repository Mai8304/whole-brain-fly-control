import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ConsolePreferencesProvider } from '@/providers/console-preferences-provider'

import { MujocoFlyPage } from './mujoco-fly-page'

const createViewerClientMock = vi.fn()
const resetCameraFromViewport = vi.fn()

vi.mock('@/pages/mujoco-fly/components/mujoco-fly-viewport', () => ({
  MujocoFlyViewport: ({
    onResetCameraRef,
  }: {
    onResetCameraRef: (callback: () => void) => void
  }) => {
    onResetCameraRef(resetCameraFromViewport)
    return <div data-testid="mujoco-fly-viewport-shell" />
  },
}))

vi.mock('@/pages/mujoco-fly/lib/mujoco-fly-viewer-client', () => ({
  createMujocoFlyViewerClient: (...args: unknown[]) => createViewerClientMock(...args),
}))

type ViewerStatus = 'loading' | 'paused' | 'running' | 'unavailable' | 'error'

function createViewerClientDouble(options: { unavailable?: boolean } = {}) {
  let status: ViewerStatus = 'loading'
  let session = null as null | {
    available: boolean
    status: string
    reason: string | null
    scene_version: string
  }
  let viewerState = null as null | {
    frame_id: number
    sim_time: number
    running_state: string
    scene_version: string
    body_poses: Array<{ body_name: string; position: number[]; quaternion: number[] }>
    reason?: string
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
        if (options.unavailable) {
          status = 'unavailable'
          session = {
            available: false,
            status: 'unavailable',
            reason: 'Official walking policy checkpoint is unavailable',
            scene_version: 'flybody-walk-imitation-v1',
          }
          viewerState = {
            frame_id: 0,
            sim_time: 0,
            running_state: 'unavailable',
            scene_version: 'flybody-walk-imitation-v1',
            body_poses: [],
            reason: 'Official walking policy checkpoint is unavailable',
          }
          emit()
          return
        }

        status = 'paused'
        session = {
          available: true,
          status: 'paused',
          reason: null,
          scene_version: 'flybody-walk-imitation-v1',
        }
        viewerState = {
          frame_id: 1,
          sim_time: 0.1,
          running_state: 'paused',
          scene_version: 'flybody-walk-imitation-v1',
          body_poses: [],
        }
        emit()
      }),
      start: vi.fn(async () => {
        status = 'running'
        if (session) {
          session = { ...session, status: 'running' }
        }
        if (viewerState) {
          viewerState = { ...viewerState, running_state: 'running' }
        }
        emit()
      }),
      pause: vi.fn(async () => {
        status = 'paused'
        if (session) {
          session = { ...session, status: 'paused' }
        }
        if (viewerState) {
          viewerState = { ...viewerState, running_state: 'paused' }
        }
        emit()
      }),
      reset: vi.fn(async () => {
        status = session?.available ? 'paused' : 'unavailable'
        emit()
      }),
      dispose: vi.fn(),
      subscribe: vi.fn((listener: () => void) => {
        listeners.add(listener)
        return () => listeners.delete(listener)
      }),
      getStatus: vi.fn(() => status),
      getSession: vi.fn(() => session),
      getViewerState: vi.fn(() => viewerState),
    },
  }
}

describe('MujocoFlyPage', () => {
  beforeEach(() => {
    createViewerClientMock.mockReset()
    resetCameraFromViewport.mockReset()
  })

  it('renders a strict unavailable state when the official runtime chain is absent', async () => {
    const { client } = createViewerClientDouble({ unavailable: true })
    createViewerClientMock.mockReturnValue(client)

    render(
      <ConsolePreferencesProvider>
        <MujocoFlyPage />
      </ConsolePreferencesProvider>,
    )

    await waitFor(() => {
      expect(client.bootstrap).toHaveBeenCalledTimes(1)
    })

    expect(screen.getByTestId('mujoco-fly-page')).toBeInTheDocument()
    expect(screen.getByTestId('mujoco-fly-viewport-shell')).toBeInTheDocument()
    expect(screen.getByText(/official walking policy checkpoint is unavailable/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /start/i })).toBeDisabled()
    expect(screen.getByRole('button', { name: /pause/i })).toBeDisabled()
    expect(screen.getByRole('button', { name: /^reset$/i })).toBeDisabled()
  })

  it('wires Start, Pause, Reset, and Reset Camera through the viewer client and viewport', async () => {
    const { client } = createViewerClientDouble()
    createViewerClientMock.mockReturnValue(client)
    const user = userEvent.setup()

    render(
      <ConsolePreferencesProvider>
        <MujocoFlyPage />
      </ConsolePreferencesProvider>,
    )

    await waitFor(() => {
      expect(client.bootstrap).toHaveBeenCalledTimes(1)
      expect(screen.getByRole('button', { name: /start/i })).toBeEnabled()
    })

    await user.click(screen.getByRole('button', { name: /start/i }))
    expect(client.start).toHaveBeenCalledTimes(1)
    expect(screen.getByRole('button', { name: /pause/i })).toBeEnabled()

    await user.click(screen.getByRole('button', { name: /pause/i }))
    expect(client.pause).toHaveBeenCalledTimes(1)
    expect(screen.getByRole('button', { name: /start/i })).toBeEnabled()

    await user.click(screen.getByRole('button', { name: /^reset$/i }))
    expect(client.reset).toHaveBeenCalledTimes(1)

    await user.click(screen.getByRole('button', { name: /reset camera/i }))
    expect(resetCameraFromViewport).toHaveBeenCalledTimes(1)
  })
})
