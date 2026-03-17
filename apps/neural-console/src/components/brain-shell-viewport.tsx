import { Component, Suspense, useMemo } from 'react'

import { Canvas } from '@react-three/fiber'
import { Html, OrbitControls, useGLTF } from '@react-three/drei'
import { Box3, Group, Mesh, MeshStandardMaterial, Object3D, Vector3 } from 'three'

import {
  getBrainShellMaterialAppearance,
  getNeuropilGlowMaterialAppearance,
} from '@/components/brain-shell-appearance'
import { useConsolePreferences } from '@/providers/console-preferences-provider'
import type {
  BrainAssetManifestPayload,
  BrainShellPayload,
  DisplayRegionActivityPayload,
} from '@/types/console'

const CAN_RENDER_THREE = typeof window !== 'undefined' && import.meta.env.MODE !== 'test'

interface BrainShellViewportProps {
  shell: BrainShellPayload | null | undefined
  brainAssets: BrainAssetManifestPayload | null
  displayRegionActivity: readonly DisplayRegionActivityPayload[]
  glowAvailable: boolean
}

interface GlowMeshEntry {
  groupNeuropilId: string
  assetUrl: string
  defaultColor: string
  glowStrength: number
}

export function BrainShellViewport({
  shell,
  brainAssets,
  displayRegionActivity,
  glowAvailable,
}: BrainShellViewportProps) {
  const { resolvedTheme, t } = useConsolePreferences()
  const glowMeshes = useMemo(
    () =>
      resolveGlowMeshes({
        brainAssets,
        displayRegionActivity,
        glowAvailable,
      }),
    [brainAssets, displayRegionActivity, glowAvailable],
  )
  const hasRenderableGlow = glowMeshes.length > 0
  const glowDetail = hasRenderableGlow
    ? t('experiment.viewport.detail.glowAvailable')
    : t('experiment.viewport.detail.glowUnavailable')
  const glowFooter = hasRenderableGlow
    ? t('experiment.viewport.footer.glowAvailable')
    : t('experiment.viewport.footer.glowUnavailable')

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
              ? `${brainAssets.shell.render_format.toUpperCase()} · ${brainAssets.shell.vertex_count.toLocaleString()} vertices · ${glowDetail}`
              : `Asset: ${shell.asset_id} · ${glowDetail}`
          }
        />
      </ViewportFrame>
    )
  }

  return (
    <ViewportFrame>
      <ViewportRenderBoundary
        fallback={
          <ViewportCanvasScene
            shell={shell}
            theme={resolvedTheme}
            glowMeshes={[]}
            footerLabel={t('experiment.viewport.footer.glowUnavailable')}
            orbitLabel={t('experiment.viewport.overlay.orbit')}
            loadingLabel={t('experiment.brain.loading')}
          />
        }
        resetKey={`${shell.asset_url}:${glowMeshes.map((entry) => entry.assetUrl).join('|')}`}
      >
        <ViewportCanvasScene
          shell={shell}
          theme={resolvedTheme}
          glowMeshes={glowMeshes}
          footerLabel={glowFooter}
          orbitLabel={t('experiment.viewport.overlay.orbit')}
          loadingLabel={t('experiment.brain.loading')}
        />
      </ViewportRenderBoundary>
    </ViewportFrame>
  )
}

export class ViewportRenderBoundary extends Component<
  {
    fallback: React.ReactNode
    resetKey: string
    children: React.ReactNode
  },
  { hasError: boolean }
> {
  state = { hasError: false }

  static getDerivedStateFromError() {
    return { hasError: true }
  }

  componentDidCatch() {
    // Fail closed in the viewport: render shell-only fallback instead of crashing the page.
  }

  componentDidUpdate(prevProps: Readonly<{ resetKey: string }>) {
    if (this.state.hasError && prevProps.resetKey !== this.props.resetKey) {
      this.setState({ hasError: false })
    }
  }

  render() {
    if (this.state.hasError) {
      return this.props.fallback
    }
    return this.props.children
  }
}

function ViewportCanvasScene({
  shell,
  theme,
  glowMeshes,
  footerLabel,
  orbitLabel,
  loadingLabel,
}: {
  shell: BrainShellPayload
  theme: 'light' | 'dark'
  glowMeshes: GlowMeshEntry[]
  footerLabel: string
  orbitLabel: string
  loadingLabel: string
}) {
  return (
    <>
      <Canvas camera={{ position: [0, 0, 3.2], fov: 34 }}>
        <color attach="background" args={[theme === 'dark' ? '#07111e' : '#eef4fb']} />
        <ambientLight intensity={0.85} />
        <hemisphereLight
          intensity={0.65}
          groundColor={theme === 'dark' ? '#06101a' : '#d8e2ec'}
          color={theme === 'dark' ? '#d7ebff' : '#1e3a5f'}
        />
        <directionalLight
          position={[3, 3, 4]}
          intensity={1.4}
          color={theme === 'dark' ? '#d4e6ff' : '#dbeafe'}
        />
        <directionalLight
          position={[-2.5, -1.5, 2]}
          intensity={0.5}
          color={theme === 'dark' ? '#7aa7ff' : '#2563eb'}
        />
        <Suspense fallback={<Html center className="text-xs text-muted-foreground">{loadingLabel}</Html>}>
          <BrainShellModel shell={shell} theme={theme} glowMeshes={glowMeshes} />
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
          {orbitLabel}
        </div>
      </div>
      <div className="console-overlay-chip pointer-events-none absolute bottom-4 left-4 px-3 py-2 text-xs">
        {footerLabel}
      </div>
    </>
  )
}

function BrainShellModel({
  shell,
  theme,
  glowMeshes,
}: {
  shell: BrainShellPayload
  theme: 'light' | 'dark'
  glowMeshes: GlowMeshEntry[]
}) {
  const gltf = useGLTF(shell.asset_url)

  const { shellScene, frameCenter, frameScale } = useMemo(() => {
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
    const scale = 2 / maxDimension

    return { shellScene: scene, frameCenter: center, frameScale: scale }
  }, [gltf.scene, shell.base_color, shell.opacity, theme])

  return (
    <group scale={[frameScale, frameScale, frameScale]} rotation={[-0.2, 0.55, 0]}>
      <group position={[-frameCenter.x, -frameCenter.y, -frameCenter.z]}>
        <primitive object={shellScene} />
        {glowMeshes.map((entry) => (
          <GroupedNeuropilGlowMesh
            key={`${entry.groupNeuropilId}:${entry.assetUrl}`}
            assetUrl={entry.assetUrl}
            defaultColor={entry.defaultColor}
            glowStrength={entry.glowStrength}
            theme={theme}
          />
        ))}
      </group>
    </group>
  )
}

function GroupedNeuropilGlowMesh({
  assetUrl,
  defaultColor,
  glowStrength,
  theme,
}: {
  assetUrl: string
  defaultColor: string
  glowStrength: number
  theme: 'light' | 'dark'
}) {
  const gltf = useGLTF(assetUrl)
  const glowScene = useMemo(() => {
    const scene = gltf.scene.clone() as Group
    const appearance = getNeuropilGlowMaterialAppearance({
      baseColor: defaultColor,
      glowStrength,
      theme,
    })
    scene.traverse((child: Object3D) => {
      if (child instanceof Mesh) {
        child.material = new MeshStandardMaterial(appearance)
      }
    })
    return scene
  }, [assetUrl, defaultColor, glowStrength, gltf.scene, theme])

  return <primitive object={glowScene} />
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

function resolveGlowMeshes({
  brainAssets,
  displayRegionActivity,
  glowAvailable,
}: {
  brainAssets: BrainAssetManifestPayload | null
  displayRegionActivity: readonly DisplayRegionActivityPayload[]
  glowAvailable: boolean
}): GlowMeshEntry[] {
  if (!glowAvailable || !brainAssets || displayRegionActivity.length === 0) {
    return []
  }

  const manifestByNeuropil = new Map(
    brainAssets.neuropil_manifest.map((entry) => [entry.neuropil, entry]),
  )

  const renderCandidates = displayRegionActivity.map((activity) => {
    const manifest = manifestByNeuropil.get(activity.group_neuropil_id)
    if (!manifest || typeof manifest.asset_url !== 'string' || manifest.asset_url.length === 0) {
      return null
    }
    return {
      activity,
      manifest,
    }
  })

  // Research strict mode: if any declared grouped neuropil cannot map to a declared asset, disable glow.
  if (renderCandidates.some((candidate) => candidate == null)) {
    return []
  }

  const typedCandidates = renderCandidates.filter((candidate) => candidate != null)
  if (typedCandidates.length === 0) {
    return []
  }
  const maxActivityMass = Math.max(
    ...typedCandidates.map((candidate) => candidate.activity.raw_activity_mass),
  )

  return typedCandidates
    .sort((left, right) => left.manifest.priority - right.manifest.priority)
    .map((candidate) => ({
      groupNeuropilId: candidate.activity.group_neuropil_id,
      assetUrl: candidate.manifest.asset_url as string,
      defaultColor: candidate.manifest.default_color,
      glowStrength: toGlowStrength(candidate.activity.raw_activity_mass, maxActivityMass),
    }))
}

function toGlowStrength(rawActivityMass: number, maxActivityMass: number) {
  if (maxActivityMass <= 0) {
    return 0
  }
  return Math.min(1, Math.log1p(rawActivityMass) / Math.log1p(maxActivityMass))
}
