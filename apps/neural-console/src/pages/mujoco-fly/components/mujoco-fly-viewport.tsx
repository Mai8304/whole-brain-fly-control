import { useEffect, useRef } from 'react'

import { createBabylonScene } from '../lib/babylon-scene'
import type { MujocoFlyViewerState, MujocoFlyViewerStatus } from '../lib/mujoco-fly-viewer-client'

export interface MujocoFlyViewportProps {
  viewerState: MujocoFlyViewerState | null
  status: MujocoFlyViewerStatus
  onResetCameraRef: (reset: () => void) => void
  onError?: (error: Error) => void
}

export function MujocoFlyViewport({
  viewerState,
  status,
  onResetCameraRef,
  onError,
}: MujocoFlyViewportProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) {
      return
    }

    try {
      const handle = createBabylonScene(canvas)
      onResetCameraRef(handle.resetCamera)
      return () => {
        onResetCameraRef(() => undefined)
        handle.dispose()
      }
    } catch (error) {
      onError?.(error as Error)
      return undefined
    }
  }, [onError, onResetCameraRef])

  const reason = viewerState?.reason

  return (
    <section
      data-testid="mujoco-fly-viewport-shell"
      className="relative min-h-[calc(100vh-11rem)] overflow-hidden rounded-[28px] border border-border/60 bg-background/40 shadow-sm"
      data-status={status}
    >
      <canvas ref={canvasRef} className="h-full w-full rounded-[28px]" />
      {status === 'unavailable' && reason ? (
        <div className="pointer-events-none absolute inset-x-8 bottom-8 rounded-2xl border border-border/70 bg-background/92 px-5 py-4 shadow-sm">
          <p className="text-sm font-medium text-foreground">{reason}</p>
        </div>
      ) : null}
    </section>
  )
}
