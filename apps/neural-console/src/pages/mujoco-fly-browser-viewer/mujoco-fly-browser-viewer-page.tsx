import { useEffect, useMemo, useRef, useState } from 'react'

import { ConsolePageHeader } from '@/components/console-page-header'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { useConsolePreferences } from '@/providers/console-preferences-provider'

import {
  MujocoFlyBrowserViewerViewport,
  type MujocoFlyBrowserViewerControls,
} from './components/mujoco-fly-browser-viewer-viewport'
import {
  createMujocoFlyBrowserViewerClient,
  type MujocoFlyBrowserViewerBootstrapPayload,
  type MujocoFlyBrowserViewerCameraPreset,
  type MujocoFlyBrowserViewerClient,
  type MujocoFlyBrowserViewerPosePayload,
  type MujocoFlyBrowserViewerSessionPayload,
  type MujocoFlyBrowserViewerStatus,
} from './lib/mujoco-fly-browser-viewer-client'

const EMPTY_VIEWER_CONTROLS: MujocoFlyBrowserViewerControls = {
  resetView: () => undefined,
  setViewPreset: () => undefined,
}

export function MujocoFlyBrowserViewerPage() {
  const { t } = useConsolePreferences()
  const clientRef = useRef<MujocoFlyBrowserViewerClient | null>(null)
  const viewerControlsRef = useRef<MujocoFlyBrowserViewerControls>(EMPTY_VIEWER_CONTROLS)
  const [status, setStatus] = useState<MujocoFlyBrowserViewerStatus>('loading')
  const [bootstrap, setBootstrap] = useState<MujocoFlyBrowserViewerBootstrapPayload | null>(null)
  const [session, setSession] = useState<MujocoFlyBrowserViewerSessionPayload | null>(null)
  const [viewerState, setViewerState] = useState<MujocoFlyBrowserViewerPosePayload | null>(null)
  const [localError, setLocalError] = useState<string | null>(null)

  if (clientRef.current === null) {
    clientRef.current = createMujocoFlyBrowserViewerClient()
  }

  useEffect(() => {
    const client = clientRef.current
    if (!client) {
      return
    }

    const syncFromClient = () => {
      setStatus(client.getStatus())
      setBootstrap(client.getBootstrap())
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

  const runtimeReason = localError ?? viewerState?.reason ?? session?.reason ?? null
  const sceneVersion =
    viewerState?.scene_version ?? session?.scene_version ?? bootstrap?.scene_version ?? 'unavailable'
  const runtimeMode = bootstrap?.runtime_mode ?? 'unavailable'

  async function applyControl(action: 'start' | 'pause' | 'reset') {
    const client = clientRef.current
    if (!client) {
      return
    }

    try {
      if (action === 'start') {
        await client.start()
        return
      }
      if (action === 'pause') {
        await client.pause()
        return
      }
      await client.reset()
    } catch (error) {
      setLocalError((error as Error).message)
    }
  }

  function applyLocalViewPreset(preset: MujocoFlyBrowserViewerCameraPreset) {
    viewerControlsRef.current.setViewPreset(preset)
  }

  const runtimeAvailableLabel = useMemo(() => {
    if (!session) {
      return t('mujocoFlyBrowserViewer.runtime.value.loading')
    }
    return session.available
      ? t('mujocoFlyBrowserViewer.runtime.value.yes')
      : t('mujocoFlyBrowserViewer.runtime.value.no')
  }, [session, t])

  const checkpointLoadedLabel = useMemo(() => {
    if (!session) {
      return t('mujocoFlyBrowserViewer.runtime.value.loading')
    }
    return session.checkpoint_loaded
      ? t('mujocoFlyBrowserViewer.runtime.value.yes')
      : t('mujocoFlyBrowserViewer.runtime.value.no')
  }, [session, t])

  const runtimeReasonLabel =
    runtimeReason ?? t('mujocoFlyBrowserViewer.runtime.value.none')

  return (
    <main
      data-testid="mujoco-fly-browser-viewer-page"
      className="mx-auto flex min-h-screen w-full max-w-[1800px] flex-col gap-4 px-4 py-4 lg:px-6"
    >
      <ConsolePageHeader
        title={t('mujocoFlyBrowserViewer.title')}
        description={t('mujocoFlyBrowserViewer.description')}
      />

      {runtimeReason ? (
        <section className="rounded-2xl border border-border/70 bg-background/85 px-5 py-4">
          <div className="text-sm font-medium text-foreground">
            {t('mujocoFlyBrowserViewer.viewer.unavailable.title')}
          </div>
          <div className="mt-1 text-sm text-muted-foreground">{runtimeReason}</div>
          <div className="mt-2 text-xs text-muted-foreground">
            {t('mujocoFlyBrowserViewer.viewer.unavailable.description')}
          </div>
        </section>
      ) : null}

      <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_360px]">
        <Card className="console-panel border-none shadow-none">
          <CardHeader className="pb-3">
            <CardTitle>{t('mujocoFlyBrowserViewer.viewer.title')}</CardTitle>
            <CardDescription>{t('mujocoFlyBrowserViewer.viewer.description')}</CardDescription>
          </CardHeader>
          <CardContent>
            <MujocoFlyBrowserViewerViewport
              bootstrap={bootstrap}
              viewerState={viewerState}
              status={status}
              onViewerControlsRef={(controls) => {
                viewerControlsRef.current = controls
              }}
              onError={(error) => setLocalError(error.message)}
            />
          </CardContent>
        </Card>

        <div className="grid gap-4">
          <Card className="console-panel border-none shadow-none">
            <CardHeader className="pb-3">
              <CardTitle>{t('mujocoFlyBrowserViewer.runtime.title')}</CardTitle>
              <CardDescription>{t('mujocoFlyBrowserViewer.runtime.description')}</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4">
              <div className="flex flex-wrap gap-2">
                <Button
                  type="button"
                  onClick={() => void applyControl('start')}
                  disabled={!session?.available || !session.checkpoint_loaded || status !== 'paused'}
                >
                  {t('action.start')}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => void applyControl('pause')}
                  disabled={!session?.available || status !== 'running'}
                >
                  {t('action.pause')}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => void applyControl('reset')}
                  disabled={!session?.available || (status !== 'paused' && status !== 'running')}
                >
                  {t('action.reset')}
                </Button>
              </div>

              <Separator />

              <div className="grid gap-2">
                <div className="console-kicker">{t('mujocoFlyBrowserViewer.view.title')}</div>
                <div className="text-sm text-muted-foreground">
                  {t('mujocoFlyBrowserViewer.view.description')}
                </div>
                <div className="flex flex-wrap gap-2">
                  <Button type="button" variant="outline" onClick={() => viewerControlsRef.current.resetView()}>
                    {t('mujocoFlyBrowserViewer.view.reset')}
                  </Button>
                  <Button type="button" variant="outline" onClick={() => applyLocalViewPreset('track')}>
                    {t('mujocoFlyBrowserViewer.view.track')}
                  </Button>
                  <Button type="button" variant="outline" onClick={() => applyLocalViewPreset('side')}>
                    {t('mujocoFlyBrowserViewer.view.side')}
                  </Button>
                  <Button type="button" variant="outline" onClick={() => applyLocalViewPreset('back')}>
                    {t('mujocoFlyBrowserViewer.view.back')}
                  </Button>
                  <Button type="button" variant="outline" onClick={() => applyLocalViewPreset('top')}>
                    {t('mujocoFlyBrowserViewer.view.top')}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="console-panel border-none shadow-none">
            <CardHeader className="pb-3">
              <CardTitle>{t('mujocoFlyBrowserViewer.runtime.title')}</CardTitle>
              <CardDescription>{t('mujocoFlyBrowserViewer.runtime.description')}</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-3 text-sm">
              <RuntimeField
                label={t('mujocoFlyBrowserViewer.runtime.field.available')}
                value={runtimeAvailableLabel}
              />
              <RuntimeField
                label={t('mujocoFlyBrowserViewer.runtime.field.runningState')}
                value={t(statusKey(status))}
              />
              <RuntimeField
                label={t('mujocoFlyBrowserViewer.runtime.field.currentCamera')}
                value={viewerState?.current_camera ?? session?.current_camera ?? 'track'}
              />
              <RuntimeField
                label={t('mujocoFlyBrowserViewer.runtime.field.checkpointLoaded')}
                value={checkpointLoadedLabel}
              />
              <RuntimeField
                label={t('mujocoFlyBrowserViewer.runtime.field.sceneVersion')}
                value={sceneVersion}
              />
              <RuntimeField
                label={t('mujocoFlyBrowserViewer.runtime.field.runtimeMode')}
                value={runtimeMode}
              />
              <RuntimeField
                label={t('mujocoFlyBrowserViewer.runtime.field.reason')}
                value={runtimeReasonLabel}
              />
            </CardContent>
          </Card>
        </div>
      </section>
    </main>
  )
}

function RuntimeField({ label, value }: { label: string; value: string }) {
  return (
    <div className="grid gap-1">
      <div className="console-kicker">{label}</div>
      <div className="text-foreground">{value}</div>
    </div>
  )
}

function statusKey(status: MujocoFlyBrowserViewerStatus) {
  if (status === 'paused') {
    return 'mujocoFlyBrowserViewer.status.paused' as const
  }
  if (status === 'running') {
    return 'mujocoFlyBrowserViewer.status.running' as const
  }
  if (status === 'unavailable') {
    return 'mujocoFlyBrowserViewer.status.unavailable' as const
  }
  if (status === 'error') {
    return 'mujocoFlyBrowserViewer.status.error' as const
  }
  return 'mujocoFlyBrowserViewer.status.loading' as const
}
