import type { MujocoFlyOfficialRenderStatus } from '../lib/mujoco-fly-official-render-client'

export interface MujocoFlyOfficialRenderViewportProps {
  frameSrc: string | null
  frameAlt: string
  status: MujocoFlyOfficialRenderStatus
  reason: string | null
}

export function MujocoFlyOfficialRenderViewport({
  frameSrc,
  frameAlt,
  status,
  reason,
}: MujocoFlyOfficialRenderViewportProps) {
  return (
    <section
      data-testid="mujoco-fly-official-render-viewport"
      className="console-viewport-frame relative min-h-[680px] overflow-hidden rounded-[28px] border border-border/60 bg-background/40"
      data-status={status}
    >
      {frameSrc ? (
        <img
          src={frameSrc}
          alt={frameAlt}
          className="h-full w-full object-contain"
        />
      ) : (
        <div className="flex min-h-[680px] items-center justify-center px-6 py-10">
          <div className="max-w-lg text-center text-sm text-muted-foreground">
            {reason ?? frameAlt}
          </div>
        </div>
      )}

      {status === 'unavailable' && reason ? (
        <div className="pointer-events-none absolute inset-x-8 bottom-8 rounded-2xl border border-border/70 bg-background/92 px-5 py-4 shadow-sm">
          <p className="text-sm font-medium text-foreground">{reason}</p>
        </div>
      ) : null}
    </section>
  )
}
