import { ArcRotateCamera } from '@babylonjs/core/Cameras/arcRotateCamera'
import { Engine } from '@babylonjs/core/Engines/engine'
import { DirectionalLight } from '@babylonjs/core/Lights/directionalLight'
import { HemisphericLight } from '@babylonjs/core/Lights/hemisphericLight'
import { ShadowGenerator } from '@babylonjs/core/Lights/Shadows/shadowGenerator'
import '@babylonjs/core/Lights/Shadows/shadowGeneratorSceneComponent'
import { Material } from '@babylonjs/core/Materials/material'
import { StandardMaterial } from '@babylonjs/core/Materials/standardMaterial'
import { DynamicTexture } from '@babylonjs/core/Materials/Textures/dynamicTexture'
import { MirrorTexture } from '@babylonjs/core/Materials/Textures/mirrorTexture'
import { Texture } from '@babylonjs/core/Materials/Textures/texture'
import { Color3, Color4 } from '@babylonjs/core/Maths/math.color'
import { Matrix, Quaternion, Vector3 } from '@babylonjs/core/Maths/math.vector'
import { CreateGround } from '@babylonjs/core/Meshes/Builders/groundBuilder'
import { Mesh } from '@babylonjs/core/Meshes/mesh'
import { TransformNode } from '@babylonjs/core/Meshes/transformNode'
import { VertexData } from '@babylonjs/core/Meshes/mesh.vertexData'
import { Plane } from '@babylonjs/core/Maths/math.plane'
import { Scene } from '@babylonjs/core/scene'

import type {
  MujocoFlyBrowserViewerBootstrapPayload,
  MujocoFlyBrowserViewerBodyPose,
  MujocoFlyBrowserViewerCameraManifestEntry,
  MujocoFlyBrowserViewerCameraPreset,
  MujocoFlyBrowserViewerGroundManifest,
  MujocoFlyBrowserViewerLightManifestEntry,
  MujocoFlyBrowserViewerPosePayload,
} from './mujoco-fly-browser-viewer-client'

declare global {
  interface Window {
    __mujocoFlyBrowserViewerDebug?: {
      sceneMeshCount: () => number
      meshSummaries: () => Array<{ name: string; visible: boolean; totalVertices: number }>
      cameraState: () => { alpha: number; beta: number; radius: number; target: [number, number, number] }
      sceneReady: () => boolean
      lastAppliedFrameId: () => number | null
      geomWorldPose: (
        name: string,
      ) => { position: [number, number, number]; quaternion: [number, number, number, number] } | null
      flyBounds: () => {
        center: [number, number, number]
        size: [number, number, number]
      } | null
    }
  }
}

export interface MujocoFlyBrowserViewerSceneHandle {
  applyPoseFrame: (payload: MujocoFlyBrowserViewerPosePayload) => void
  resetView: () => void
  setViewPreset: (preset: MujocoFlyBrowserViewerCameraPreset) => void
  dispose: () => void
}

const MUJOCO_TO_BABYLON_BASIS = Quaternion.FromEulerAngles(-Math.PI / 2, 0, 0)
const MUJOCO_TO_BABYLON_BASIS_INVERSE = MUJOCO_TO_BABYLON_BASIS.clone().conjugateInPlace()
const DEFAULT_TARGET = transformMujocoVectorToBabylon([0, 0, 0.13])
const LOCAL_DEFAULT_CAMERA_PRESET: MujocoFlyBrowserViewerCameraPreset = 'side'
const DEFAULT_GROUND_HALF_EXTENT = 0.5
const STUDIO_BACKGROUND = new Color4(0, 0, 0, 1)
const CAMERA_FOCUS_BODY_NAMES = [
  'walker/thorax',
  'walker/head',
  'walker/abdomen',
] as const
const CAMERA_FOCUS_Z_BIAS = -0.012
const OFFICIAL_HEADLIGHT_AMBIENT = 0.4
const OFFICIAL_HEADLIGHT_DIFFUSE = 0.8
const OFFICIAL_HEADLIGHT_SPECULAR = 0.1

const FALLBACK_CAMERA_OFFSETS: Record<MujocoFlyBrowserViewerCameraPreset, [number, number, number]> =
  {
    track: [0.682, 0.251, -0.687],
    side: [-0.114, -0.083, -0.99],
    back: [-0.844, 0.537, 0],
    top: [0, 1, 0],
  }

interface ViewerMaterialConfig {
  diffuse: [number, number, number]
  alpha: number
  specular: number
  shininess: number
  sideOrientation: number
  backFaceCulling: boolean
  twoSidedLighting: boolean
  needDepthPrePass: boolean
  renderingGroupId: number
  transparencyMode: number
}

interface ViewerCameraConfig {
  position: [number, number, number]
  target: [number, number, number]
  radius: number
  upVector: [number, number, number] | null
}

interface ViewerArcCameraConfig {
  alpha: number
  beta: number
  radius: number
  target: [number, number, number]
}

interface ViewerDirectionalLightHandle {
  light: DirectionalLight
  manifest: MujocoFlyBrowserViewerLightManifestEntry
}

interface ParsedObjAsset {
  positions: number[]
  normals: number[]
  uvs: number[]
  indices: number[]
}

const OBJ_ASSET_CACHE = new Map<string, Promise<ParsedObjAsset>>()

export async function createMujocoFlyBrowserViewerScene(
  canvas: HTMLCanvasElement,
  bootstrap: MujocoFlyBrowserViewerBootstrapPayload,
): Promise<MujocoFlyBrowserViewerSceneHandle> {
  OBJ_ASSET_CACHE.clear()
  const engine = new Engine(canvas, true)
  const scene = new Scene(engine)
  scene.clearColor = STUDIO_BACKGROUND
  scene.useRightHandedSystem = true
  scene.ambientColor = new Color3(
    OFFICIAL_HEADLIGHT_AMBIENT,
    OFFICIAL_HEADLIGHT_AMBIENT,
    OFFICIAL_HEADLIGHT_AMBIENT,
  )

  const camera = new ArcRotateCamera(
    'mujoco-fly-browser-viewer-camera',
    -Math.PI / 2,
    Math.PI / 2.6,
    0.52,
    DEFAULT_TARGET.clone(),
    scene,
  )
  camera.minZ = 0.001
  camera.maxZ = 10
  camera.fov = 0.48
  camera.lowerRadiusLimit = 0.08
  camera.upperRadiusLimit = 2
  camera.wheelDeltaPercentage = 0.02
  camera.attachControl(canvas, true)

  const keyLight = new HemisphericLight(
    'mujoco-fly-browser-viewer-key-light',
    new Vector3(0.25, 1, 0.35),
    scene,
  )
  keyLight.intensity = 0.48
  keyLight.diffuse = new Color3(0.54, 0.54, 0.54)
  keyLight.specular = new Color3(0.06, 0.06, 0.06)
  keyLight.groundColor = new Color3(0.3, 0.34, 0.38)

  const fillLight = new HemisphericLight(
    'mujoco-fly-browser-viewer-fill-light',
    new Vector3(-0.4, -1, -0.2),
    scene,
  )
  fillLight.intensity = 0.18
  fillLight.diffuse = new Color3(0.95, 0.97, 1)
  fillLight.specular = new Color3(0.04, 0.04, 0.04)
  const headlight = new DirectionalLight(
    'mujoco-fly-browser-viewer-headlight',
    new Vector3(0, -1, 0),
    scene,
  )
  headlight.intensity = 1.18
  headlight.diffuse = new Color3(
    OFFICIAL_HEADLIGHT_DIFFUSE,
    OFFICIAL_HEADLIGHT_DIFFUSE,
    OFFICIAL_HEADLIGHT_DIFFUSE,
  )
  headlight.specular = new Color3(
    OFFICIAL_HEADLIGHT_SPECULAR,
    OFFICIAL_HEADLIGHT_SPECULAR,
    OFFICIAL_HEADLIGHT_SPECULAR,
  )
  camera.onViewMatrixChangedObservable.add(() => {
    syncHeadlight(headlight, camera)
  })

  const ground = createGroundVisual(scene, bootstrap.ground_manifest)
  const directionalLights = createDirectionalLights(scene, bootstrap.light_manifest)

  const worldRoot = new TransformNode('mujoco-fly-browser-viewer-world-root', scene)
  worldRoot.rotationQuaternion = Quaternion.Identity()
  const bodyNodes = new Map<string, TransformNode>()
  const geomNodes = new Map<string, TransformNode>()
  const flyMeshes: Mesh[] = []
  const renderableBodyEntries = bootstrap.body_manifest.filter(
    (entry) => !entry.body_name.startsWith('ghost/'),
  )
  const renderableGeomEntries = bootstrap.geom_manifest.filter(
    (entry) => !entry.body_name.startsWith('ghost/'),
  )
  let activePreset: MujocoFlyBrowserViewerCameraPreset = LOCAL_DEFAULT_CAMERA_PRESET
  let followPresetCamera = true
  let shadowGenerator: ShadowGenerator | null = null
  let disposed = false
  let sceneReady = false
  let lastAppliedFrameId: number | null = null
  let lastPosePayload: MujocoFlyBrowserViewerPosePayload | null = null

  engine.runRenderLoop(() => {
    scene.render()
  })

  for (const entry of renderableBodyEntries) {
    const bodyNode = new TransformNode(`body:${entry.body_name}`, scene)
    bodyNode.parent = worldRoot
    bodyNode.rotationQuaternion = Quaternion.Identity()
    bodyNodes.set(entry.body_name, bodyNode)
  }

  for (const entry of renderableGeomEntries) {
    const geomNode = new TransformNode(`geom:${entry.geom_name}`, scene)
    geomNode.parent = worldRoot
    geomNode.rotationQuaternion = Quaternion.Identity()
    geomNodes.set(entry.geom_name, geomNode)
  }

  const handleResize = () => engine.resize()
  const markManualCameraInteraction = () => {
    followPresetCamera = false
    syncHeadlight(headlight, camera)
  }
  canvas.addEventListener('pointerdown', markManualCameraInteraction)
  canvas.addEventListener('wheel', markManualCameraInteraction, { passive: true })
  window.addEventListener('resize', handleResize)

  function applyPresetCamera(preset: MujocoFlyBrowserViewerCameraPreset) {
    const presetFov = viewerFovForPreset(preset)
    const focusTargetMujoco = computeFocusTargetMujoco(lastPosePayload)
    const flyBounds = computeFlyBounds(flyMeshes)
    const viewerTarget = resolveViewerTarget({
      focusTargetMujoco,
      flyBoundsCenter: flyBounds?.center ?? null,
    })
    const fallbackTarget = viewerTarget ?? DEFAULT_TARGET.clone()
    const fitRadius = flyBounds
      ? computeViewerFitRadiusFromBounds(
          [flyBounds.size.x, flyBounds.size.y, flyBounds.size.z],
          presetFov,
        )
      : (computeViewerFitRadiusMujoco(lastPosePayload) ?? 0.92)
    const cameraManifestEntry = bootstrap.camera_manifest.find((entry) => entry.preset === preset)
    const bodyPose = cameraManifestEntry
      ? lookupBodyPose(lastPosePayload, cameraManifestEntry.parent_body_name)
      : null
    const officialCamera = cameraManifestEntry
      ? resolveMountedViewerCameraConfig({
          cameraManifest: cameraManifestEntry,
          bodyPose,
          focusTargetMujoco: focusTargetMujoco ?? [0, 0, 0.13],
          fitRadius,
        })
      : null
    let resolvedCamera = fallbackArcCameraPresetConfig(
      preset,
      [fallbackTarget.x, fallbackTarget.y, fallbackTarget.z],
      fitRadius,
    )
    if (officialCamera) {
      const targetVector = Vector3.FromArray([fallbackTarget.x, fallbackTarget.y, fallbackTarget.z])
      const officialDirection = normalizeOrNull(
        Vector3.FromArray(officialCamera.position).subtract(targetVector),
      )
      if (officialDirection) {
        const viewerRadius = fitRadius * officialViewerDistanceMultiplier(preset)
        const viewerPosition = targetVector.add(officialDirection.scale(viewerRadius))
        resolvedCamera = viewerCameraConfigToArcCameraConfig({
          position: [viewerPosition.x, viewerPosition.y, viewerPosition.z],
          target: [targetVector.x, targetVector.y, targetVector.z],
          radius: viewerRadius,
          upVector: null,
        })
      }
    }

    camera.setTarget(Vector3.FromArray(resolvedCamera.target))
    camera.alpha = resolvedCamera.alpha
    camera.beta = resolvedCamera.beta
    camera.radius = resolvedCamera.radius
    camera.upVector = Vector3.Up()
    camera.fov = presetFov
    syncHeadlight(headlight, camera)
  }

  function setViewPreset(preset: MujocoFlyBrowserViewerCameraPreset) {
    activePreset = preset
    followPresetCamera = true
    applyPresetCamera(preset)
  }

  function applyPoseFrame(payload: MujocoFlyBrowserViewerPosePayload) {
    lastAppliedFrameId = payload.frame_id
    lastPosePayload = payload
    for (const pose of payload.body_poses) {
      const node = bodyNodes.get(pose.body_name)
      if (!node) {
        continue
      }
      node.position = transformMujocoVectorToBabylon(pose.position)
      node.rotationQuaternion = mujocoQuaternionToBabylon(pose.quaternion)
    }
    for (const pose of payload.geom_poses) {
      const node = geomNodes.get(pose.geom_name)
      if (!node) {
        continue
      }
      node.position = transformMujocoVectorToBabylon(pose.position)
      node.rotationQuaternion = rotationMatrixToQuaternion(pose.rotation_matrix)
    }

    applyMountedLights(directionalLights, payload)

    if (!followPresetCamera) {
      syncHeadlight(headlight, camera)
      return
    }
    applyPresetCamera(activePreset)
  }

  setViewPreset(LOCAL_DEFAULT_CAMERA_PRESET)

  if (import.meta.env.DEV) {
    window.__mujocoFlyBrowserViewerDebug = {
      sceneMeshCount: () => scene.meshes.length,
      meshSummaries: () =>
        scene.meshes.slice(0, 12).map((mesh) => ({
          name: mesh.name,
          visible: mesh.isVisible,
          totalVertices: mesh.getTotalVertices(),
        })),
      cameraState: () => ({
        alpha: camera.alpha,
        beta: camera.beta,
        radius: camera.radius,
        target: [camera.target.x, camera.target.y, camera.target.z],
      }),
      sceneReady: () => sceneReady,
      lastAppliedFrameId: () => lastAppliedFrameId,
      geomWorldPose: (name: string) => {
        const node = geomNodes.get(name)
        if (!node) {
          return null
        }
        node.computeWorldMatrix(true)
        const position = node.getAbsolutePosition()
        const rotation = node.absoluteRotationQuaternion ?? Quaternion.Identity()
        return {
          position: [position.x, position.y, position.z],
          quaternion: [rotation.w, rotation.x, rotation.y, rotation.z],
        }
      },
      flyBounds: () => {
        const flyBounds = computeFlyBounds(flyMeshes)
        if (!flyBounds) {
          return null
        }
        return {
          center: [flyBounds.center.x, flyBounds.center.y, flyBounds.center.z],
          size: [flyBounds.size.x, flyBounds.size.y, flyBounds.size.z],
        }
      },
    }
  }

  void (async () => {
    await Promise.all(
      renderableGeomEntries.map(async (entry) => {
        if (disposed) {
          return
        }
        const geomNode = geomNodes.get(entry.geom_name)
        if (!geomNode) {
          return
        }

        const mesh = await createObjMesh(scene, entry.geom_name, entry.mesh_asset)
        if (disposed) {
          mesh.dispose(false, true)
          return
        }
        mesh.parent = geomNode
        mesh.position = transformMujocoVectorToBabylon(entry.mesh_local_position)
        mesh.rotationQuaternion = mujocoQuaternionToBabylon(entry.mesh_local_quaternion)
        mesh.scaling = new Vector3(...entry.mesh_scale)
        const materialSpec = resolveViewerMaterialConfig({
          materialName: entry.material_name,
          rgba: entry.material_rgba,
          specular: entry.material_specular,
          shininess: entry.material_shininess,
        })
        mesh.isPickable = false
        flyMeshes.push(mesh)
        const material = new StandardMaterial(`mesh-material:${entry.geom_name}`, scene)
        material.diffuseColor = Color3.FromArray(materialSpec.diffuse)
        material.specularColor = new Color3(materialSpec.specular, materialSpec.specular, materialSpec.specular)
        material.alpha = materialSpec.alpha
        material.specularPower = materialSpec.shininess <= 0 ? 16 : 24 + materialSpec.shininess * 104
        material.sideOrientation = materialSpec.sideOrientation
        material.backFaceCulling = materialSpec.backFaceCulling
        material.twoSidedLighting = materialSpec.twoSidedLighting
        material.useSpecularOverAlpha = true
        material.needDepthPrePass = materialSpec.needDepthPrePass
        material.transparencyMode = materialSpec.transparencyMode
        material.separateCullingPass = !materialSpec.backFaceCulling
        material.forceDepthWrite = materialSpec.alpha >= 0.999
        material.ambientColor = materialSpec.backFaceCulling
          ? material.diffuseColor.scale(0.44)
          : material.diffuseColor.scale(0.24)
        if (entry.material_name === 'walker/red') {
          material.emissiveColor = material.diffuseColor.scale(0.08)
        }
        if (entry.material_name === 'walker/membrane') {
          material.emissiveColor = new Color3(0.11, 0.14, 0.17)
          material.specularColor = new Color3(0.92, 0.95, 0.98)
        }
        mesh.material = material
        mesh.overrideMaterialSideOrientation = materialSpec.sideOrientation
        mesh.renderingGroupId = materialSpec.renderingGroupId
        mesh.receiveShadows = entry.material_name !== 'walker/membrane'
      }),
    )

    if (disposed) {
      return
    }
    if (directionalLights[0]) {
      shadowGenerator = createShadowGenerator(directionalLights[0].light, flyMeshes, ground)
      attachGroundReflection(scene, ground, flyMeshes)
    }
    sceneReady = true
    if (lastPosePayload) {
      applyMountedLights(directionalLights, lastPosePayload)
    }
    if (followPresetCamera) {
      applyPresetCamera(activePreset)
    }
  })().catch((error: unknown) => {
    if (!disposed) {
      console.error('Failed to bootstrap MuJoCo fly browser viewer scene', error)
    }
  })

  return {
    applyPoseFrame,
    resetView() {
      setViewPreset(LOCAL_DEFAULT_CAMERA_PRESET)
    },
    setViewPreset,
    dispose() {
      disposed = true
      if (import.meta.env.DEV && window.__mujocoFlyBrowserViewerDebug) {
        delete window.__mujocoFlyBrowserViewerDebug
      }
      window.removeEventListener('resize', handleResize)
      canvas.removeEventListener('pointerdown', markManualCameraInteraction)
      canvas.removeEventListener('wheel', markManualCameraInteraction)
      engine.stopRenderLoop()
      worldRoot.dispose(false, true)
      ground.dispose(false, true)
      shadowGenerator?.dispose()
      for (const light of directionalLights) {
        light.light.dispose()
      }
      headlight.dispose()
      scene.dispose()
      engine.dispose()
    },
  }
}

export function materialColorFromRgba(
  rgba: [number, number, number, number] | null,
): ViewerMaterialConfig {
  if (!rgba) {
    return {
      diffuse: [0.16, 0.18, 0.2],
      alpha: 1,
      specular: 0.05,
      shininess: 0.25,
      sideOrientation: Material.CounterClockWiseSideOrientation,
      backFaceCulling: true,
      twoSidedLighting: false,
      needDepthPrePass: false,
      renderingGroupId: 0,
      transparencyMode: Material.MATERIAL_OPAQUE,
    }
  }
  return {
    diffuse: [rgba[0], rgba[1], rgba[2]],
    alpha: rgba[3],
    specular: 0.18,
    shininess: 0.6,
    sideOrientation: Material.CounterClockWiseSideOrientation,
    backFaceCulling: true,
    twoSidedLighting: false,
    needDepthPrePass: false,
    renderingGroupId: 0,
    transparencyMode: rgba[3] < 1 ? Material.MATERIAL_ALPHABLEND : Material.MATERIAL_OPAQUE,
  }
}

export function collectPreloadMeshAssets(
  geomManifest: Array<{ body_name: string; mesh_asset: string; geom_name?: string }>,
): string[] {
  const assets: string[] = []
  const seen = new Set<string>()
  for (const entry of geomManifest) {
    if (entry.body_name.startsWith('ghost/')) {
      continue
    }
    if (seen.has(entry.mesh_asset)) {
      continue
    }
    seen.add(entry.mesh_asset)
    assets.push(entry.mesh_asset)
  }
  return assets
}

export function resolveViewerMaterialConfig({
  materialName,
  rgba,
  specular,
  shininess,
}: {
  materialName: string | null
  rgba: [number, number, number, number] | null
  specular: number | null
  shininess: number | null
}): ViewerMaterialConfig {
  const base = materialColorFromRgba(rgba)
  const isMembrane = materialName === 'walker/membrane' || (rgba?.[3] ?? 1) < 1
  const membraneDiffuse = isMembrane
    ? ([
        Math.min(1, base.diffuse[0] * 1.08 + 0.1),
        Math.min(1, base.diffuse[1] * 1.08 + 0.1),
        Math.min(1, base.diffuse[2] * 1.08 + 0.08),
      ] as [number, number, number])
    : base.diffuse
  return {
    ...base,
    diffuse: membraneDiffuse,
    alpha: isMembrane ? Math.min(base.alpha, 0.16) : base.alpha,
    specular: specular ?? base.specular,
    shininess: shininess ?? base.shininess,
    backFaceCulling: !isMembrane,
    twoSidedLighting: isMembrane,
    needDepthPrePass: isMembrane,
    renderingGroupId: isMembrane ? 1 : 0,
    transparencyMode: isMembrane ? Material.MATERIAL_ALPHABLEND : Material.MATERIAL_OPAQUE,
  }
}

export function groundPaletteFromManifest(
  groundManifest: MujocoFlyBrowserViewerGroundManifest | null,
): {
  base: [number, number, number]
  accent: [number, number, number]
  mark: [number, number, number]
} {
  if (!groundManifest) {
    return {
      base: [0.2, 0.3, 0.4],
      accent: [0.1, 0.2, 0.3],
      mark: [0.8, 0.8, 0.8],
    }
  }

  return {
    base: groundManifest.texture_rgb1 ?? [0.2, 0.3, 0.4],
    accent: groundManifest.texture_rgb2 ?? [0.1, 0.2, 0.3],
    mark: groundManifest.texture_markrgb ?? [0.8, 0.8, 0.8],
  }
}

export function resolveCameraPresetConfig(
  cameraManifest: MujocoFlyBrowserViewerCameraManifestEntry,
  target: [number, number, number],
  fitRadius = 0.52,
): ViewerCameraConfig {
  const targetVector = Vector3.FromArray(target)
  const officialOffset = transformMujocoVectorToBabylon(cameraManifest.position)
  const normalizedOffset = normalizeOrNull(officialOffset)
  const fallback = fallbackCameraPresetConfig(cameraManifest.preset, target, fitRadius)
  if (!normalizedOffset) {
    return fallback
  }
  const radius = Math.max(officialOffset.length(), fitRadius * cameraDistanceMultiplier(cameraManifest.preset))
  const position = targetVector.add(normalizedOffset.scale(radius))

  return {
    position: [position.x, position.y, position.z],
    target,
    radius,
    upVector: null,
  }
}

export function resolveMountedViewerCameraConfig({
  cameraManifest,
  bodyPose,
  focusTargetMujoco,
  fitRadius = 0.52,
}: {
  cameraManifest: MujocoFlyBrowserViewerCameraManifestEntry
  bodyPose: MujocoFlyBrowserViewerBodyPose | null
  focusTargetMujoco: [number, number, number]
  fitRadius?: number
}): ViewerCameraConfig {
  const worldPositionMujoco = bodyPose
    ? composeMountedMujocoPoint(cameraManifest.position, bodyPose)
    : cameraManifest.position
  const localForward = cameraForwardMujoco(cameraManifest)
  const worldForward = bodyPose
    ? rotateMujocoVectorByQuaternion(localForward, bodyPose.quaternion)
    : localForward
  const forwardDistance = Math.max(
    vectorLength(cameraManifest.position) * 1.15,
    fitRadius * cameraDistanceMultiplier(cameraManifest.preset),
  )
  const targetMujoco = bodyPose
    ? ([
        worldPositionMujoco[0] + worldForward[0] * forwardDistance,
        worldPositionMujoco[1] + worldForward[1] * forwardDistance,
        worldPositionMujoco[2] + worldForward[2] * forwardDistance,
      ] as [number, number, number])
    : focusTargetMujoco
  const position = transformMujocoVectorToBabylon(worldPositionMujoco)
  const target = transformMujocoVectorToBabylon(targetMujoco)

  return {
    position: [position.x, position.y, position.z],
    target: [target.x, target.y, target.z],
    radius: Math.max(position.subtract(target).length(), fitRadius),
    upVector: null,
  }
}

export function fallbackCameraPresetConfig(
  preset: MujocoFlyBrowserViewerCameraPreset,
  target: [number, number, number],
  minimumRadius: number,
): ViewerCameraConfig {
  const targetVector = Vector3.FromArray(target)
  const rawOffset = Vector3.FromArray(FALLBACK_CAMERA_OFFSETS[preset])
  const offset = normalizeOrNull(rawOffset)?.scale(minimumRadius) ?? new Vector3(0, 0, -minimumRadius)
  const position = targetVector.add(offset)
  return {
    position: [position.x, position.y, position.z],
    target,
    radius: position.subtract(targetVector).length(),
    upVector: null,
  }
}

function fallbackArcCameraPresetConfig(
  preset: MujocoFlyBrowserViewerCameraPreset,
  target: [number, number, number],
  minimumRadius: number,
): ViewerArcCameraConfig {
  const targetVector = Vector3.FromArray(target)
  const rawOffset = Vector3.FromArray(FALLBACK_CAMERA_OFFSETS[preset])
  const offset = normalizeOrNull(rawOffset)?.scale(minimumRadius) ?? new Vector3(0, 0, -minimumRadius)
  const position = targetVector.add(offset)
  const relative = position.subtract(targetVector)
  const radius = Math.max(relative.length(), 0.001)
  const alpha = Math.atan2(relative.z, relative.x)
  const beta = Math.acos(
    Math.min(0.999, Math.max(-0.999, relative.y / radius)),
  )
  return {
    alpha,
    beta,
    radius,
    target,
  }
}

function viewerCameraConfigToArcCameraConfig(
  config: ViewerCameraConfig,
): ViewerArcCameraConfig {
  const targetVector = Vector3.FromArray(config.target)
  const position = Vector3.FromArray(config.position)
  const relative = position.subtract(targetVector)
  const radius = Math.max(relative.length(), 0.001)
  const alpha = Math.atan2(relative.z, relative.x)
  const beta = Math.acos(Math.min(0.999, Math.max(-0.999, relative.y / radius)))
  return {
    alpha,
    beta,
    radius,
    target: config.target,
  }
}

function officialViewerDistanceMultiplier(preset: MujocoFlyBrowserViewerCameraPreset) {
  if (preset === 'top') {
    return 1.15
  }
  if (preset === 'track') {
    return 0.84
  }
  return 0.74
}

function cameraDistanceMultiplier(preset: MujocoFlyBrowserViewerCameraPreset) {
  if (preset === 'top') {
    return 1.15
  }
  if (preset === 'track') {
    return 0.95
  }
  return 0.9
}

function viewerFovForPreset(preset: MujocoFlyBrowserViewerCameraPreset) {
  if (preset === 'top') {
    return 0.36
  }
  if (preset === 'track') {
    return 0.4
  }
  return 0.34
}

function lookupBodyPose(
  payload: MujocoFlyBrowserViewerPosePayload | null,
  bodyName: string | null | undefined,
) {
  if (!payload || !bodyName) {
    return null
  }
  return payload.body_poses.find((entry) => entry.body_name === bodyName) ?? null
}

function normalizeOrNull(vector: Vector3) {
  if (vector.lengthSquared() === 0) {
    return null
  }
  return vector.normalizeToNew()
}

function mujocoQuaternionToBabylon(
  quaternion: [number, number, number, number] | number[],
) {
  const rawQuaternion = new Quaternion(
    quaternion[1],
    quaternion[2],
    quaternion[3],
    quaternion[0],
  )
  return MUJOCO_TO_BABYLON_BASIS
    .multiply(rawQuaternion)
    .multiply(MUJOCO_TO_BABYLON_BASIS_INVERSE)
}

export function rotationMatrixToQuaternion(
  rotationMatrix: [
    number,
    number,
    number,
    number,
    number,
    number,
    number,
    number,
    number,
  ],
) {
  // MuJoCo xmat is exposed as a flattened 3x3 basis, but Babylon's
  // Quaternion.FromRotationMatrix expects the matrix values in the engine's
  // internal layout. Reading the incoming basis as columns here preserves the
  // official geom orientation for flybody meshes.
  const matrix = Matrix.FromValues(
    rotationMatrix[0],
    rotationMatrix[3],
    rotationMatrix[6],
    0,
    rotationMatrix[1],
    rotationMatrix[4],
    rotationMatrix[7],
    0,
    rotationMatrix[2],
    rotationMatrix[5],
    rotationMatrix[8],
    0,
    0,
    0,
    0,
    1,
  )
  const rawQuaternion = Quaternion.FromRotationMatrix(matrix)
  return MUJOCO_TO_BABYLON_BASIS
    .multiply(rawQuaternion)
    .multiply(MUJOCO_TO_BABYLON_BASIS_INVERSE)
}

function rotateMujocoVectorByQuaternion(
  vector: [number, number, number],
  quaternion: [number, number, number, number],
) {
  const [w, x, y, z] = quaternion
  const vx = vector[0]
  const vy = vector[1]
  const vz = vector[2]

  const tx = 2 * (y * vz - z * vy)
  const ty = 2 * (z * vx - x * vz)
  const tz = 2 * (x * vy - y * vx)

  return [
    vx + w * tx + (y * tz - z * ty),
    vy + w * ty + (z * tx - x * tz),
    vz + w * tz + (x * ty - y * tx),
  ] as [number, number, number]
}

function cameraForwardMujoco(
  cameraManifest: MujocoFlyBrowserViewerCameraManifestEntry,
): [number, number, number] {
  if (cameraManifest.xyaxes) {
    const xAxis: [number, number, number] = [
      cameraManifest.xyaxes[0],
      cameraManifest.xyaxes[1],
      cameraManifest.xyaxes[2],
    ]
    const yAxis: [number, number, number] = [
      cameraManifest.xyaxes[3],
      cameraManifest.xyaxes[4],
      cameraManifest.xyaxes[5],
    ]
    const zAxis = crossMujocoVectors(xAxis, yAxis)
    return normalizeMujocoVector([-zAxis[0], -zAxis[1], -zAxis[2]])
  }
  if (cameraManifest.quaternion) {
    return normalizeMujocoVector(
      rotateMujocoVectorByQuaternion([0, 0, -1], cameraManifest.quaternion),
    )
  }
  return [0, 0, -1]
}

function composeMountedMujocoPoint(
  localPosition: [number, number, number],
  bodyPose: MujocoFlyBrowserViewerBodyPose,
) {
  const rotated = rotateMujocoVectorByQuaternion(localPosition, bodyPose.quaternion)
  return [
    bodyPose.position[0] + rotated[0],
    bodyPose.position[1] + rotated[1],
    bodyPose.position[2] + rotated[2],
  ] as [number, number, number]
}

function crossMujocoVectors(
  left: [number, number, number],
  right: [number, number, number],
): [number, number, number] {
  return [
    left[1] * right[2] - left[2] * right[1],
    left[2] * right[0] - left[0] * right[2],
    left[0] * right[1] - left[1] * right[0],
  ]
}

function normalizeMujocoVector(vector: [number, number, number]): [number, number, number] {
  const length = vectorLength(vector)
  if (length === 0) {
    return [0, 0, -1]
  }
  return [vector[0] / length, vector[1] / length, vector[2] / length]
}

function vectorLength(vector: [number, number, number]) {
  return Math.sqrt(vector[0] ** 2 + vector[1] ** 2 + vector[2] ** 2)
}

export function computeFocusTargetMujoco(
  payload: MujocoFlyBrowserViewerPosePayload | null,
): [number, number, number] | null {
  if (!payload) {
    return null
  }
  const anchors = payload.body_poses.filter((entry) =>
    CAMERA_FOCUS_BODY_NAMES.includes(entry.body_name as (typeof CAMERA_FOCUS_BODY_NAMES)[number]),
  )
  if (anchors.length === 0) {
    return null
  }
  const sums: [number, number, number] = [0, 0, 0]
  for (const entry of anchors) {
    sums[0] += entry.position[0]
    sums[1] += entry.position[1]
    sums[2] += entry.position[2]
  }
  return [
    sums[0] / anchors.length,
    sums[1] / anchors.length,
    sums[2] / anchors.length + CAMERA_FOCUS_Z_BIAS,
  ]
}

export function computeViewerFitRadiusMujoco(
  payload: MujocoFlyBrowserViewerPosePayload | null,
): number | null {
  const focusTarget = computeFocusTargetMujoco(payload)
  if (!focusTarget || !payload) {
    return null
  }
  const anchors = payload.body_poses.filter((entry) =>
    CAMERA_FOCUS_BODY_NAMES.includes(entry.body_name as (typeof CAMERA_FOCUS_BODY_NAMES)[number]),
  )
  if (anchors.length === 0) {
    return null
  }
  const maxDistance = anchors.reduce((currentMaximum, entry) => {
    const dx = entry.position[0] - focusTarget[0]
    const dy = entry.position[1] - focusTarget[1]
    const dz = entry.position[2] - focusTarget[2]
    return Math.max(currentMaximum, Math.sqrt(dx * dx + dy * dy + dz * dz))
  }, 0)
  if (maxDistance === 0) {
    return 0.38
  }
  return Math.max(0.54, maxDistance * 12.5)
}

export function computeViewerFitRadiusFromBounds(
  size: [number, number, number] | [number, number, number, ...number[]],
  fov: number,
) {
  const maxDimension = Math.max(size[0] ?? 0, size[1] ?? 0, size[2] ?? 0)
  if (maxDimension <= 0) {
    return 0.92
  }
  const safeHalfFov = Math.max(0.12, fov / 2)
  const halfExtent = maxDimension / 2
  return (halfExtent / Math.tan(safeHalfFov)) * 1.18
}

export function resolveViewerTarget({
  focusTargetMujoco,
  flyBoundsCenter,
}: {
  focusTargetMujoco: [number, number, number] | null
  flyBoundsCenter: Vector3 | null
}) {
  if (flyBoundsCenter) {
    return flyBoundsCenter.clone()
  }
  if (focusTargetMujoco) {
    return transformMujocoVectorToBabylon(focusTargetMujoco)
  }
  return null
}

export function transformMujocoVectorToBabylon(
  vector: [number, number, number] | Vector3,
): Vector3 {
  if (vector instanceof Vector3) {
    return new Vector3(vector.x, vector.z, -vector.y)
  }
  return new Vector3(vector[0], vector[2], -vector[1])
}

async function createObjMesh(scene: Scene, name: string, assetUrl: string): Promise<Mesh> {
  const parsed = await loadObjAsset(assetUrl)
  const mesh = new Mesh(name, scene)
  const vertexData = new VertexData()
  vertexData.positions = parsed.positions.slice()
  vertexData.indices = parsed.indices.slice()
  if (parsed.normals.length > 0) {
    vertexData.normals = parsed.normals.slice()
  }
  if (parsed.uvs.length > 0) {
    vertexData.uvs = parsed.uvs.slice()
  }
  vertexData.applyToMesh(mesh)
  return mesh
}

async function loadObjAsset(assetUrl: string): Promise<ParsedObjAsset> {
  const cached = OBJ_ASSET_CACHE.get(assetUrl)
  if (cached) {
    return cached
  }
  const loadPromise = (async () => {
    const response = await fetch(assetUrl, { cache: 'no-store' })
    if (!response.ok) {
      throw new Error(`Failed to load flybody mesh asset ${assetUrl}: ${response.status}`)
    }
    const source = await response.text()
    return parseObjAsset(source)
  })()
  OBJ_ASSET_CACHE.set(assetUrl, loadPromise)
  return loadPromise
}

function parseObjAsset(source: string): ParsedObjAsset {
  const sourcePositions: Array<[number, number, number]> = []
  const sourceNormals: Array<[number, number, number]> = []
  const sourceUvs: Array<[number, number]> = []
  const positions: number[] = []
  const normals: number[] = []
  const uvs: number[] = []
  const indices: number[] = []
  let nextIndex = 0

  for (const rawLine of source.split(/\r?\n/)) {
    const line = rawLine.trim()
    if (!line || line.startsWith('#')) {
      continue
    }

    if (line.startsWith('v ')) {
      const [, x, y, z] = line.split(/\s+/)
      const transformed = transformMujocoVertexToBabylon([
        Number(x),
        Number(y),
        Number(z),
      ])
      sourcePositions.push([transformed[0], transformed[1], transformed[2]])
      continue
    }
    if (line.startsWith('vt ')) {
      const [, u, v] = line.split(/\s+/)
      sourceUvs.push([Number(u), Number(v)])
      continue
    }
    if (line.startsWith('vn ')) {
      const [, x, y, z] = line.split(/\s+/)
      const transformed = transformMujocoVertexToBabylon([
        Number(x),
        Number(y),
        Number(z),
      ])
      sourceNormals.push([transformed[0], transformed[1], transformed[2]])
      continue
    }
    if (!line.startsWith('f ')) {
      continue
    }

    const vertices = line
      .slice(2)
      .trim()
      .split(/\s+/)
      .map(parseObjFaceVertex)

    for (let triangleIndex = 1; triangleIndex < vertices.length - 1; triangleIndex += 1) {
      for (const vertex of [vertices[0], vertices[triangleIndex], vertices[triangleIndex + 1]]) {
        const position = sourcePositions[vertex.positionIndex]
        if (!position) {
          throw new Error(`OBJ position index out of range: ${vertex.positionIndex + 1}`)
        }
        positions.push(...position)

        if (vertex.uvIndex !== null) {
          const uv = sourceUvs[vertex.uvIndex]
          if (!uv) {
            throw new Error(`OBJ uv index out of range: ${vertex.uvIndex + 1}`)
          }
          uvs.push(...uv)
        }

        if (vertex.normalIndex !== null) {
          const normal = sourceNormals[vertex.normalIndex]
          if (!normal) {
            throw new Error(`OBJ normal index out of range: ${vertex.normalIndex + 1}`)
          }
          normals.push(...normal)
        }

        indices.push(nextIndex)
        nextIndex += 1
      }
    }
  }

  return { positions, normals, uvs, indices }
}

function transformMujocoVertexToBabylon(
  vector: [number, number, number],
): [number, number, number] {
  return [vector[0], vector[2], -vector[1]]
}

function parseObjFaceVertex(token: string) {
  const [positionToken, uvToken, normalToken] = token.split('/')
  return {
    positionIndex: Number(positionToken) - 1,
    uvIndex: uvToken ? Number(uvToken) - 1 : null,
    normalIndex: normalToken ? Number(normalToken) - 1 : null,
  }
}

function computeFlyBounds(flyMeshes: Mesh[]) {
  let minimum: Vector3 | null = null
  let maximum: Vector3 | null = null

  for (const mesh of flyMeshes) {
    mesh.computeWorldMatrix(true)
    const { boundingBox } = mesh.getBoundingInfo()
    minimum = minimum
      ? Vector3.Minimize(minimum, boundingBox.minimumWorld)
      : boundingBox.minimumWorld.clone()
    maximum = maximum
      ? Vector3.Maximize(maximum, boundingBox.maximumWorld)
      : boundingBox.maximumWorld.clone()
  }

  if (!minimum || !maximum) {
    return null
  }

  return {
    center: minimum.add(maximum).scale(0.5),
    size: maximum.subtract(minimum),
  }
}

function createGroundVisual(
  scene: Scene,
  groundManifest: MujocoFlyBrowserViewerGroundManifest | null,
) {
  const halfExtentX = groundManifest?.size?.[0] ?? DEFAULT_GROUND_HALF_EXTENT
  const halfExtentY = groundManifest?.size?.[1] ?? DEFAULT_GROUND_HALF_EXTENT
  const ground = CreateGround(
    'mujoco-fly-browser-viewer-ground',
    { width: halfExtentX * 2, height: halfExtentY * 2, subdivisions: 2 },
    scene,
  )
  const groundMaterial = new StandardMaterial('mujoco-fly-browser-viewer-ground-material', scene)
  groundMaterial.specularColor = new Color3(0.08, 0.08, 0.08)
  groundMaterial.backFaceCulling = false

  if (groundManifest) {
    const palette = groundPaletteFromManifest(groundManifest)
    const reflectance = Math.max(0, Math.min(groundManifest.reflectance, 1)) * 0.22
    const texture = createCheckerTexture(scene, palette)
    texture.uScale = Math.max(1, groundManifest.texrepeat[0] * 2)
    texture.vScale = Math.max(1, groundManifest.texrepeat[1] * 2)
    groundMaterial.specularColor = new Color3(reflectance, reflectance, reflectance)
    groundMaterial.diffuseColor = Color3.White()
    groundMaterial.ambientColor = new Color3(0.16, 0.18, 0.22)
    groundMaterial.diffuseTexture = texture
    groundMaterial.alpha = groundManifest.material_rgba?.[3] ?? 1
  } else {
    groundMaterial.diffuseColor = new Color3(0.2, 0.3, 0.4)
    groundMaterial.ambientColor = new Color3(0.16, 0.18, 0.22)
    groundMaterial.alpha = 0.95
  }

  ground.material = groundMaterial
  ground.receiveShadows = true
  return ground
}

function createDirectionalLights(
  scene: Scene,
  lightManifest: MujocoFlyBrowserViewerLightManifestEntry[],
) {
  const directionalLights: ViewerDirectionalLightHandle[] = []

  for (const [index, lightEntry] of lightManifest.entries()) {
    const directionalLight = new DirectionalLight(
      `mujoco-fly-browser-viewer-light:${lightEntry.name}`,
      Vector3.Down(),
      scene,
    )
    const diffuse = lightEntry.diffuse ?? [0.8, 0.8, 0.8]
    directionalLight.diffuse = Color3.FromArray(diffuse)
    directionalLight.specular = Color3.FromArray(diffuse)
    directionalLight.intensity = index === 0 ? 2.8 : index === 1 ? 1.6 : 0.9
    directionalLights.push({ light: directionalLight, manifest: lightEntry })
  }

  return directionalLights
}

function applyMountedLights(
  directionalLights: ViewerDirectionalLightHandle[],
  payload: MujocoFlyBrowserViewerPosePayload,
) {
  for (const entry of directionalLights) {
    const bodyPose = lookupBodyPose(payload, entry.manifest.parent_body_name)
    const positionMujoco = bodyPose
      ? composeMountedMujocoPoint(entry.manifest.position, bodyPose)
      : entry.manifest.position
    const directionMujoco = bodyPose
      ? rotateMujocoVectorByQuaternion(
          entry.manifest.direction ?? inferDirectionFromPosition(entry.manifest.position),
          bodyPose.quaternion,
        )
      : entry.manifest.direction ?? inferDirectionFromPosition(entry.manifest.position)
    entry.light.position = transformMujocoVectorToBabylon(positionMujoco)
    entry.light.direction = transformMujocoVectorToBabylon(directionMujoco).normalize()
  }
}

function createCheckerTexture(
  scene: Scene,
  palette: {
    base: [number, number, number]
    accent: [number, number, number]
    mark: [number, number, number]
  },
) {
  const texture = new DynamicTexture(
    'mujoco-fly-browser-viewer-ground-texture',
    { width: 256, height: 256 },
    scene,
    false,
  )
  const context = texture.getContext()
  const size = 256
  const half = size / 2
  context.fillStyle = cssColor(palette.base)
  context.fillRect(0, 0, half, half)
  context.fillRect(half, half, half, half)
  context.fillStyle = cssColor(palette.accent)
  context.fillRect(half, 0, half, half)
  context.fillRect(0, half, half, half)
  context.strokeStyle = cssColor(palette.mark)
  context.lineWidth = 6
  context.strokeRect(3, 3, size - 6, size - 6)
  context.strokeRect(half + 3, 3, half - 6, half - 6)
  context.strokeRect(3, half + 3, half - 6, half - 6)
  texture.wrapU = Texture.WRAP_ADDRESSMODE
  texture.wrapV = Texture.WRAP_ADDRESSMODE
  texture.update(false)
  return texture
}

function createShadowGenerator(
  light: DirectionalLight,
  flyMeshes: Mesh[],
  ground: Mesh,
) {
  const shadowGenerator = new ShadowGenerator(1024, light)
  shadowGenerator.useBlurExponentialShadowMap = true
  shadowGenerator.blurKernel = 32
  shadowGenerator.darkness = 0.22
  for (const mesh of flyMeshes) {
    shadowGenerator.addShadowCaster(mesh, true)
  }
  ground.receiveShadows = true
  return shadowGenerator
}

function attachGroundReflection(scene: Scene, ground: Mesh, flyMeshes: Mesh[]) {
  const material = ground.material
  if (!(material instanceof StandardMaterial)) {
    return
  }
  const mirror = new MirrorTexture('mujoco-fly-browser-viewer-ground-mirror', 1024, scene, true)
  mirror.mirrorPlane = Plane.FromPositionAndNormal(Vector3.Zero(), Vector3.Up())
  mirror.level = 0.28
  mirror.renderList = flyMeshes
  material.reflectionTexture = mirror
}

function syncHeadlight(light: DirectionalLight, camera: ArcRotateCamera) {
  const direction = camera.target.subtract(camera.position)
  if (direction.lengthSquared() === 0) {
    return
  }
  light.position = camera.position.clone()
  light.direction = direction.normalize()
}

function cssColor([r, g, b]: [number, number, number]) {
  return `rgb(${Math.round(r * 255)}, ${Math.round(g * 255)}, ${Math.round(b * 255)})`
}

function inferDirectionFromPosition(position: [number, number, number]): [number, number, number] {
  return [-position[0], -position[1], -position[2]]
}
