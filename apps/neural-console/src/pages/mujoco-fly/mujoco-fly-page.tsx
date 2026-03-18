import { useCallback, useEffect, useRef, useState } from 'react'

import { Button } from '@/components/ui/button'
import { useConsolePreferences } from '@/providers/console-preferences-provider'

import { MujocoFlyViewport } from './components/mujoco-fly-viewport'
import {
  createMujocoFlyViewerClient,
  type MujocoFlySessionPayload,
  type MujocoFlyViewerClient,
  type MujocoFlyViewerState,
  type MujocoFlyViewerStatus,
} from './lib/mujoco-fly-viewer-client'

export function MujocoFlyPage() {
  const { t } = useConsolePreferences()
  const clientRef = useRef<MujocoFlyViewerClient | null>(null)
  const resetCameraRef = useRef<() => void>(() => undefined)
  const [status, setStatus] = useState<MujocoFlyViewerStatus>('loading')
  const [session, setSession] = useState<MujocoFlySessionPayload | null>(null)
  const [viewerState, setViewerState] = useState<MujocoFlyViewerState | null>(null)

  if (clientRef.current === null) {
    clientRef.current = createMujocoFlyViewerClient()
  }

  useEffect(() => {
    const client = clientRef.current
    if (!client) {
      return
    }

    const syncFromClient = () => {
      setStatus(client.getStatus())
      setSession(client.getSession())
      setViewerState(client.getViewerState())
    }

    syncFromClient()
    const unsubscribe = client.subscribe(syncFromClient)
    void client.bootstrap().catch(() => {
      syncFromClient()
    })

    return () => {
      unsubscribe()
      client.dispose()
    }
  }, [])

  const handleResetCameraRef = useCallback((callback: () => void) => {
    resetCameraRef.current = callback
  }, [])

  async function applyControl(action: 'start' | 'pause' | 'reset') {
    const client = clientRef.current
    if (!client) {
      return
    }

    if (action === 'start') {
      await client.start().catch(() => undefined)
      return
    }
    if (action === 'pause') {
      await client.pause().catch(() => undefined)
      return
    }
    await client.reset().catch(() => undefined)
  }

  const reason = viewerState?.reason ?? session?.reason ?? null
  const sceneVersion = viewerState?.scene_version ?? session?.scene_version ?? 'unavailable'

  return (
    <main
      data-testid="mujoco-fly-page"
      className="mx-auto flex min-h-screen w-full max-w-[1800px] flex-col gap-4 px-4 py-4 lg:px-6"
    >
      <header className="grid gap-2">
        <h1 className="text-3xl font-semibold tracking-tight text-foreground">{t('mujocoFly.title')}</h1>
        <p className="text-sm text-muted-foreground">{t('mujocoFly.description')}</p>
      </header>

      <section className="flex flex-wrap items-center gap-2">
        <Button
          type="button"
          onClick={() => void applyControl('start')}
          disabled={status !== 'paused'}
        >
          {t('action.start')}
        </Button>
        <Button
          type="button"
          variant="outline"
          onClick={() => void applyControl('pause')}
          disabled={status !== 'running'}
        >
          {t('experiment.replay.pause')}
        </Button>
        <Button
          type="button"
          variant="outline"
          onClick={() => void applyControl('reset')}
          disabled={status !== 'paused' && status !== 'running'}
        >
          {t('action.reset')}
        </Button>
        <Button type="button" variant="outline" onClick={() => resetCameraRef.current()}>
          {t('action.resetCamera')}
        </Button>
        <span className="text-xs font-medium uppercase tracking-[0.16em] text-muted-foreground">
          {t(statusLabelKey(status))}
        </span>
        <span className="ml-auto rounded-full border border-border/70 bg-background/80 px-3 py-1 text-xs font-medium text-muted-foreground">
          {t('mujocoFly.sceneVersion')}: {sceneVersion}
        </span>
      </section>

      {reason ? (
        <section className="rounded-2xl border border-border/70 bg-background/85 px-5 py-4">
          <div className="text-sm font-medium text-foreground">{t('mujocoFly.unavailable.title')}</div>
          <div className="mt-1 text-sm text-muted-foreground">{reason}</div>
          <div className="mt-2 text-xs text-muted-foreground">
            {t('mujocoFly.unavailable.description')}
          </div>
        </section>
      ) : null}

      <MujocoFlyViewport
        viewerState={viewerState}
        status={status}
        onResetCameraRef={handleResetCameraRef}
      />
    </main>
  )
}

function statusLabelKey(status: MujocoFlyViewerStatus) {
  if (status === 'paused') {
    return 'mujocoFly.status.paused' as const
  }
  if (status === 'running') {
    return 'mujocoFly.status.running' as const
  }
  if (status === 'unavailable') {
    return 'mujocoFly.status.unavailable' as const
  }
  if (status === 'error') {
    return 'mujocoFly.status.error' as const
  }
  return 'mujocoFly.status.loading' as const
}
