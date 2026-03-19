import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { ConsolePreferencesProvider } from '@/providers/console-preferences-provider'

import { MujocoFlyOfficialRenderPage } from './mujoco-fly-official-render-page'

const createOfficialRenderClientMock = vi.fn()

vi.mock('@/pages/mujoco-fly-official-render/components/mujoco-fly-official-render-viewport', () => ({
  MujocoFlyOfficialRenderViewport: ({
    frameSrc,
    status,
    reason,
  }: {
    frameSrc: string | null
    status: string
    reason: string | null
  }) => (
    <div data-testid="mujoco-fly-official-render-viewport">
      <span data-testid="mujoco-fly-official-render-viewport-status">{status}</span>
      <span data-testid="mujoco-fly-official-render-viewport-src">{frameSrc ?? 'no-frame'}</span>
      <span data-testid="mujoco-fly-official-render-viewport-reason">{reason ?? 'no-reason'}</span>
    </div>
  ),
}))

vi.mock('@/pages/mujoco-fly-official-render/lib/mujoco-fly-official-render-client', () => ({
  buildMujocoFlyOfficialRenderFrameUrl: ({
    width,
    height,
    camera,
    cacheKey,
  }: {
    width: number
    height: number
    camera: string
    cacheKey?: string | number | null
  }) =>
    `/api/mujoco-fly-official-render/frame?width=${width}&height=${height}&camera=${camera}&cache=${cacheKey ?? ''}`,
  createMujocoFlyOfficialRenderClient: (...args: unknown[]) => createOfficialRenderClientMock(...args),
}))

function createOfficialRenderClientDouble(options: { unavailable?: boolean } = {}) {
  let status: 'loading' | 'paused' | 'running' | 'unavailable' | 'error' = 'loading'
  let session = null as null | {
    available: boolean
    running_state: string
    current_camera: string
    checkpoint_loaded: boolean
    reason: string | null
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
            running_state: 'unavailable',
            current_camera: 'track',
            checkpoint_loaded: false,
            reason: 'Official walking policy checkpoint is unavailable',
          }
          emit()
          return
        }
        status = 'paused'
        session = {
          available: true,
          running_state: 'paused',
          current_camera: 'track',
          checkpoint_loaded: true,
          reason: null,
        }
        emit()
      }),
      start: vi.fn(async () => {
        status = 'running'
        if (session) {
          session = { ...session, running_state: 'running' }
        }
        emit()
      }),
      pause: vi.fn(async () => {
        status = 'paused'
        if (session) {
          session = { ...session, running_state: 'paused' }
        }
        emit()
      }),
      reset: vi.fn(async () => {
        status = session?.available ? 'paused' : 'unavailable'
        if (session?.available) {
          session = { ...session, running_state: 'paused' }
        }
        emit()
      }),
      setCameraPreset: vi.fn(async (camera: string) => {
        if (session) {
          session = { ...session, current_camera: camera }
        }
        emit()
      }),
      fetchFrame: vi.fn(async () => new Blob(['jpeg'], { type: 'image/jpeg' })),
      dispose: vi.fn(),
      subscribe: vi.fn((listener: () => void) => {
        listeners.add(listener)
        return () => listeners.delete(listener)
      }),
      getStatus: vi.fn(() => status),
      getSession: vi.fn(() => session),
    },
  }
}

function createDeferred<T>() {
  let resolve!: (value: T) => void
  let reject!: (reason?: unknown) => void
  const promise = new Promise<T>((innerResolve, innerReject) => {
    resolve = innerResolve
    reject = innerReject
  })
  return { promise, resolve, reject }
}

describe('MujocoFlyOfficialRenderPage', () => {
  beforeEach(() => {
    createOfficialRenderClientMock.mockReset()
    vi.stubGlobal(
      'URL',
      Object.assign(URL, {
        createObjectURL: vi.fn(() => 'blob:official-render-frame'),
        revokeObjectURL: vi.fn(),
      }),
    )
  })

  it('renders the official render page with contract-aligned session fields and frame surface', async () => {
    const { client } = createOfficialRenderClientDouble()
    createOfficialRenderClientMock.mockReturnValue(client)

    render(
      <ConsolePreferencesProvider>
        <MujocoFlyOfficialRenderPage />
      </ConsolePreferencesProvider>,
    )

    await waitFor(() => {
      expect(client.bootstrap).toHaveBeenCalledTimes(1)
    })

    expect(
      screen.getByRole('heading', { name: /mujoco fly official render/i }),
    ).toBeInTheDocument()
    expect(screen.getByTestId('mujoco-fly-official-render-viewport')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /start/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /pause/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /^reset$/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /track/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /side/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /back/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /top/i })).toBeInTheDocument()
    expect(screen.getByText(/^official render session$/i)).toBeInTheDocument()
    expect(screen.getByText(/session available/i)).toBeInTheDocument()
    expect(screen.getByText(/running state/i)).toBeInTheDocument()
    expect(screen.getByText(/current camera/i)).toBeInTheDocument()
    expect(screen.getByText(/checkpoint loaded/i)).toBeInTheDocument()
    expect(screen.getByText(/^reason$/i)).toBeInTheDocument()
    expect(screen.getAllByText(/^yes$/i).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/^paused$/i).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/^track$/i).length).toBeGreaterThan(0)
    expect(screen.getByText(/^no issue$/i)).toBeInTheDocument()
    await waitFor(() => {
      expect(
        screen.getByTestId('mujoco-fly-official-render-viewport-src'),
      ).toHaveTextContent('blob:official-render-frame')
    })
  })

  it('wires official render controls and camera presets through the client', async () => {
    const { client } = createOfficialRenderClientDouble()
    createOfficialRenderClientMock.mockReturnValue(client)
    const user = userEvent.setup()

    render(
      <ConsolePreferencesProvider>
        <MujocoFlyOfficialRenderPage />
      </ConsolePreferencesProvider>,
    )

    await waitFor(() => {
      expect(client.bootstrap).toHaveBeenCalledTimes(1)
      expect(screen.getByRole('button', { name: /start/i })).toBeEnabled()
    })

    await user.click(screen.getByRole('button', { name: /start/i }))
    expect(client.start).toHaveBeenCalledTimes(1)

    await user.click(screen.getByRole('button', { name: /pause/i }))
    expect(client.pause).toHaveBeenCalledTimes(1)

    await user.click(screen.getByRole('button', { name: /^reset$/i }))
    expect(client.reset).toHaveBeenCalledTimes(1)

    await user.click(screen.getByRole('button', { name: /^back$/i }))
    expect(client.setCameraPreset).toHaveBeenCalledWith('back')
  })

  it('waits for the in-flight frame fetch before sending camera changes', async () => {
    const deferredFrame = createDeferred<Blob>()
    const { client } = createOfficialRenderClientDouble()
    client.fetchFrame.mockImplementation(() => deferredFrame.promise)
    createOfficialRenderClientMock.mockReturnValue(client)
    const user = userEvent.setup()

    render(
      <ConsolePreferencesProvider>
        <MujocoFlyOfficialRenderPage />
      </ConsolePreferencesProvider>,
    )

    await waitFor(() => {
      expect(client.bootstrap).toHaveBeenCalledTimes(1)
      expect(screen.getByRole('button', { name: /start/i })).toBeEnabled()
    })

    await user.click(screen.getByRole('button', { name: /side/i }))
    expect(client.setCameraPreset).not.toHaveBeenCalled()

    deferredFrame.resolve(new Blob(['jpeg'], { type: 'image/jpeg' }))

    await waitFor(() => {
      expect(client.setCameraPreset).toHaveBeenCalledWith('side')
    })
  })

  it('fails closed when the official runtime is unavailable', async () => {
    const { client } = createOfficialRenderClientDouble({ unavailable: true })
    createOfficialRenderClientMock.mockReturnValue(client)

    render(
      <ConsolePreferencesProvider>
        <MujocoFlyOfficialRenderPage />
      </ConsolePreferencesProvider>,
    )

    await waitFor(() => {
      expect(client.bootstrap).toHaveBeenCalledTimes(1)
    })

    expect(screen.getByRole('button', { name: /start/i })).toBeDisabled()
    expect(screen.getByRole('button', { name: /pause/i })).toBeDisabled()
    expect(screen.getByRole('button', { name: /^reset$/i })).toBeDisabled()
    expect(
      screen.getAllByText(/official walking policy checkpoint is unavailable/i).length,
    ).toBeGreaterThan(0)
    expect(screen.getByTestId('mujoco-fly-official-render-viewport-src')).toHaveTextContent('no-frame')
  })
})
