import { Suspense, useMemo } from 'react'

import { Canvas } from '@react-three/fiber'
import { Html, OrbitControls, useGLTF } from '@react-three/drei'
import { Box3, Group, Mesh, MeshStandardMaterial, Object3D, Vector3 } from 'three'

import { getBrainShellMaterialAppearance } from '@/components/brain-shell-appearance'
import { useConsolePreferences } from '@/providers/console-preferences-provider'
import type { BrainAssetManifestPayload, BrainShellPayload } from '@/types/console'

const CAN_RENDER_THREE = typeof window !== 'undefined' && import.meta.env.MODE !== 'test'

interface BrainShellViewportProps {
  shell: BrainShellPayload | null | undefined
  brainAssets: BrainAssetManifestPayload | null
}

export function BrainShellViewport({ shell, brainAssets }: BrainShellViewportProps) {
  const { resolvedTheme, t } = useConsolePreferences()
  if (!shell) {
    return (
      <ViewportFrame>
        <FallbackCopy
          title={t('experiment.viewport.title.missing')}
          detail={t('experiment.viewport.detail.missing')}
        />
      </ViewportFrame>
    )
  }

  if (!CAN_RENDER_THREE) {
    return (
      <ViewportFrame>
        <FallbackCopy
          title={t('experiment.viewport.title.ready')}
          detail={
            brainAssets
              ? `${brainAssets.shell.render_format.toUpperCase()} · ${brainAssets.shell.vertex_count.toLocaleString()} vertices`
              : `Asset: ${shell.asset_id}`
          }
        />
      </ViewportFrame>
    )
  }

  return (
    <ViewportFrame>
      <Canvas camera={{ position: [0, 0, 3.2], fov: 34 }}>
        <color attach="background" args={[resolvedTheme === 'dark' ? '#07111e' : '#eef4fb']} />
        <ambientLight intensity={0.85} />
        <hemisphereLight
          intensity={0.65}
          groundColor={resolvedTheme === 'dark' ? '#06101a' : '#d8e2ec'}
          color={resolvedTheme === 'dark' ? '#d7ebff' : '#1e3a5f'}
        />
        <directionalLight
          position={[3, 3, 4]}
          intensity={1.4}
          color={resolvedTheme === 'dark' ? '#d4e6ff' : '#dbeafe'}
        />
        <directionalLight
          position={[-2.5, -1.5, 2]}
          intensity={0.5}
          color={resolvedTheme === 'dark' ? '#7aa7ff' : '#2563eb'}
        />
        <Suspense fallback={<Html center className="text-xs text-muted-foreground">{t('experiment.brain.loading')}</Html>}>
          <BrainShellModel shell={shell} theme={resolvedTheme} />
        </Suspense>
        <OrbitControls
          autoRotate
          autoRotateSpeed={0.35}
          enablePan={false}
          minDistance={1.8}
          maxDistance={6}
        />
      </Canvas>
      <div className="console-overlay-chip pointer-events-none absolute left-4 top-4 px-3 py-2 text-[11px] uppercase tracking-[0.18em]">
        <div>{shell.asset_id}</div>
        <div className="mt-1 text-[10px] tracking-[0.12em] text-muted-foreground">
          {t('experiment.viewport.overlay.orbit')}
        </div>
      </div>
      <div className="console-overlay-chip pointer-events-none absolute bottom-4 left-4 px-3 py-2 text-xs">
        {t('experiment.viewport.footer')}
      </div>
    </ViewportFrame>
  )
}

function BrainShellModel({
  shell,
  theme,
}: {
  shell: BrainShellPayload
  theme: 'light' | 'dark'
}) {
  const gltf = useGLTF(shell.asset_url)

  const { centeredScene, scale } = useMemo(() => {
    const scene = gltf.scene.clone() as Group
    const appearance = getBrainShellMaterialAppearance({
      baseColor: shell.base_color,
      opacity: shell.opacity,
      theme,
    })
    scene.traverse((child: Object3D) => {
      if (child instanceof Mesh) {
        child.material = new MeshStandardMaterial(appearance)
      }
    })

    const bounds = new Box3().setFromObject(scene)
    const size = bounds.getSize(new Vector3())
    const center = bounds.getCenter(new Vector3())
    const maxDimension = Math.max(size.x, size.y, size.z) || 1
    const nextScale = 2 / maxDimension

    scene.position.set(-center.x, -center.y, -center.z)
    return { centeredScene: scene, scale: nextScale }
  }, [gltf.scene, shell.base_color, shell.opacity, theme])

  return (
    <group scale={[scale, scale, scale]} rotation={[-0.2, 0.55, 0]}>
      <primitive object={centeredScene} />
    </group>
  )
}

function ViewportFrame({ children }: { children: React.ReactNode }) {
  return <div className="console-viewport-frame">{children}</div>
}

function FallbackCopy({ title, detail }: { title: string; detail: string }) {
  return (
    <div className="flex h-full items-center justify-center px-6 text-center text-sm text-muted-foreground">
      <div>
        <p className="text-base font-medium text-foreground">{title}</p>
        <p className="mt-2">{detail}</p>
      </div>
    </div>
  )
}
