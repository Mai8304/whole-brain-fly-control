import { ArcRotateCamera } from '@babylonjs/core/Cameras/arcRotateCamera'
import { Engine } from '@babylonjs/core/Engines/engine'
import { HemisphericLight } from '@babylonjs/core/Lights/hemisphericLight'
import { Color3, Color4 } from '@babylonjs/core/Maths/math.color'
import { Quaternion, Vector3 } from '@babylonjs/core/Maths/math.vector'
import { TransformNode } from '@babylonjs/core/Meshes/transformNode'
import { Scene } from '@babylonjs/core/scene'

export interface BabylonSceneHandle {
  scene: Scene
  worldRoot: TransformNode
  dispose: () => void
  resetCamera: () => void
}

const DEFAULT_CAMERA_ALPHA = -Math.PI / 2
const DEFAULT_CAMERA_BETA = 1.12
const DEFAULT_CAMERA_RADIUS = 0.58
const DEFAULT_CAMERA_TARGET = new Vector3(0, 0.045, 0)

export function createBabylonScene(canvas: HTMLCanvasElement): BabylonSceneHandle {
  const engine = new Engine(canvas, true)
  const scene = new Scene(engine)
  scene.clearColor = new Color4(0.93, 0.95, 0.98, 1)
  scene.useRightHandedSystem = true

  const worldRoot = new TransformNode('mujoco-fly-world-root', scene)
  worldRoot.rotationQuaternion = Quaternion.Identity()

  const camera = new ArcRotateCamera(
    'mujoco-fly-camera',
    DEFAULT_CAMERA_ALPHA,
    DEFAULT_CAMERA_BETA,
    DEFAULT_CAMERA_RADIUS,
    DEFAULT_CAMERA_TARGET,
    scene,
  )
  camera.minZ = 0.001
  camera.maxZ = 10
  camera.lowerRadiusLimit = 0.08
  camera.upperRadiusLimit = 2
  camera.wheelDeltaPercentage = 0.02
  camera.attachControl(canvas, true)

  const keyLight = new HemisphericLight('mujoco-fly-key-light', new Vector3(0.25, 1, 0.15), scene)
  keyLight.intensity = 1.05
  keyLight.groundColor = new Color3(0.74, 0.78, 0.86)

  const fillLight = new HemisphericLight('mujoco-fly-fill-light', new Vector3(-0.35, -1, -0.2), scene)
  fillLight.intensity = 0.3

  const handleResize = () => engine.resize()
  window.addEventListener('resize', handleResize)
  engine.runRenderLoop(() => {
    scene.render()
  })

  function resetCamera() {
    camera.alpha = DEFAULT_CAMERA_ALPHA
    camera.beta = DEFAULT_CAMERA_BETA
    camera.radius = DEFAULT_CAMERA_RADIUS
    camera.setTarget(DEFAULT_CAMERA_TARGET)
  }

  resetCamera()

  return {
    scene,
    worldRoot,
    resetCamera,
    dispose() {
      window.removeEventListener('resize', handleResize)
      engine.stopRenderLoop()
      worldRoot.dispose(false, true)
      scene.dispose()
      engine.dispose()
    },
  }
}
