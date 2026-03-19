import { Material } from '@babylonjs/core/Materials/material'
import { describe, expect, it } from 'vitest'

import {
  collectPreloadMeshAssets,
  computeFocusTargetMujoco,
  computeViewerFitRadiusFromBounds,
  computeViewerFitRadiusMujoco,
  fallbackCameraPresetConfig,
  groundPaletteFromManifest,
  resolveViewerMaterialConfig,
  materialColorFromRgba,
  resolveMountedViewerCameraConfig,
  resolveViewerTarget,
  rotationMatrixToQuaternion,
} from './babylon-scene'
import { Vector3 } from '@babylonjs/core/Maths/math.vector'

describe('babylon-scene helpers', () => {
  it('converts official rgba into a viewer material config instead of a single hardcoded dark color', () => {
    const material = materialColorFromRgba([0.67, 0.35, 0.14, 1])

    expect(material.diffuse).toEqual([0.67, 0.35, 0.14])
    expect(material.alpha).toBe(1)
  })

  it('keeps local side-view framing tight instead of inheriting the distant runtime camera offset', () => {
    const preset = fallbackCameraPresetConfig('side', [0, 0, 0.13], 0.28)

    expect(preset.radius).toBeCloseTo(0.28, 6)
    expect(preset.position[0]).toBeLessThan(0)
    expect(preset.position[2]).toBeLessThan(-0.1)
    expect(preset.target).toEqual([0, 0, 0.13])
  })

  it('mounts official side cameras on the thorax pose instead of treating XML camera offsets as world-space positions', () => {
    const preset = resolveMountedViewerCameraConfig({
      cameraManifest: {
        preset: 'side',
        camera_name: 'walker/side',
        parent_body_name: 'walker/thorax',
        mode: 'track',
        position: [-0.045, 0.424, -0.035],
        quaternion: null,
        xyaxes: [-1, 0, 0, 0, 0, 1],
        fovy: null,
      },
      bodyPose: {
        body_name: 'walker/thorax',
        position: [0.12, -0.03, 0.14],
        quaternion: [1, 0, 0, 0],
      },
      focusTargetMujoco: [0.12, -0.03, 0.14],
      fitRadius: 0.28,
    })

    expect(preset.position[0]).toBeCloseTo(0.075, 6)
    expect(preset.position[1]).toBeCloseTo(0.105, 6)
    expect(preset.position[2]).toBeCloseTo(-0.394, 6)
    expect(preset.target[2]).toBeGreaterThan(preset.position[2])
  })

  it('preserves the official checker floor palette instead of lifting it to white', () => {
    const palette = groundPaletteFromManifest({
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
    })

    expect(palette.base).toEqual([0.2, 0.3, 0.4])
    expect(palette.accent).toEqual([0.1, 0.2, 0.3])
    expect(palette.mark).toEqual([0.8, 0.8, 0.8])
  })

  it('treats wing membranes as translucent two-sided surfaces with depth pre-pass', () => {
    const material = resolveViewerMaterialConfig({
      materialName: 'walker/membrane',
      rgba: [0.539, 0.686, 0.8, 0.4],
      specular: 0.62,
      shininess: 0.907,
    })

    expect(material.alpha).toBeCloseTo(0.16, 6)
    expect(material.backFaceCulling).toBe(false)
    expect(material.twoSidedLighting).toBe(true)
    expect(material.needDepthPrePass).toBe(true)
    expect(material.renderingGroupId).toBe(1)
    expect(material.sideOrientation).toBe(Material.CounterClockWiseSideOrientation)
  })

  it('keeps opaque flybody shell materials single-sided so the abdomen and legs do not show internal faces', () => {
    const bodyMaterial = resolveViewerMaterialConfig({
      materialName: 'walker/body',
      rgba: [0.674, 0.35, 0.143, 1],
      specular: 0,
      shininess: 0.6,
    })
    const lowerMaterial = resolveViewerMaterialConfig({
      materialName: 'walker/lower',
      rgba: [0.799, 0.61, 0.386, 1],
      specular: 0,
      shininess: 0.6,
    })

    expect(bodyMaterial.backFaceCulling).toBe(true)
    expect(bodyMaterial.twoSidedLighting).toBe(false)
    expect(bodyMaterial.sideOrientation).toBe(Material.CounterClockWiseSideOrientation)
    expect(lowerMaterial.backFaceCulling).toBe(true)
    expect(lowerMaterial.twoSidedLighting).toBe(false)
    expect(lowerMaterial.sideOrientation).toBe(Material.CounterClockWiseSideOrientation)
  })

  it('preserves official black accent materials instead of recoloring them in the viewer', () => {
    const blackMaterial = resolveViewerMaterialConfig({
      materialName: 'walker/black',
      rgba: [0, 0, 0, 1],
      specular: 0,
      shininess: 0.727,
    })

    expect(blackMaterial.diffuse).toEqual([0, 0, 0])
    expect(blackMaterial.specular).toBe(0)
    expect(blackMaterial.shininess).toBe(0.727)
  })

  it('preloads unique non-ghost mesh assets before building the scene', () => {
    const assets = collectPreloadMeshAssets([
      {
        geom_name: 'walker/thorax',
        body_name: 'walker/thorax',
        mesh_asset: '/thorax.obj',
      },
      {
        geom_name: 'walker/head',
        body_name: 'walker/head',
        mesh_asset: '/head.obj',
      },
      {
        geom_name: 'walker/head_duplicate',
        body_name: 'walker/head',
        mesh_asset: '/head.obj',
      },
      {
        geom_name: 'ghost/thorax',
        body_name: 'ghost/thorax',
        mesh_asset: '/ghost.obj',
      },
    ])

    expect(assets).toEqual(['/thorax.obj', '/head.obj'])
  })

  it('derives geom world rotation directly from official geom rotation matrices', () => {
    const quaternion = rotationMatrixToQuaternion([
      1, 0, 0,
      0, 1, 0,
      0, 0, 1,
    ])

    expect(quaternion.x).toBeCloseTo(0, 6)
    expect(quaternion.y).toBeCloseTo(0, 6)
    expect(quaternion.z).toBeCloseTo(0, 6)
    expect(quaternion.w).toBeCloseTo(1, 6)
  })

  it('focuses the viewer camera on thorax, head, and abdomen instead of leg-dominated bounds', () => {
    const focusTarget = computeFocusTargetMujoco({
      frame_id: 1,
      sim_time: 0,
      running_state: 'paused',
      current_camera: 'side',
      scene_version: 'flybody-walk-imitation-v1',
      body_poses: [
        { body_name: 'walker/thorax', position: [0, 0, 0.13], quaternion: [1, 0, 0, 0] },
        { body_name: 'walker/head', position: [0.05, 0, 0.13], quaternion: [1, 0, 0, 0] },
        { body_name: 'walker/abdomen', position: [-0.05, 0, 0.13], quaternion: [1, 0, 0, 0] },
        { body_name: 'walker/tarsus_T3_left', position: [-0.3, 0.2, -0.2], quaternion: [1, 0, 0, 0] },
      ],
      geom_poses: [],
    })

    expect(focusTarget?.[0]).toBeCloseTo(0, 6)
    expect(focusTarget?.[1]).toBeCloseTo(0, 6)
    expect(focusTarget?.[2]).toBeCloseTo(0.118, 6)
  })

  it('derives viewer fit radius from the main fly silhouette instead of stretched leg tips', () => {
    const radius = computeViewerFitRadiusMujoco({
      frame_id: 1,
      sim_time: 0,
      running_state: 'paused',
      current_camera: 'side',
      scene_version: 'flybody-walk-imitation-v1',
      body_poses: [
        { body_name: 'walker/thorax', position: [0, 0, 0.13], quaternion: [1, 0, 0, 0] },
        { body_name: 'walker/head', position: [0.05, 0, 0.13], quaternion: [1, 0, 0, 0] },
        { body_name: 'walker/abdomen', position: [-0.05, 0, 0.13], quaternion: [1, 0, 0, 0] },
        { body_name: 'walker/tarsus_T3_left', position: [-0.3, 0.2, -0.2], quaternion: [1, 0, 0, 0] },
      ],
      geom_poses: [],
    })

    expect(radius).toBeCloseTo(0.6427, 4)
  })

  it('fits the local viewer camera to the full rendered fly bounds instead of clipping to a close-up', () => {
    const radius = computeViewerFitRadiusFromBounds([0.376, 0.35, 0.186], 0.34)

    expect(radius).toBeGreaterThan(1)
    expect(radius).toBeLessThan(1.3)
  })

  it('targets the full rendered fly bounds once meshes are available instead of over-centering on the torso', () => {
    const target = resolveViewerTarget({
      focusTargetMujoco: [0.004, 0, 0.116],
      flyBoundsCenter: new Vector3(-0.08, 0.089, 0.0),
    })

    expect(target?.x).toBeCloseTo(-0.08, 6)
    expect(target?.y).toBeCloseTo(0.089, 6)
    expect(target?.z).toBeCloseTo(0, 6)
  })
})
