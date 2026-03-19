import { useEffect, useRef } from 'react'

import {
  createMujocoFlyBrowserViewerScene,
  type MujocoFlyBrowserViewerSceneHandle,
} from '../lib/babylon-scene'
import type {
  MujocoFlyBrowserViewerBootstrapPayload,
  MujocoFlyBrowserViewerCameraPreset,
  MujocoFlyBrowserViewerPosePayload,
  MujocoFlyBrowserViewerStatus,
} from '../lib/mujoco-fly-browser-viewer-client'

export interface MujocoFlyBrowserViewerControls {
  resetView: () => void
  setViewPreset: (preset: MujocoFlyBrowserViewerCameraPreset) => void
}

export interface MujocoFlyBrowserViewerViewportProps {
  bootstrap: MujocoFlyBrowserViewerBootstrapPayload | null
  viewerState: MujocoFlyBrowserViewerPosePayload | null
  status: MujocoFlyBrowserViewerStatus
  onViewerControlsRef: (controls: MujocoFlyBrowserViewerControls) => void
  onError?: (error: Error) => void
}

export function MujocoFlyBrowserViewerViewport({
  bootstrap,
  viewerState,
  status,
  onViewerControlsRef,
  onError,
}: MujocoFlyBrowserViewerViewportProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const handleRef = useRef<MujocoFlyBrowserViewerSceneHandle | null>(null)
  const latestViewerStateRef = useRef<MujocoFlyBrowserViewerPosePayload | null>(viewerState)
  const latestControlsRef = useRef(onViewerControlsRef)
  const latestOnErrorRef = useRef(onError)

  useEffect(() => {
    latestViewerStateRef.current = viewerState
  }, [viewerState])

  useEffect(() => {
    latestControlsRef.current = onViewerControlsRef
  }, [onViewerControlsRef])

  useEffect(() => {
    latestOnErrorRef.current = onError
  }, [onError])

  useEffect(() => {
    if (!bootstrap) {
      return
    }
    const canvas = canvasRef.current
    if (!canvas) {
      return
    }

    let cancelled = false

    void (async () => {
      try {
        const handle = await createMujocoFlyBrowserViewerScene(canvas, bootstrap)
        if (cancelled) {
          handle.dispose()
          return
        }
        handleRef.current = handle
        latestControlsRef.current({
          resetView: handle.resetView,
          setViewPreset: handle.setViewPreset,
        })
        if (latestViewerStateRef.current) {
          handle.applyPoseFrame(latestViewerStateRef.current)
        }
      } catch (error) {
        latestOnErrorRef.current?.(error as Error)
      }
    })()

    return () => {
      cancelled = true
      latestControlsRef.current({
        resetView: () => undefined,
        setViewPreset: () => undefined,
      })
      handleRef.current?.dispose()
      handleRef.current = null
    }
  }, [bootstrap])

  useEffect(() => {
    if (!viewerState) {
      return
    }
    handleRef.current?.applyPoseFrame(viewerState)
  }, [viewerState])

  return (
    <section
      data-testid="mujoco-fly-browser-viewer-viewport-shell"
      className="relative min-h-[calc(100vh-11rem)] overflow-hidden rounded-[28px] border border-border/60 bg-background/40 shadow-sm"
      data-status={status}
    >
      <canvas ref={canvasRef} className="h-full w-full rounded-[28px]" />
    </section>
  )
}
