export type MujocoFlyBrowserViewerStatus =
  | 'loading'
  | 'paused'
  | 'running'
  | 'unavailable'
  | 'error'

export type MujocoFlyBrowserViewerCameraPreset = 'track' | 'side' | 'back' | 'top'

export interface MujocoFlyBrowserViewerBodyManifestEntry {
  body_name: string
  parent_body_name: string | null
  renderable: boolean
  geom_names: string[]
}

export interface MujocoFlyBrowserViewerGeomManifestEntry {
  geom_name: string
  body_name: string
  mesh_asset: string
  mesh_scale: [number, number, number]
  local_position: [number, number, number]
  local_quaternion: [number, number, number, number]
  material_name: string | null
  material_rgba: [number, number, number, number] | null
  material_specular: number | null
  material_shininess: number | null
}

export interface MujocoFlyBrowserViewerCameraManifestEntry {
  preset: MujocoFlyBrowserViewerCameraPreset
  camera_name: string
  mode: string | null
  position: [number, number, number]
  quaternion: [number, number, number, number] | null
  xyaxes: [number, number, number, number, number, number] | null
  fovy: number | null
}

export interface MujocoFlyBrowserViewerBootstrapPayload {
  scene_version: string
  runtime_mode: string
  entry_xml: string
  checkpoint_loaded: boolean
  default_camera: MujocoFlyBrowserViewerCameraPreset
  camera_presets: MujocoFlyBrowserViewerCameraPreset[]
  camera_manifest: MujocoFlyBrowserViewerCameraManifestEntry[]
  body_manifest: MujocoFlyBrowserViewerBodyManifestEntry[]
  geom_manifest: MujocoFlyBrowserViewerGeomManifestEntry[]
}

export interface MujocoFlyBrowserViewerSessionPayload {
  available: boolean
  running_state: string
  checkpoint_loaded: boolean
  current_camera: MujocoFlyBrowserViewerCameraPreset
  scene_version: string
  reason: string | null
}

export interface MujocoFlyBrowserViewerBodyPose {
  body_name: string
  position: [number, number, number]
  quaternion: [number, number, number, number]
}

export interface MujocoFlyBrowserViewerPosePayload {
  frame_id: number
  sim_time: number
  running_state: string
  current_camera: MujocoFlyBrowserViewerCameraPreset
  scene_version: string
  body_poses: MujocoFlyBrowserViewerBodyPose[]
  reason?: string
}

interface WebSocketLike {
  addEventListener: (type: string, listener: (event: { data?: string }) => void) => void
  close: () => void
}

interface CreateMujocoFlyBrowserViewerClientOptions {
  basePath?: string
  fetchImpl?: typeof fetch
  createSocket?: (url: string) => WebSocketLike
  websocketUrl?: string
}

export interface MujocoFlyBrowserViewerClient {
  bootstrap: () => Promise<void>
  start: () => Promise<void>
  pause: () => Promise<void>
  reset: () => Promise<void>
  dispose: () => void
  subscribe: (listener: () => void) => () => void
  getStatus: () => MujocoFlyBrowserViewerStatus
  getBootstrap: () => MujocoFlyBrowserViewerBootstrapPayload | null
  getSession: () => MujocoFlyBrowserViewerSessionPayload | null
  getViewerState: () => MujocoFlyBrowserViewerPosePayload | null
}

const API_BASE_URL = import.meta.env.VITE_CONSOLE_API_BASE_URL?.trim() ?? ''

export function createMujocoFlyBrowserViewerClient(
  options: CreateMujocoFlyBrowserViewerClientOptions = {},
): MujocoFlyBrowserViewerClient {
  const basePath = options.basePath ?? '/api/mujoco-fly-browser-viewer'
  const fetchImpl = options.fetchImpl ?? fetch
  const createSocket =
    options.createSocket ??
    ((url: string) => new WebSocket(url) as unknown as WebSocketLike)

  let status: MujocoFlyBrowserViewerStatus = 'loading'
  let bootstrapPayload: MujocoFlyBrowserViewerBootstrapPayload | null = null
  let session: MujocoFlyBrowserViewerSessionPayload | null = null
  let viewerState: MujocoFlyBrowserViewerPosePayload | null = null
  let bootstrapPromise: Promise<void> | null = null
  let socket: WebSocketLike | null = null
  let disposed = false
  const listeners = new Set<() => void>()

  const notify = () => {
    for (const listener of listeners) {
      listener()
    }
  }

  const syncStatus = () => {
    const sourceState = viewerState?.running_state ?? session?.running_state ?? 'loading'
    if (sourceState === 'running') {
      status = 'running'
      return
    }
    if (sourceState === 'paused') {
      status = 'paused'
      return
    }
    if (sourceState === 'unavailable') {
      status = 'unavailable'
      return
    }
    if (sourceState === 'error') {
      status = 'error'
      return
    }
    status = 'loading'
  }

  const connectStream = () => {
    if (socket || !session?.available || disposed) {
      return
    }

    const streamUrl = options.websocketUrl ?? buildWebSocketUrl(`${basePath}/stream`)
    socket = createSocket(streamUrl)
    socket.addEventListener('message', (event) => {
      if (!event.data || disposed) {
        return
      }
      viewerState = JSON.parse(event.data) as MujocoFlyBrowserViewerPosePayload
      syncStatus()
      notify()
    })
  }

  const refreshSession = async (url = `${basePath}/session`, init?: RequestInit) => {
    session = await requestJson<MujocoFlyBrowserViewerSessionPayload>(fetchImpl, url, init)
    syncStatus()
    if (session.available) {
      connectStream()
    }
    notify()
  }

  return {
    async bootstrap() {
      if (bootstrapPromise) {
        return bootstrapPromise
      }
      bootstrapPromise = (async () => {
        try {
          bootstrapPayload = await requestJson<MujocoFlyBrowserViewerBootstrapPayload>(
            fetchImpl,
            `${basePath}/bootstrap`,
          )
          await refreshSession()
        } catch (error) {
          status = 'error'
          notify()
          throw error
        }
      })()
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
    dispose() {
      disposed = true
      socket?.close()
      socket = null
      listeners.clear()
    },
    subscribe(listener: () => void) {
      listeners.add(listener)
      return () => {
        listeners.delete(listener)
      }
    },
    getStatus() {
      return status
    },
    getBootstrap() {
      return bootstrapPayload
    },
    getSession() {
      return session
    },
    getViewerState() {
      return viewerState
    },
  }
}

async function requestJson<T>(
  fetchImpl: typeof fetch,
  url: string,
  init?: RequestInit,
): Promise<T> {
  const response = await fetchImpl(resolveUrl(url), init)
  if (!response.ok) {
    throw new Error(`${init?.method ?? 'GET'} ${url} failed with ${response.status}`)
  }
  return (await response.json()) as T
}

function buildWebSocketUrl(path: string) {
  const url = new URL(resolveUrl(path), window.location.origin)
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
  return url.toString()
}

function resolveUrl(path: string): string {
  if (!API_BASE_URL) {
    return path
  }
  return `${API_BASE_URL.replace(/\/$/, '')}${path}`
}
