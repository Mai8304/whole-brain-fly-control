import { describe, expect, it, vi } from 'vitest'

import { createMujocoFlyViewerClient } from './mujoco-fly-viewer-client'

function jsonResponse(payload: unknown, init: { ok?: boolean; status?: number } = {}) {
  return Promise.resolve({
    ok: init.ok ?? true,
    status: init.status ?? 200,
    json: async () => payload,
  } as Response)
}

describe('createMujocoFlyViewerClient', () => {
  it('boots into unavailable status without opening a websocket when official runtime is unavailable', async () => {
    const fetchImpl = vi.fn((input: RequestInfo | URL) => {
      const url = String(input)
      if (url.endsWith('/api/mujoco-fly/session')) {
        return jsonResponse({
          available: false,
          status: 'unavailable',
          reason: 'Official walking policy checkpoint is unavailable',
          scene_version: 'flybody-walk-imitation-v1',
        })
      }
      if (url.endsWith('/api/mujoco-fly/state')) {
        return jsonResponse({
          frame_id: 0,
          sim_time: 0,
          running_state: 'unavailable',
          scene_version: 'flybody-walk-imitation-v1',
          body_poses: [],
          reason: 'Official walking policy checkpoint is unavailable',
        })
      }
      throw new Error(`unexpected request: ${url}`)
    })
    const createSocket = vi.fn()
    const client = createMujocoFlyViewerClient({
      fetchImpl,
      createSocket,
    })

    await client.bootstrap()

    expect(client.getStatus()).toBe('unavailable')
    expect(client.getSession()?.available).toBe(false)
    expect(client.getViewerState()?.running_state).toBe('unavailable')
    expect(createSocket).not.toHaveBeenCalled()
  })

  it('opens the state stream for an available runtime and applies streamed body poses', async () => {
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
      if (url.endsWith('/api/mujoco-fly/session')) {
        return jsonResponse({
          available: true,
          status: 'paused',
          reason: null,
          scene_version: 'flybody-walk-imitation-v1',
        })
      }
      if (url.endsWith('/api/mujoco-fly/state')) {
        return jsonResponse({
          frame_id: 1,
          sim_time: 0.1,
          running_state: 'paused',
          scene_version: 'flybody-walk-imitation-v1',
          body_poses: [],
        })
      }
      if (url.endsWith('/api/mujoco-fly/start')) {
        expect(init?.method).toBe('POST')
        return jsonResponse({
          available: true,
          status: 'running',
          reason: null,
          scene_version: 'flybody-walk-imitation-v1',
        })
      }
      throw new Error(`unexpected request: ${url}`)
    })
    const createSocket = vi.fn(() => socket)
    const client = createMujocoFlyViewerClient({
      fetchImpl,
      createSocket,
      websocketUrl: 'ws://test.local/api/mujoco-fly/stream',
    })

    await client.bootstrap()
    await client.start()

    emit('message', {
      frame_id: 2,
      sim_time: 0.2,
      running_state: 'running',
      scene_version: 'flybody-walk-imitation-v1',
      body_poses: [
        {
          body_name: 'walker/thorax',
          position: [0.0, 0.1, 0.2],
          quaternion: [1.0, 0.0, 0.0, 0.0],
        },
      ],
    })

    expect(createSocket).toHaveBeenCalledWith('ws://test.local/api/mujoco-fly/stream')
    expect(client.getStatus()).toBe('running')
    expect(client.getViewerState()?.body_poses[0]?.body_name).toBe('walker/thorax')
  })
})
