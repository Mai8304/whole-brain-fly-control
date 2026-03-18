import { describe, expect, it, vi } from 'vitest'

import {
  buildMujocoFlyOfficialRenderFrameUrl,
  createMujocoFlyOfficialRenderClient,
} from './mujoco-fly-official-render-client'

function jsonResponse(payload: unknown, init: { ok?: boolean; status?: number } = {}) {
  return Promise.resolve({
    ok: init.ok ?? true,
    status: init.status ?? 200,
    json: async () => payload,
  } as Response)
}

describe('createMujocoFlyOfficialRenderClient', () => {
  it('boots from the official render session endpoint and exposes contract-aligned session state', async () => {
    const fetchImpl = vi.fn((input: RequestInfo | URL) => {
      const url = String(input)
      if (url.endsWith('/api/mujoco-fly-official-render/session')) {
        return jsonResponse({
          available: true,
          running_state: 'paused',
          current_camera: 'track',
          checkpoint_loaded: true,
          reason: null,
        })
      }
      throw new Error(`unexpected request: ${url}`)
    })
    const client = createMujocoFlyOfficialRenderClient({ fetchImpl })

    await client.bootstrap()

    expect(client.getStatus()).toBe('paused')
    expect(client.getSession()).toEqual({
      available: true,
      running_state: 'paused',
      current_camera: 'track',
      checkpoint_loaded: true,
      reason: null,
    })
  })

  it('builds official render frame urls with width, height, camera, and cache key', () => {
    expect(
      buildMujocoFlyOfficialRenderFrameUrl({
        width: 1280,
        height: 720,
        camera: 'back',
        cacheKey: '12',
      }),
    ).toBe('/api/mujoco-fly-official-render/frame?width=1280&height=720&camera=back&cache=12')
  })

  it('calls the official render control endpoints and updates the current camera', async () => {
    const fetchImpl = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
      const url = String(input)
      if (url.endsWith('/api/mujoco-fly-official-render/session')) {
        return jsonResponse({
          available: true,
          running_state: 'paused',
          current_camera: 'track',
          checkpoint_loaded: true,
          reason: null,
        })
      }
      if (url.endsWith('/api/mujoco-fly-official-render/start')) {
        expect(init?.method).toBe('POST')
        return jsonResponse({
          available: true,
          running_state: 'running',
          current_camera: 'track',
          checkpoint_loaded: true,
          reason: null,
        })
      }
      if (url.endsWith('/api/mujoco-fly-official-render/pause')) {
        expect(init?.method).toBe('POST')
        return jsonResponse({
          available: true,
          running_state: 'paused',
          current_camera: 'track',
          checkpoint_loaded: true,
          reason: null,
        })
      }
      if (url.endsWith('/api/mujoco-fly-official-render/reset')) {
        expect(init?.method).toBe('POST')
        return jsonResponse({
          available: true,
          running_state: 'paused',
          current_camera: 'track',
          checkpoint_loaded: true,
          reason: null,
        })
      }
      if (url.endsWith('/api/mujoco-fly-official-render/camera')) {
        expect(init?.method).toBe('POST')
        expect(init?.body).toBe(JSON.stringify({ camera: 'back' }))
        return jsonResponse({
          available: true,
          running_state: 'paused',
          current_camera: 'back',
          checkpoint_loaded: true,
          reason: null,
        })
      }
      throw new Error(`unexpected request: ${url}`)
    })
    const client = createMujocoFlyOfficialRenderClient({ fetchImpl })

    await client.bootstrap()
    await client.start()
    await client.pause()
    await client.reset()
    await client.setCameraPreset('back')

    expect(client.getStatus()).toBe('paused')
    expect(client.getSession()?.current_camera).toBe('back')
  })

  it('fails closed into unavailable status when the official runtime is unavailable', async () => {
    const fetchImpl = vi.fn((input: RequestInfo | URL) => {
      const url = String(input)
      if (url.endsWith('/api/mujoco-fly-official-render/session')) {
        return jsonResponse({
          available: false,
          running_state: 'unavailable',
          current_camera: 'track',
          checkpoint_loaded: false,
          reason: 'Official walking policy checkpoint is unavailable',
        })
      }
      throw new Error(`unexpected request: ${url}`)
    })
    const client = createMujocoFlyOfficialRenderClient({ fetchImpl })

    await client.bootstrap()

    expect(client.getStatus()).toBe('unavailable')
    expect(client.getSession()?.available).toBe(false)
    expect(client.getSession()?.reason).toMatch(/checkpoint/i)
  })
})
