import { ArcRotateCamera } from '@babylonjs/core/Cameras/arcRotateCamera'
import { Engine } from '@babylonjs/core/Engines/engine'
import { HemisphericLight } from '@babylonjs/core/Lights/hemisphericLight'
import { Color3, Color4 } from '@babylonjs/core/Maths/math.color'
import { Quaternion, Vector3 } from '@babylonjs/core/Maths/math.vector'
import { CreateGround } from '@babylonjs/core/Meshes/Builders/groundBuilder'
import { Mesh } from '@babylonjs/core/Meshes/mesh'
import { StandardMaterial } from '@babylonjs/core/Materials/standardMaterial'
import { TransformNode } from '@babylonjs/core/Meshes/transformNode'
import { VertexData } from '@babylonjs/core/Meshes/mesh.vertexData'
import { Scene } from '@babylonjs/core/scene'

import type {
  MujocoFlyBrowserViewerBootstrapPayload,
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
const CAMERA_FIT_MULTIPLIER = 1.35

const CAMERA_PRESETS: Record<
  MujocoFlyBrowserViewerCameraPreset,
  { alpha: number; beta: number; radius: number; target: Vector3 }
> = {
  track: { alpha: -Math.PI / 2, beta: 1.05, radius: 0.52, target: DEFAULT_TARGET.clone() },
  side: { alpha: Math.PI, beta: 1.18, radius: 0.62, target: DEFAULT_TARGET.clone() },
  back: { alpha: Math.PI / 2, beta: 1.12, radius: 0.58, target: DEFAULT_TARGET.clone() },
  top: { alpha: -Math.PI / 2, beta: 0.22, radius: 0.48, target: DEFAULT_TARGET.clone() },
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
    CAMERA_PRESETS.track.alpha,
    CAMERA_PRESETS.track.beta,
    CAMERA_PRESETS.track.radius,
    CAMERA_PRESETS.track.target,
    scene,
  )
  camera.minZ = 0.001
  camera.maxZ = 10
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
    { width: 0.9, height: 0.9, subdivisions: 2 },
    scene,
  )
  const groundMaterial = new StandardMaterial('mujoco-fly-browser-viewer-ground-material', scene)
  groundMaterial.diffuseColor = new Color3(0.92, 0.94, 0.97)
  groundMaterial.specularColor = new Color3(0.05, 0.05, 0.05)
  groundMaterial.alpha = 0.95
  ground.material = groundMaterial

  const worldRoot = new TransformNode('mujoco-fly-browser-viewer-world-root', scene)
  worldRoot.rotationQuaternion = MUJOCO_TO_BABYLON_BASIS.clone()
  const bodyNodes = new Map<string, TransformNode>()
  const flyMeshes: Mesh[] = []
  let activePreset: MujocoFlyBrowserViewerCameraPreset = bootstrap.default_camera
  let followPresetCamera = true

  for (const entry of bootstrap.body_manifest) {
    const node = new TransformNode(entry.body_name, scene)
    node.parent = worldRoot
    node.rotationQuaternion = Quaternion.Identity()
    bodyNodes.set(entry.body_name, node)
  }

  for (const entry of bootstrap.geom_manifest) {
    if (entry.body_name.startsWith('ghost/')) {
      continue
    }
    const bodyNode = bodyNodes.get(entry.body_name)
    if (!bodyNode) {
      throw new Error(`Geom ${entry.geom_name} references unknown body ${entry.body_name}`)
    }

    const geomNode = new TransformNode(`geom:${entry.geom_name}`, scene)
    geomNode.parent = bodyNode
    geomNode.position = new Vector3(...entry.local_position)
    geomNode.rotationQuaternion = toBabylonQuaternion(entry.local_quaternion)
    geomNode.scaling = new Vector3(...entry.mesh_scale)

    const mesh = await createObjMesh(scene, entry.geom_name, entry.mesh_asset)
    mesh.parent = geomNode
    mesh.isPickable = false
    flyMeshes.push(mesh)
    const material = new StandardMaterial(`mesh-material:${entry.geom_name}`, scene)
    material.diffuseColor = new Color3(0.16, 0.18, 0.2)
    material.specularColor = new Color3(0.05, 0.05, 0.05)
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
    flyBounds = computeFlyBounds(flyMeshes),
  ) {
    const next = CAMERA_PRESETS[preset]
    const target = flyBounds?.center ?? next.target.clone()
    const minRadius = flyBounds
      ? Math.max(
          next.radius,
          Math.max(flyBounds.size.x, flyBounds.size.y, flyBounds.size.z) * CAMERA_FIT_MULTIPLIER,
        )
      : next.radius
    camera.setTarget(target)
    camera.alpha = next.alpha
    camera.beta = next.beta
    camera.radius = minRadius
  }

  function setViewPreset(preset: MujocoFlyBrowserViewerCameraPreset) {
    activePreset = preset
    followPresetCamera = true
    applyPresetCamera(preset)
  }

  function applyPoseFrame(payload: MujocoFlyBrowserViewerPosePayload) {
    for (const pose of payload.body_poses) {
      const node = bodyNodes.get(pose.body_name)
      if (!node) {
        throw new Error(`Received pose for unknown body ${pose.body_name}`)
      }
      node.position = new Vector3(...pose.position)
      node.rotationQuaternion = toBabylonQuaternion(pose.quaternion)
    }

    if (!followPresetCamera) {
      return
    }
    applyPresetCamera(activePreset)
  }

  setViewPreset(bootstrap.default_camera)

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
      setViewPreset(bootstrap.default_camera)
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

function toBabylonQuaternion(quaternion: [number, number, number, number] | number[]) {
  return new Quaternion(quaternion[1], quaternion[2], quaternion[3], quaternion[0])
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
