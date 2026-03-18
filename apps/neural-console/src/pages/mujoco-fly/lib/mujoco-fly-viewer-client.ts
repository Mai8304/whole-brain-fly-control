export type MujocoFlyViewerStatus = 'loading' | 'paused' | 'running' | 'unavailable' | 'error'

export interface MujocoFlyBodyPose {
  body_name: string
  position: [number, number, number]
  quaternion: [number, number, number, number]
}

export interface MujocoFlyViewerState {
  frame_id: number
  sim_time: number
  running_state: string
  scene_version: string
  body_poses: MujocoFlyBodyPose[]
  reason?: string
}

export interface MujocoFlySessionPayload {
  available: boolean
  status: string
  reason: string | null
  scene_version: string
  scene_dir?: string | null
  policy_checkpoint_path?: string | null
}

interface WebSocketLike {
  addEventListener: (type: string, listener: (event: { data?: string }) => void) => void
  close: () => void
}

interface CreateMujocoFlyViewerClientOptions {
  basePath?: string
  fetchImpl?: typeof fetch
  createSocket?: (url: string) => WebSocketLike
  websocketUrl?: string
}

export interface MujocoFlyViewerClient {
  bootstrap: () => Promise<void>
  start: () => Promise<void>
  pause: () => Promise<void>
  reset: () => Promise<void>
  dispose: () => void
  subscribe: (listener: () => void) => () => void
  getStatus: () => MujocoFlyViewerStatus
  getSession: () => MujocoFlySessionPayload | null
  getViewerState: () => MujocoFlyViewerState | null
}

export function createMujocoFlyViewerClient(
  options: CreateMujocoFlyViewerClientOptions = {},
): MujocoFlyViewerClient {
  const basePath = options.basePath ?? '/api/mujoco-fly'
  const fetchImpl = options.fetchImpl ?? fetch
  const createSocket =
    options.createSocket ??
    ((url: string) => new WebSocket(url) as unknown as WebSocketLike)

  let status: MujocoFlyViewerStatus = 'loading'
  let session: MujocoFlySessionPayload | null = null
  let viewerState: MujocoFlyViewerState | null = null
  let bootstrapPromise: Promise<void> | null = null
  let socket: WebSocketLike | null = null
  let disposed = false
  const listeners = new Set<() => void>()

  const notify = () => {
    for (const listener of listeners) {
      listener()
    }
  }

  const syncStatusFromState = () => {
    const sourceStatus = viewerState?.running_state ?? session?.status ?? 'loading'
    if (sourceStatus === 'running') {
      status = 'running'
      return
    }
    if (sourceStatus === 'paused') {
      status = 'paused'
      return
    }
    if (sourceStatus === 'unavailable') {
      status = 'unavailable'
      return
    }
    if (sourceStatus === 'error') {
      status = 'error'
      return
    }
    status = 'loading'
  }

  const connectStream = () => {
    if (socket || !session?.available) {
      return
    }

    const streamUrl = options.websocketUrl ?? buildWebSocketUrl(`${basePath}/stream`)
    socket = createSocket(streamUrl)
    socket.addEventListener('message', (event) => {
      if (!event.data || disposed) {
        return
      }
      const payload = JSON.parse(event.data) as MujocoFlyViewerState
      viewerState = payload
      syncStatusFromState()
      notify()
    })
  }

  const refreshSessionAndState = async () => {
    session = await requestJson<MujocoFlySessionPayload>(fetchImpl, `${basePath}/session`)
    viewerState = await requestJson<MujocoFlyViewerState>(fetchImpl, `${basePath}/state`)
    syncStatusFromState()
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
          await refreshSessionAndState()
        } catch (_error) {
          status = 'error'
          notify()
          throw _error
        }
      })()
      return bootstrapPromise
    },
    async start() {
      session = await requestJson<MujocoFlySessionPayload>(fetchImpl, `${basePath}/start`, {
        method: 'POST',
      })
      syncStatusFromState()
      if (session.available) {
        connectStream()
      }
      notify()
    },
    async pause() {
      session = await requestJson<MujocoFlySessionPayload>(fetchImpl, `${basePath}/pause`, {
        method: 'POST',
      })
      syncStatusFromState()
      notify()
    },
    async reset() {
      session = await requestJson<MujocoFlySessionPayload>(fetchImpl, `${basePath}/reset`, {
        method: 'POST',
      })
      syncStatusFromState()
      notify()
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
  const response = await fetchImpl(url, init)
  if (!response.ok) {
    throw new Error(`${init?.method ?? 'GET'} ${url} failed with ${response.status}`)
  }
  return (await response.json()) as T
}

function buildWebSocketUrl(path: string) {
  const url = new URL(path, window.location.origin)
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:'
  return url.toString()
}
