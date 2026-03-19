import { describe, expect, it, vi } from 'vitest'

import { createMujocoFlyBrowserViewerClient } from './mujoco-fly-browser-viewer-client'

function jsonResponse(payload: unknown, init: { ok?: boolean; status?: number } = {}) {
  return Promise.resolve({
    ok: init.ok ?? true,
    status: init.status ?? 200,
    json: async () => payload,
  } as Response)
}

describe('createMujocoFlyBrowserViewerClient', () => {
  it('boots from bootstrap and session endpoints and opens the pose stream for an available runtime', async () => {
    const listeners = new Map<string, Set<(event: { data?: string }) => void>>()
    const socket = {
      addEventListener(type: string, listener: (event: { data?: string }) => void) {
        listeners.set(type, (listeners.get(type) ?? new Set()).add(listener))
      },
      close: vi.fn(),
    }
    const emit = (type: string, payload: unknown) => {
      for (const listener of listeners.get(type) ?? []) {
        listener({ data: JSON.stringify(payload) })
      }
    }
    const fetchImpl = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input)
      if (url.endsWith('/api/mujoco-fly-browser-viewer/bootstrap')) {
        return jsonResponse({
          scene_version: 'flybody-walk-imitation-v1',
          runtime_mode: 'official-flybody-browser-viewer',
          entry_xml: 'walk_imitation.xml',
          checkpoint_loaded: true,
          default_camera: 'track',
          camera_presets: ['track', 'side', 'back', 'top'],
          camera_manifest: [],
          ground_manifest: {
            geom_name: 'groundplane',
            size: [8, 8, 0.25],
            material_name: 'groundplane',
            friction: 0.5,
            texture_name: 'groundplane',
            texture_builtin: 'checker',
            texture_rgb1: [0.2, 0.3, 0.4],
            texture_rgb2: [0.1, 0.2, 0.3],
            texture_mark: 'edge',
            texture_markrgb: [0.8, 0.8, 0.8],
            texture_size: [200, 200],
            texrepeat: [2, 2],
            texuniform: true,
            reflectance: 0.2,
          },
          light_manifest: [],
          body_manifest: [
            {
              body_name: 'walker/thorax',
              parent_body_name: 'walker/',
              renderable: true,
              geom_names: ['walker/thorax'],
            },
          ],
          geom_manifest: [
            {
              geom_name: 'walker/thorax',
              body_name: 'walker/thorax',
              mesh_asset: '/mujoco-fly/flybody-official-walk/thorax.obj',
              mesh_scale: [0.1, 0.1, 0.1],
              geom_local_position: [0, 0, 0],
              geom_local_quaternion: [1, 0, 0, 0],
              mesh_local_position: [0, 0, 0],
              mesh_local_quaternion: [1, 0, 0, 0],
              material_name: 'walker/body',
              material_rgba: [0.67, 0.35, 0.14, 1],
              material_specular: 0,
              material_shininess: 0.6,
            },
          ],
        })
      }
      if (url.endsWith('/api/mujoco-fly-browser-viewer/session')) {
        if (init?.method === 'POST') {
          return jsonResponse({
            available: true,
            running_state: 'running',
            checkpoint_loaded: true,
            current_camera: 'track',
            scene_version: 'flybody-walk-imitation-v1',
            reason: null,
          })
        }
        return jsonResponse({
          available: true,
          running_state: 'paused',
          checkpoint_loaded: true,
          current_camera: 'track',
          scene_version: 'flybody-walk-imitation-v1',
          reason: null,
        })
      }
      if (url.endsWith('/api/mujoco-fly-browser-viewer/state')) {
        return jsonResponse({
          frame_id: 1,
          sim_time: 0.1,
          running_state: 'paused',
          current_camera: 'track',
          scene_version: 'flybody-walk-imitation-v1',
          body_poses: [
            {
              body_name: 'walker/thorax',
              position: [0.0, 0.05, 0.15],
              quaternion: [1.0, 0.0, 0.0, 0.0],
            },
          ],
          geom_poses: [
            {
              geom_name: 'walker/thorax',
              position: [0.1, 0.2, 0.3],
              rotation_matrix: [1, 0, 0, 0, 1, 0, 0, 0, 1],
            },
          ],
        })
      }
      if (url.endsWith('/api/mujoco-fly-browser-viewer/start')) {
        expect(init?.method).toBe('POST')
        return jsonResponse({
          available: true,
          running_state: 'running',
          checkpoint_loaded: true,
          current_camera: 'track',
          scene_version: 'flybody-walk-imitation-v1',
          reason: null,
        })
      }
      if (url.endsWith('/api/mujoco-fly-browser-viewer/pause')) {
        expect(init?.method).toBe('POST')
        return jsonResponse({
          available: true,
          running_state: 'paused',
          checkpoint_loaded: true,
          current_camera: 'track',
          scene_version: 'flybody-walk-imitation-v1',
          reason: null,
        })
      }
      if (url.endsWith('/api/mujoco-fly-browser-viewer/reset')) {
        expect(init?.method).toBe('POST')
        return jsonResponse({
          available: true,
          running_state: 'paused',
          checkpoint_loaded: true,
          current_camera: 'track',
          scene_version: 'flybody-walk-imitation-v1',
          reason: null,
        })
      }
      throw new Error(`unexpected request: ${url}`)
    })
    const createSocket = vi.fn(() => socket)
    const client = createMujocoFlyBrowserViewerClient({
      fetchImpl,
      createSocket,
      websocketUrl: 'ws://test.local/api/mujoco-fly-browser-viewer/stream',
    })

    await client.bootstrap()
    await client.start()

    emit('message', {
      frame_id: 2,
      sim_time: 0.2,
      running_state: 'running',
      current_camera: 'track',
      scene_version: 'flybody-walk-imitation-v1',
      body_poses: [
        {
          body_name: 'walker/thorax',
          position: [0.0, 0.1, 0.2],
          quaternion: [1.0, 0.0, 0.0, 0.0],
        },
      ],
      geom_poses: [
        {
          geom_name: 'walker/thorax',
          position: [0.1, 0.2, 0.3],
          rotation_matrix: [1, 0, 0, 0, 1, 0, 0, 0, 1],
        },
      ],
    })

    expect(client.getStatus()).toBe('running')
    expect(client.getBootstrap()?.runtime_mode).toBe('official-flybody-browser-viewer')
    expect(client.getSession()?.checkpoint_loaded).toBe(true)
    expect(client.getViewerState()?.body_poses[0]?.body_name).toBe('walker/thorax')
    expect(client.getViewerState()?.geom_poses[0]?.geom_name).toBe('walker/thorax')
    expect(fetchImpl).toHaveBeenCalledWith('/api/mujoco-fly-browser-viewer/state', {
      cache: 'no-store',
    })
    expect(createSocket).toHaveBeenCalledWith('ws://test.local/api/mujoco-fly-browser-viewer/stream')
  })

  it('disables HTTP caching for bootstrap, session, and state payloads so updated scene assets are not served stale', async () => {
    const fetchImpl = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input)
      expect(init?.cache).toBe('no-store')
      if (url.endsWith('/api/mujoco-fly-browser-viewer/bootstrap')) {
        return jsonResponse({
          scene_version: 'flybody-walk-imitation-v1',
          runtime_mode: 'official-flybody-browser-viewer',
          entry_xml: 'walk_imitation.xml',
          checkpoint_loaded: true,
          default_camera: 'track',
          camera_presets: ['track', 'side', 'back', 'top'],
          camera_manifest: [],
          ground_manifest: null,
          light_manifest: [],
          body_manifest: [],
          geom_manifest: [],
        })
      }
      if (url.endsWith('/api/mujoco-fly-browser-viewer/session')) {
        return jsonResponse({
          available: true,
          running_state: 'paused',
          checkpoint_loaded: true,
          current_camera: 'track',
          scene_version: 'flybody-walk-imitation-v1',
          reason: null,
        })
      }
      if (url.endsWith('/api/mujoco-fly-browser-viewer/state')) {
        return jsonResponse({
          frame_id: 1,
          sim_time: 0,
          running_state: 'paused',
          current_camera: 'track',
          scene_version: 'flybody-walk-imitation-v1',
          body_poses: [],
          geom_poses: [],
        })
      }
      throw new Error(`unexpected request: ${url}`)
    })
    const client = createMujocoFlyBrowserViewerClient({
      fetchImpl,
      createSocket: () => ({
        addEventListener: vi.fn(),
        close: vi.fn(),
      }),
      websocketUrl: 'ws://test.local/api/mujoco-fly-browser-viewer/stream',
    })

    await client.bootstrap()

    expect(fetchImpl).toHaveBeenCalledWith('/api/mujoco-fly-browser-viewer/bootstrap', {
      cache: 'no-store',
    })
    expect(fetchImpl).toHaveBeenCalledWith('/api/mujoco-fly-browser-viewer/session', {
      cache: 'no-store',
    })
    expect(fetchImpl).toHaveBeenCalledWith('/api/mujoco-fly-browser-viewer/state', {
      cache: 'no-store',
    })
  })

  it('keeps the viewer available but start-disabled when the official checkpoint is absent', async () => {
    const fetchImpl = vi.fn((input: RequestInfo | URL) => {
      const url = String(input)
      if (url.endsWith('/api/mujoco-fly-browser-viewer/bootstrap')) {
        return jsonResponse({
          scene_version: 'flybody-walk-imitation-v1',
          runtime_mode: 'official-flybody-browser-viewer',
          entry_xml: 'walk_imitation.xml',
          checkpoint_loaded: false,
          default_camera: 'track',
          camera_presets: ['track', 'side', 'back', 'top'],
          camera_manifest: [],
          ground_manifest: {
            geom_name: 'groundplane',
            size: [8, 8, 0.25],
            material_name: 'groundplane',
            friction: 0.5,
            texture_name: 'groundplane',
            texture_builtin: 'checker',
            texture_rgb1: [0.2, 0.3, 0.4],
            texture_rgb2: [0.1, 0.2, 0.3],
            texture_mark: 'edge',
            texture_markrgb: [0.8, 0.8, 0.8],
            texture_size: [200, 200],
            texrepeat: [2, 2],
            texuniform: true,
            reflectance: 0.2,
          },
          light_manifest: [],
          body_manifest: [],
          geom_manifest: [],
        })
      }
      if (url.endsWith('/api/mujoco-fly-browser-viewer/session')) {
        return jsonResponse({
          available: true,
          running_state: 'paused',
          checkpoint_loaded: false,
          current_camera: 'track',
          scene_version: 'flybody-walk-imitation-v1',
          reason: 'Official walking policy checkpoint is unavailable',
        })
      }
      if (url.endsWith('/api/mujoco-fly-browser-viewer/state')) {
        return jsonResponse({
          frame_id: 1,
          sim_time: 0,
          running_state: 'paused',
          current_camera: 'track',
          scene_version: 'flybody-walk-imitation-v1',
          body_poses: [],
          geom_poses: [],
          reason: 'Official walking policy checkpoint is unavailable',
        })
      }
      throw new Error(`unexpected request: ${url}`)
    })
    const createSocket = vi.fn(() => ({
      addEventListener: vi.fn(),
      close: vi.fn(),
    }))
    const client = createMujocoFlyBrowserViewerClient({
      fetchImpl,
      createSocket,
      websocketUrl: 'ws://test.local/api/mujoco-fly-browser-viewer/stream',
    })

    await client.bootstrap()

    expect(client.getStatus()).toBe('paused')
    expect(client.getSession()?.available).toBe(true)
    expect(client.getSession()?.checkpoint_loaded).toBe(false)
    expect(client.getSession()?.reason).toMatch(/checkpoint/i)
    expect(createSocket).toHaveBeenCalledTimes(1)
  })

  it('calls pause and reset control endpoints and closes the socket on dispose', async () => {
    const socket = {
      addEventListener: vi.fn(),
      close: vi.fn(),
    }
    const fetchImpl = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input)
      if (url.endsWith('/api/mujoco-fly-browser-viewer/bootstrap')) {
        return jsonResponse({
          scene_version: 'flybody-walk-imitation-v1',
          runtime_mode: 'official-flybody-browser-viewer',
          entry_xml: 'walk_imitation.xml',
          checkpoint_loaded: true,
          default_camera: 'track',
          camera_presets: ['track', 'side', 'back', 'top'],
          camera_manifest: [],
          ground_manifest: {
            geom_name: 'groundplane',
            size: [8, 8, 0.25],
            material_name: 'groundplane',
            friction: 0.5,
            texture_name: 'groundplane',
            texture_builtin: 'checker',
            texture_rgb1: [0.2, 0.3, 0.4],
            texture_rgb2: [0.1, 0.2, 0.3],
            texture_mark: 'edge',
            texture_markrgb: [0.8, 0.8, 0.8],
            texture_size: [200, 200],
            texrepeat: [2, 2],
            texuniform: true,
            reflectance: 0.2,
          },
          light_manifest: [],
          body_manifest: [],
          geom_manifest: [],
        })
      }
      if (url.endsWith('/api/mujoco-fly-browser-viewer/session')) {
        return jsonResponse({
          available: true,
          running_state: 'paused',
          checkpoint_loaded: true,
          current_camera: 'track',
          scene_version: 'flybody-walk-imitation-v1',
          reason: null,
        })
      }
      if (url.endsWith('/api/mujoco-fly-browser-viewer/state')) {
        return jsonResponse({
          frame_id: 1,
          sim_time: 0.1,
          running_state: 'paused',
          current_camera: 'track',
          scene_version: 'flybody-walk-imitation-v1',
          body_poses: [],
          geom_poses: [],
        })
      }
      if (url.endsWith('/api/mujoco-fly-browser-viewer/pause')) {
        expect(init?.method).toBe('POST')
        return jsonResponse({
          available: true,
          running_state: 'paused',
          checkpoint_loaded: true,
          current_camera: 'track',
          scene_version: 'flybody-walk-imitation-v1',
          reason: null,
        })
      }
      if (url.endsWith('/api/mujoco-fly-browser-viewer/reset')) {
        expect(init?.method).toBe('POST')
        return jsonResponse({
          available: true,
          running_state: 'paused',
          checkpoint_loaded: true,
          current_camera: 'track',
          scene_version: 'flybody-walk-imitation-v1',
          reason: null,
        })
      }
      throw new Error(`unexpected request: ${url}`)
    })
    const client = createMujocoFlyBrowserViewerClient({
      fetchImpl,
      createSocket: vi.fn(() => socket),
      websocketUrl: 'ws://test.local/api/mujoco-fly-browser-viewer/stream',
    })

    await client.bootstrap()
    await client.pause()
    await client.reset()
    client.dispose()

    expect(socket.close).toHaveBeenCalledTimes(1)
  })
})
