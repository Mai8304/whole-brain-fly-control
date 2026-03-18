import { useEffect, useRef, useState } from 'react'

import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { ConsolePageHeader } from '@/components/console-page-header'
import { useConsolePreferences } from '@/providers/console-preferences-provider'

import { MujocoFlyOfficialRenderViewport } from './components/mujoco-fly-official-render-viewport'
import {
  buildMujocoFlyOfficialRenderFrameUrl,
  createMujocoFlyOfficialRenderClient,
  type MujocoFlyOfficialRenderCameraPreset,
  type MujocoFlyOfficialRenderClient,
  type MujocoFlyOfficialRenderSessionPayload,
  type MujocoFlyOfficialRenderStatus,
} from './lib/mujoco-fly-official-render-client'

export function MujocoFlyOfficialRenderPage() {
  const { t } = useConsolePreferences()
  const clientRef = useRef<MujocoFlyOfficialRenderClient | null>(null)
  const [status, setStatus] = useState<MujocoFlyOfficialRenderStatus>('loading')
  const [session, setSession] = useState<MujocoFlyOfficialRenderSessionPayload | null>(null)
  const [frameRevision, setFrameRevision] = useState(0)

  if (clientRef.current === null) {
    clientRef.current = createMujocoFlyOfficialRenderClient()
  }

  useEffect(() => {
    const client = clientRef.current
    if (!client) {
      return
    }

    const syncFromClient = () => {
      setStatus(client.getStatus())
      setSession(client.getSession())
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

  useEffect(() => {
    if (!session?.available) {
      return
    }
    setFrameRevision((current) => current + 1)
  }, [session?.available, session?.current_camera, status])

  useEffect(() => {
    if (status !== 'running' || !session?.available) {
      return
    }
    const intervalId = window.setInterval(() => {
      setFrameRevision((current) => current + 1)
    }, 250)
    return () => window.clearInterval(intervalId)
  }, [session?.available, status])

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
    } catch {
      setStatus(client.getStatus())
      setSession(client.getSession())
    }
  }

  async function applyCameraPreset(camera: MujocoFlyOfficialRenderCameraPreset) {
    const client = clientRef.current
    if (!client) {
      return
    }
    try {
      await client.setCameraPreset(camera)
    } catch {
      setStatus(client.getStatus())
      setSession(client.getSession())
    }
  }

  const frameSrc =
    session?.available && session.current_camera
      ? buildMujocoFlyOfficialRenderFrameUrl({
          width: 1280,
          height: 720,
          camera: session.current_camera,
          cacheKey: frameRevision,
        })
      : null
  const reason = session?.reason ?? null

  return (
    <main
      data-testid="mujoco-fly-official-render-page"
      className="mx-auto flex min-h-screen w-full max-w-[1800px] flex-col gap-4 px-4 py-4 lg:px-6"
    >
      <ConsolePageHeader
        title={t('mujocoFlyOfficialRender.title')}
        description={t('mujocoFlyOfficialRender.description')}
      />

      <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_360px]">
        <Card className="console-panel border-none shadow-none">
          <CardHeader className="pb-3">
            <CardTitle>{t('mujocoFlyOfficialRender.viewport.title')}</CardTitle>
            <CardDescription>{t('mujocoFlyOfficialRender.viewport.description')}</CardDescription>
          </CardHeader>
          <CardContent>
            <MujocoFlyOfficialRenderViewport
              frameSrc={frameSrc}
              frameAlt={t('mujocoFlyOfficialRender.viewport.frameAlt')}
              status={status}
              reason={reason}
            />
          </CardContent>
        </Card>

        <div className="grid gap-4">
          <Card className="console-panel border-none shadow-none">
            <CardHeader className="pb-3">
              <CardTitle>{t('mujocoFlyOfficialRender.controls.title')}</CardTitle>
              <CardDescription>{t('mujocoFlyOfficialRender.controls.description')}</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4">
              <div className="flex flex-wrap gap-2">
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
                  {t('action.pause')}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => void applyControl('reset')}
                  disabled={status !== 'paused' && status !== 'running'}
                >
                  {t('action.reset')}
                </Button>
              </div>

              <Separator />

              <div className="grid gap-2">
                <div className="console-kicker">{t('mujocoFlyOfficialRender.camera.title')}</div>
                <div className="flex flex-wrap gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => void applyCameraPreset('track')}
                    disabled={!session?.available}
                  >
                    {t('mujocoFlyOfficialRender.camera.track')}
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => void applyCameraPreset('side')}
                    disabled={!session?.available}
                  >
                    {t('mujocoFlyOfficialRender.camera.side')}
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => void applyCameraPreset('back')}
                    disabled={!session?.available}
                  >
                    {t('mujocoFlyOfficialRender.camera.back')}
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => void applyCameraPreset('top')}
                    disabled={!session?.available}
                  >
                    {t('mujocoFlyOfficialRender.camera.top')}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="console-panel border-none shadow-none">
            <CardHeader className="pb-3">
              <CardTitle>{t('mujocoFlyOfficialRender.session.title')}</CardTitle>
              <CardDescription>{t('mujocoFlyOfficialRender.session.description')}</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-3">
              <SessionField
                label={t('mujocoFlyOfficialRender.session.field.available')}
                value={
                  session
                    ? session.available
                      ? t('mujocoFlyOfficialRender.session.value.yes')
                      : t('mujocoFlyOfficialRender.session.value.no')
                    : t('mujocoFlyOfficialRender.session.value.loading')
                }
              />
              <SessionField
                label={t('mujocoFlyOfficialRender.session.field.runningState')}
                value={session?.running_state ?? t('mujocoFlyOfficialRender.session.value.loading')}
              />
              <SessionField
                label={t('mujocoFlyOfficialRender.session.field.currentCamera')}
                value={session?.current_camera ?? t('mujocoFlyOfficialRender.session.value.loading')}
              />
              <SessionField
                label={t('mujocoFlyOfficialRender.session.field.checkpointLoaded')}
                value={
                  session
                    ? session.checkpoint_loaded
                      ? t('mujocoFlyOfficialRender.session.value.yes')
                      : t('mujocoFlyOfficialRender.session.value.no')
                    : t('mujocoFlyOfficialRender.session.value.loading')
                }
              />
              <SessionField
                label={t('mujocoFlyOfficialRender.session.field.reason')}
                value={
                  session ? reason ?? t('mujocoFlyOfficialRender.session.value.none') : t('mujocoFlyOfficialRender.session.value.loading')
                }
              />
            </CardContent>
          </Card>
        </div>
      </section>
    </main>
  )
}

function SessionField({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-2xl border border-border/70 bg-background/50 px-4 py-3">
      <div className="text-xs uppercase tracking-[0.18em] text-muted-foreground">{label}</div>
      <div className="mt-1 text-sm font-medium text-foreground">{value}</div>
    </div>
  )
}
