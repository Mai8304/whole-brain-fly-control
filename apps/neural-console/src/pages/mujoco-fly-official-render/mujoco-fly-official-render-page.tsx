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
  createMujocoFlyOfficialRenderClient,
  type MujocoFlyOfficialRenderCameraPreset,
  type MujocoFlyOfficialRenderClient,
  type MujocoFlyOfficialRenderSessionPayload,
  type MujocoFlyOfficialRenderStatus,
} from './lib/mujoco-fly-official-render-client'

const FRAME_WIDTH = 1280
const FRAME_HEIGHT = 720
const RUNNING_FRAME_INTERVAL_MS = 250

export function MujocoFlyOfficialRenderPage() {
  const { t } = useConsolePreferences()
  const clientRef = useRef<MujocoFlyOfficialRenderClient | null>(null)
  const frameUrlRef = useRef<string | null>(null)
  const frameCacheKeyRef = useRef(0)
  const frameRequestRef = useRef<Promise<void> | null>(null)
  const [status, setStatus] = useState<MujocoFlyOfficialRenderStatus>('loading')
  const [session, setSession] = useState<MujocoFlyOfficialRenderSessionPayload | null>(null)
  const [frameSrc, setFrameSrc] = useState<string | null>(null)
  const [controlPending, setControlPending] = useState(false)

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
    if (!session?.available || !session.current_camera) {
      replaceFrameSrc(frameUrlRef, setFrameSrc, null)
      return
    }
    if (controlPending) {
      return
    }
    const client = clientRef.current
    if (!client) {
      return
    }

    let cancelled = false

    const fetchFrame = async () => {
      const request = (async () => {
        const blob = await client.fetchFrame({
          width: FRAME_WIDTH,
          height: FRAME_HEIGHT,
          camera: session.current_camera,
          cacheKey: ++frameCacheKeyRef.current,
        })
        if (cancelled) {
          return
        }
        const nextUrl = URL.createObjectURL(blob)
        replaceFrameSrc(frameUrlRef, setFrameSrc, nextUrl)
      })()
      frameRequestRef.current = request
      try {
        await request
      } finally {
        if (frameRequestRef.current === request) {
          frameRequestRef.current = null
        }
      }
    }

    const run = async () => {
      try {
        await fetchFrame()
        while (!cancelled && status === 'running') {
          await sleep(RUNNING_FRAME_INTERVAL_MS)
          if (cancelled) {
            return
          }
          await fetchFrame()
        }
      } catch {
        if (cancelled) {
          return
        }
        setStatus(client.getStatus())
        setSession(client.getSession())
        replaceFrameSrc(frameUrlRef, setFrameSrc, null)
      }
    }

    void run()

    return () => {
      cancelled = true
    }
  }, [controlPending, session?.available, session?.current_camera, status])

  useEffect(() => {
    return () => {
      replaceFrameSrc(frameUrlRef, setFrameSrc, null)
    }
  }, [])

  async function applyControl(action: 'start' | 'pause' | 'reset') {
    const client = clientRef.current
    if (!client) {
      return
    }
    setControlPending(true)
    try {
      await frameRequestRef.current?.catch(() => undefined)
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
    } finally {
      setControlPending(false)
    }
  }

  async function applyCameraPreset(camera: MujocoFlyOfficialRenderCameraPreset) {
    const client = clientRef.current
    if (!client) {
      return
    }
    setControlPending(true)
    try {
      await frameRequestRef.current?.catch(() => undefined)
      await client.setCameraPreset(camera)
    } catch {
      setStatus(client.getStatus())
      setSession(client.getSession())
    } finally {
      setControlPending(false)
    }
  }

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
                  disabled={controlPending || status !== 'paused'}
                >
                  {t('action.start')}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => void applyControl('pause')}
                  disabled={controlPending || status !== 'running'}
                >
                  {t('action.pause')}
                </Button>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => void applyControl('reset')}
                  disabled={controlPending || (status !== 'paused' && status !== 'running')}
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
                    disabled={controlPending || !session?.available}
                  >
                    {t('mujocoFlyOfficialRender.camera.track')}
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => void applyCameraPreset('side')}
                    disabled={controlPending || !session?.available}
                  >
                    {t('mujocoFlyOfficialRender.camera.side')}
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => void applyCameraPreset('back')}
                    disabled={controlPending || !session?.available}
                  >
                    {t('mujocoFlyOfficialRender.camera.back')}
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    onClick={() => void applyCameraPreset('top')}
                    disabled={controlPending || !session?.available}
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

function replaceFrameSrc(
  frameUrlRef: React.MutableRefObject<string | null>,
  setFrameSrc: React.Dispatch<React.SetStateAction<string | null>>,
  nextUrl: string | null,
) {
  const previousUrl = frameUrlRef.current
  frameUrlRef.current = nextUrl
  setFrameSrc(nextUrl)
  if (previousUrl) {
    URL.revokeObjectURL(previousUrl)
  }
}

function sleep(ms: number) {
  return new Promise<void>((resolve) => {
    window.setTimeout(resolve, ms)
  })
}
