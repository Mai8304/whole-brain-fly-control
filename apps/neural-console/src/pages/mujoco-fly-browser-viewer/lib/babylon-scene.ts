import { ArcRotateCamera } from '@babylonjs/core/Cameras/arcRotateCamera'
import { Engine } from '@babylonjs/core/Engines/engine'
import { HemisphericLight } from '@babylonjs/core/Lights/hemisphericLight'
import { Color3, Color4 } from '@babylonjs/core/Maths/math.color'
import { Matrix, Quaternion, Vector3 } from '@babylonjs/core/Maths/math.vector'
import { CreateGround } from '@babylonjs/core/Meshes/Builders/groundBuilder'
import { Mesh } from '@babylonjs/core/Meshes/mesh'
import { StandardMaterial } from '@babylonjs/core/Materials/standardMaterial'
import { TransformNode } from '@babylonjs/core/Meshes/transformNode'
import { VertexData } from '@babylonjs/core/Meshes/mesh.vertexData'
import { Scene } from '@babylonjs/core/scene'

import type {
  MujocoFlyBrowserViewerBootstrapPayload,
  MujocoFlyBrowserViewerCameraManifestEntry,
  MujocoFlyBrowserViewerCameraPreset,
  MujocoFlyBrowserViewerPosePayload,
} from './mujoco-fly-browser-viewer-client'

declare global {
  interface Window {
    __mujocoFlyBrowserViewerDebug?: {
      sceneMeshCount: () => number
      meshSummaries: () => Array<{ name: string; visible: boolean; totalVertices: number }>
      cameraState: () => { alpha: number; beta: number; radius: number; target: [number, number, number] }
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
const DEFAULT_TARGET = transformMujocoVectorToBabylon([0, 0, 0.13])
const LOCAL_DEFAULT_CAMERA_PRESET: MujocoFlyBrowserViewerCameraPreset = 'track'
const CAMERA_FIT_MULTIPLIER = 0.72

const FALLBACK_CAMERA_OFFSETS: Record<MujocoFlyBrowserViewerCameraPreset, [number, number, number]> =
  {
    track: [1, 0.28, -0.55],
    side: [0.18, 0.18, -1],
    back: [-1, 0.25, 0.18],
    top: [0.1, 1, -0.06],
  }

interface ViewerMaterialConfig {
  diffuse: [number, number, number]
  alpha: number
  specular: number
  shininess: number
}

interface ViewerCameraConfig {
  position: [number, number, number]
  target: [number, number, number]
  radius: number
  upVector: [number, number, number] | null
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
  const engine = new Engine(canvas, true)
  const scene = new Scene(engine)
  scene.clearColor = new Color4(0.94, 0.96, 0.99, 1)
  scene.useRightHandedSystem = true

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
  keyLight.intensity = 1.05
  keyLight.groundColor = new Color3(0.72, 0.77, 0.86)

  const fillLight = new HemisphericLight(
    'mujoco-fly-browser-viewer-fill-light',
    new Vector3(-0.4, -1, -0.2),
    scene,
  )
  fillLight.intensity = 0.26

  const ground = CreateGround(
    'mujoco-fly-browser-viewer-ground',
    { width: 0.65, height: 0.65, subdivisions: 2 },
    scene,
  )
  const groundMaterial = new StandardMaterial('mujoco-fly-browser-viewer-ground-material', scene)
  groundMaterial.diffuseColor = new Color3(0.92, 0.94, 0.97)
  groundMaterial.specularColor = new Color3(0.05, 0.05, 0.05)
  groundMaterial.alpha = 0.95
  ground.material = groundMaterial

  const worldRoot = new TransformNode('mujoco-fly-browser-viewer-world-root', scene)
  worldRoot.rotationQuaternion = MUJOCO_TO_BABYLON_BASIS.clone()
  const geomNodes = new Map<string, TransformNode>()
  const flyMeshes: Mesh[] = []
  const cameraManifestByPreset = new Map(
    bootstrap.camera_manifest.map((entry) => [entry.preset, entry] as const),
  )
  let activePreset: MujocoFlyBrowserViewerCameraPreset = LOCAL_DEFAULT_CAMERA_PRESET
  let followPresetCamera = true

  for (const entry of bootstrap.geom_manifest) {
    if (entry.body_name.startsWith('ghost/')) {
      continue
    }

    const geomNode = new TransformNode(`geom:${entry.geom_name}`, scene)
    geomNode.parent = worldRoot
    geomNode.rotationQuaternion = Quaternion.Identity()
    geomNodes.set(entry.geom_name, geomNode)

    const mesh = await createObjMesh(scene, entry.geom_name, entry.mesh_asset)
    mesh.parent = geomNode
    mesh.scaling = new Vector3(...entry.mesh_scale)
    mesh.isPickable = false
    flyMeshes.push(mesh)
    const materialSpec = materialColorFromRgba(entry.material_rgba)
    const material = new StandardMaterial(`mesh-material:${entry.geom_name}`, scene)
    material.diffuseColor = Color3.FromArray(materialSpec.diffuse)
    material.specularColor = new Color3(
      entry.material_specular ?? materialSpec.specular,
      entry.material_specular ?? materialSpec.specular,
      entry.material_specular ?? materialSpec.specular,
    )
    material.alpha = materialSpec.alpha
    const shininess = entry.material_shininess ?? materialSpec.shininess
    material.specularPower = shininess <= 0 ? 16 : 8 + shininess * 64
    material.backFaceCulling = false
    material.twoSidedLighting = true
    mesh.material = material
  }

  const handleResize = () => engine.resize()
  const markManualCameraInteraction = () => {
    followPresetCamera = false
  }
  canvas.addEventListener('pointerdown', markManualCameraInteraction)
  canvas.addEventListener('wheel', markManualCameraInteraction, { passive: true })
  window.addEventListener('resize', handleResize)
  engine.runRenderLoop(() => {
    scene.render()
  })

  function applyPresetCamera(
    preset: MujocoFlyBrowserViewerCameraPreset,
    focusTarget: Vector3 | null = null,
    flyBounds = computeFlyBounds(flyMeshes),
  ) {
    const target = focusTarget ?? flyBounds?.center ?? DEFAULT_TARGET.clone()
    const fitRadius = flyBounds
      ? Math.max(flyBounds.size.x, flyBounds.size.y, flyBounds.size.z) * CAMERA_FIT_MULTIPLIER
      : 0.52
    const officialCamera = cameraManifestByPreset.get(preset)
    const resolvedCamera = officialCamera
      ? resolveCameraPresetConfig(
          officialCamera,
          [target.x, target.y, target.z],
          fitRadius,
        )
      : fallbackCameraPresetConfig(preset, [target.x, target.y, target.z], fitRadius)

    camera.setTarget(Vector3.FromArray(resolvedCamera.target))
    camera.setPosition(Vector3.FromArray(resolvedCamera.position))
    camera.upVector = resolvedCamera.upVector
      ? Vector3.FromArray(resolvedCamera.upVector)
      : Vector3.Up()
  }

  function setViewPreset(preset: MujocoFlyBrowserViewerCameraPreset) {
    activePreset = preset
    followPresetCamera = true
    applyPresetCamera(preset)
  }

  function applyPoseFrame(payload: MujocoFlyBrowserViewerPosePayload) {
    for (const pose of payload.geom_poses) {
      const node = geomNodes.get(pose.geom_name)
      if (!node) {
        continue
      }
      node.position = new Vector3(...pose.position)
      node.rotationQuaternion = rotationMatrixToQuaternion(pose.rotation_matrix)
    }

    if (!followPresetCamera) {
      return
    }
    applyPresetCamera(activePreset, computeFocusTarget(payload))
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

  return {
    applyPoseFrame,
    resetView() {
      setViewPreset(LOCAL_DEFAULT_CAMERA_PRESET)
    },
    setViewPreset,
    dispose() {
      if (import.meta.env.DEV && window.__mujocoFlyBrowserViewerDebug) {
        delete window.__mujocoFlyBrowserViewerDebug
      }
      window.removeEventListener('resize', handleResize)
      canvas.removeEventListener('pointerdown', markManualCameraInteraction)
      canvas.removeEventListener('wheel', markManualCameraInteraction)
      engine.stopRenderLoop()
      worldRoot.dispose(false, true)
      ground.dispose(false, true)
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
    }
  }
  return {
    diffuse: [rgba[0], rgba[1], rgba[2]],
    alpha: rgba[3],
    specular: 0.18,
    shininess: 0.6,
  }
}

export function resolveCameraPresetConfig(
  cameraManifest: MujocoFlyBrowserViewerCameraManifestEntry,
  target: [number, number, number],
  fitRadius = 0.52,
): ViewerCameraConfig {
  const targetVector = Vector3.FromArray(target)
  const officialPosition = transformMujocoVectorToBabylon(cameraManifest.position)
  const officialOffset = officialPosition.subtract(DEFAULT_TARGET)
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

function fallbackCameraPresetConfig(
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

function cameraDistanceMultiplier(preset: MujocoFlyBrowserViewerCameraPreset) {
  if (preset === 'top') {
    return 1.15
  }
  if (preset === 'track') {
    return 0.95
  }
  return 0.9
}

function normalizeOrNull(vector: Vector3) {
  if (vector.lengthSquared() === 0) {
    return null
  }
  return vector.normalizeToNew()
}

function rotationMatrixToQuaternion(
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
  ] | number[],
) {
  const matrix = Matrix.FromValues(
    rotationMatrix[0],
    rotationMatrix[1],
    rotationMatrix[2],
    0,
    rotationMatrix[3],
    rotationMatrix[4],
    rotationMatrix[5],
    0,
    rotationMatrix[6],
    rotationMatrix[7],
    rotationMatrix[8],
    0,
    0,
    0,
    0,
    1,
  )
  return Quaternion.FromRotationMatrix(matrix)
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
    const response = await fetch(assetUrl)
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
      sourcePositions.push([Number(x), Number(y), Number(z)])
      continue
    }
    if (line.startsWith('vt ')) {
      const [, u, v] = line.split(/\s+/)
      sourceUvs.push([Number(u), Number(v)])
      continue
    }
    if (line.startsWith('vn ')) {
      const [, x, y, z] = line.split(/\s+/)
      sourceNormals.push([Number(x), Number(y), Number(z)])
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

function computeFocusTarget(payload: MujocoFlyBrowserViewerPosePayload) {
  const focusNames = ['walker/thorax', 'walker/abdomen', 'walker/head']
  const matches = payload.body_poses.filter((pose) => focusNames.includes(pose.body_name))
  if (matches.length === 0) {
    return null
  }
  const sum = matches.reduce(
    (accumulator, pose) => accumulator.add(transformMujocoVectorToBabylon(pose.position)),
    Vector3.Zero(),
  )
  return sum.scale(1 / matches.length)
}
