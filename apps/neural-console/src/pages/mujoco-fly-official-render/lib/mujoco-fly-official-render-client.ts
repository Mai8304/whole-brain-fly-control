export type MujocoFlyOfficialRenderStatus =
  | 'loading'
  | 'paused'
  | 'running'
  | 'unavailable'
  | 'error'

export type MujocoFlyOfficialRenderCameraPreset = 'track' | 'side' | 'back' | 'top'

export interface MujocoFlyOfficialRenderSessionPayload {
  available: boolean
  running_state: string
  current_camera: MujocoFlyOfficialRenderCameraPreset
  checkpoint_loaded: boolean
  reason: string | null
}

interface CreateMujocoFlyOfficialRenderClientOptions {
  basePath?: string
  fetchImpl?: typeof fetch
}

export interface MujocoFlyOfficialRenderClient {
  bootstrap: () => Promise<void>
  start: () => Promise<void>
  pause: () => Promise<void>
  reset: () => Promise<void>
  setCameraPreset: (camera: MujocoFlyOfficialRenderCameraPreset) => Promise<void>
  fetchFrame: (options: BuildMujocoFlyOfficialRenderFrameUrlOptions) => Promise<Blob>
  dispose: () => void
  subscribe: (listener: () => void) => () => void
  getStatus: () => MujocoFlyOfficialRenderStatus
  getSession: () => MujocoFlyOfficialRenderSessionPayload | null
}

interface BuildMujocoFlyOfficialRenderFrameUrlOptions {
  basePath?: string
  width: number
  height: number
  camera: MujocoFlyOfficialRenderCameraPreset
  cacheKey?: string | number | null
}

export function createMujocoFlyOfficialRenderClient(
  options: CreateMujocoFlyOfficialRenderClientOptions = {},
): MujocoFlyOfficialRenderClient {
  const basePath = options.basePath ?? '/api/mujoco-fly-official-render'
  const fetchImpl = options.fetchImpl ?? fetch

  let status: MujocoFlyOfficialRenderStatus = 'loading'
  let session: MujocoFlyOfficialRenderSessionPayload | null = null
  let bootstrapPromise: Promise<void> | null = null
  let disposed = false
  const listeners = new Set<() => void>()

  const notify = () => {
    for (const listener of listeners) {
      listener()
    }
  }

  const syncStatusFromSession = () => {
    if (!session) {
      status = 'loading'
      return
    }
    if (!session.available || session.running_state === 'unavailable') {
      status = 'unavailable'
      return
    }
    if (session.running_state === 'running') {
      status = 'running'
      return
    }
    if (session.running_state === 'paused') {
      status = 'paused'
      return
    }
    status = 'error'
  }

  const refreshSession = async (url: string, init?: RequestInit) => {
    try {
      session = await requestJson<MujocoFlyOfficialRenderSessionPayload>(fetchImpl, url, init)
      syncStatusFromSession()
      notify()
    } catch (error) {
      status = 'error'
      notify()
      throw error
    }
  }

  return {
    async bootstrap() {
      if (bootstrapPromise) {
        return bootstrapPromise
      }
      bootstrapPromise = refreshSession(`${basePath}/session`)
      return bootstrapPromise
    },
    async start() {
      await refreshSession(`${basePath}/start`, { method: 'POST' })
    },
    async pause() {
      await refreshSession(`${basePath}/pause`, { method: 'POST' })
    },
    async reset() {
      await refreshSession(`${basePath}/reset`, { method: 'POST' })
    },
    async setCameraPreset(camera: MujocoFlyOfficialRenderCameraPreset) {
      await refreshSession(`${basePath}/camera`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ camera }),
      })
    },
    async fetchFrame(options: BuildMujocoFlyOfficialRenderFrameUrlOptions) {
      return requestBlob(
        fetchImpl,
        buildMujocoFlyOfficialRenderFrameUrl({
          ...options,
          basePath,
        }),
      )
    },
    dispose() {
      disposed = true
      listeners.clear()
    },
    subscribe(listener: () => void) {
      listeners.add(listener)
      return () => {
        if (disposed) {
          return
        }
        listeners.delete(listener)
      }
    },
    getStatus() {
      return status
    },
    getSession() {
      return session
    },
  }
}

export function buildMujocoFlyOfficialRenderFrameUrl({
  basePath = '/api/mujoco-fly-official-render',
  width,
  height,
  camera,
  cacheKey,
}: BuildMujocoFlyOfficialRenderFrameUrlOptions) {
  const params = new URLSearchParams()
  params.set('width', String(width))
  params.set('height', String(height))
  params.set('camera', camera)
  if (cacheKey !== undefined && cacheKey !== null) {
    params.set('cache', String(cacheKey))
  }
  return `${basePath}/frame?${params.toString()}`
}

async function requestJson<T>(
  fetchImpl: typeof fetch,
  url: string,
  init?: RequestInit,
): Promise<T> {
  const response = await fetchImpl(url, init)
  if (!response.ok) {
    throw new Error(`${init?.method ?? 'GET'} ${url} failed with ${response.status}`)
  }
  return (await response.json()) as T
}

async function requestBlob(
  fetchImpl: typeof fetch,
  url: string,
  init?: RequestInit,
): Promise<Blob> {
  const response = await fetchImpl(url, init)
  if (!response.ok) {
    throw new Error(`${init?.method ?? 'GET'} ${url} failed with ${response.status}`)
  }
  return response.blob()
}
