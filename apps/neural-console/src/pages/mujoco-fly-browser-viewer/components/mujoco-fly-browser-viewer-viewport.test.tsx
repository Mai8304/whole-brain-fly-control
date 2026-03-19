import { render, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import type {
  MujocoFlyBrowserViewerBootstrapPayload,
  MujocoFlyBrowserViewerPosePayload,
} from '../lib/mujoco-fly-browser-viewer-client'
import { MujocoFlyBrowserViewerViewport } from './mujoco-fly-browser-viewer-viewport'

const createSceneMock = vi.fn()
const applyPoseMock = vi.fn()
const resetViewMock = vi.fn()
const setViewPresetMock = vi.fn()
const disposeMock = vi.fn()

type MockSceneHandle = {
  applyPoseFrame: typeof applyPoseMock
  resetView: typeof resetViewMock
  setViewPreset: typeof setViewPresetMock
  dispose: typeof disposeMock
}

vi.mock('@/pages/mujoco-fly-browser-viewer/lib/babylon-scene', () => ({
  createMujocoFlyBrowserViewerScene: (...args: unknown[]) => createSceneMock(...args),
}))

const bootstrapPayload: MujocoFlyBrowserViewerBootstrapPayload = {
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
    material_rgba: [1, 1, 1, 1],
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
}

const posePayload: MujocoFlyBrowserViewerPosePayload = {
  frame_id: 1,
  sim_time: 0.1,
  running_state: 'paused',
  current_camera: 'track',
  scene_version: 'flybody-walk-imitation-v1',
  body_poses: [
    {
      body_name: 'walker/thorax',
      position: [0, 0, 0.12],
      quaternion: [1, 0, 0, 0],
    },
  ],
  geom_poses: [
    {
      geom_name: 'walker/thorax',
      position: [0.1, 0, 0.12],
      rotation_matrix: [1, 0, 0, 0, 1, 0, 0, 0, 1],
    },
  ],
}

describe('MujocoFlyBrowserViewerViewport', () => {
  beforeEach(() => {
    createSceneMock.mockReset()
    applyPoseMock.mockReset()
    resetViewMock.mockReset()
    setViewPresetMock.mockReset()
    disposeMock.mockReset()
    createSceneMock.mockResolvedValue({
      applyPoseFrame: applyPoseMock,
      resetView: resetViewMock,
      setViewPreset: setViewPresetMock,
      dispose: disposeMock,
    })
  })

  it('creates the Babylon viewer scene from bootstrap and exposes local viewer controls', async () => {
    const controlsRef = vi.fn()
    const { rerender, unmount } = render(
      <MujocoFlyBrowserViewerViewport
        bootstrap={bootstrapPayload}
        viewerState={null}
        status="paused"
        onViewerControlsRef={controlsRef}
      />,
    )

    await waitFor(() => {
      expect(createSceneMock).toHaveBeenCalledTimes(1)
    })

    rerender(
      <MujocoFlyBrowserViewerViewport
        bootstrap={bootstrapPayload}
        viewerState={posePayload}
        status="paused"
        onViewerControlsRef={controlsRef}
      />,
    )

    await waitFor(() => {
      expect(applyPoseMock).toHaveBeenCalledWith(posePayload)
    })

    expect(controlsRef).toHaveBeenCalled()
    const lastCall = controlsRef.mock.calls.at(-1)?.[0]
    expect(typeof lastCall.resetView).toBe('function')
    expect(typeof lastCall.setViewPreset).toBe('function')

    lastCall.resetView()
    lastCall.setViewPreset('side')

    expect(resetViewMock).toHaveBeenCalledTimes(1)
    expect(setViewPresetMock).toHaveBeenCalledWith('side')

    unmount()
    expect(disposeMock).toHaveBeenCalledTimes(1)
  })

  it('applies the latest viewer pose after an async scene bootstrap race', async () => {
    let resolveScene: ((handle: MockSceneHandle) => void) | null = null

    createSceneMock.mockReset()
    createSceneMock.mockImplementation(
      () =>
        new Promise<MockSceneHandle>((resolve) => {
          resolveScene = resolve
        }),
    )

    const controlsRef = vi.fn()
    const { rerender } = render(
      <MujocoFlyBrowserViewerViewport
        bootstrap={bootstrapPayload}
        viewerState={null}
        status="paused"
        onViewerControlsRef={controlsRef}
      />,
    )

    rerender(
      <MujocoFlyBrowserViewerViewport
        bootstrap={bootstrapPayload}
        viewerState={posePayload}
        status="paused"
        onViewerControlsRef={controlsRef}
      />,
    )

    expect(resolveScene).toBeTypeOf('function')
    if (!resolveScene) {
      throw new Error('expected scene factory to resolve')
    }
    const sceneResolver = resolveScene as (handle: MockSceneHandle) => void
    sceneResolver({
      applyPoseFrame: applyPoseMock,
      resetView: resetViewMock,
      setViewPreset: setViewPresetMock,
      dispose: disposeMock,
    })

    await waitFor(() => {
      expect(applyPoseMock).toHaveBeenCalledWith(posePayload)
    })
  })

  it('does not restart the Babylon scene when parent callbacks change identity during viewer updates', async () => {
    const { rerender } = render(
      <MujocoFlyBrowserViewerViewport
        bootstrap={bootstrapPayload}
        viewerState={null}
        status="paused"
        onViewerControlsRef={() => undefined}
        onError={() => undefined}
      />,
    )

    await waitFor(() => {
      expect(createSceneMock).toHaveBeenCalledTimes(1)
    })

    rerender(
      <MujocoFlyBrowserViewerViewport
        bootstrap={bootstrapPayload}
        viewerState={posePayload}
        status="paused"
        onViewerControlsRef={() => undefined}
        onError={() => undefined}
      />,
    )

    await waitFor(() => {
      expect(applyPoseMock).toHaveBeenCalledWith(posePayload)
    })

    expect(createSceneMock).toHaveBeenCalledTimes(1)
  })
})
