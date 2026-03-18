import { Badge } from '@/components/ui/badge'
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

export function MujocoFlyOfficialRenderPage() {
  const { t } = useConsolePreferences()

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
            <div
              data-testid="mujoco-fly-official-render-viewport"
              className="console-viewport-frame flex min-h-[680px] items-center justify-center px-6 py-10"
            >
              <div className="max-w-lg text-center">
                <div className="console-kicker">{t('mujocoFlyOfficialRender.viewport.title')}</div>
                <h2 className="mt-3 text-2xl font-semibold tracking-tight text-foreground">
                  {t('mujocoFlyOfficialRender.viewport.placeholder')}
                </h2>
                <p className="mt-3 text-sm leading-6 text-muted-foreground">
                  {t('mujocoFlyOfficialRender.viewport.note')}
                </p>
              </div>
            </div>
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
                <Button type="button" disabled>
                  {t('action.start')}
                </Button>
                <Button type="button" variant="outline" disabled>
                  {t('action.pause')}
                </Button>
                <Button type="button" variant="outline" disabled>
                  {t('action.reset')}
                </Button>
              </div>

              <Separator />

              <div className="grid gap-2">
                <div className="console-kicker">{t('mujocoFlyOfficialRender.camera.title')}</div>
                <div className="flex flex-wrap gap-2">
                  <Button type="button" variant="outline" disabled>
                    {t('mujocoFlyOfficialRender.camera.follow')}
                  </Button>
                  <Button type="button" variant="outline" disabled>
                    {t('mujocoFlyOfficialRender.camera.side')}
                  </Button>
                  <Button type="button" variant="outline" disabled>
                    {t('mujocoFlyOfficialRender.camera.top')}
                  </Button>
                  <Button type="button" variant="outline" disabled>
                    {t('mujocoFlyOfficialRender.camera.frontQuarter')}
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="console-panel border-none shadow-none">
            <CardHeader className="pb-3">
              <CardTitle>{t('mujocoFlyOfficialRender.status.title')}</CardTitle>
              <CardDescription>{t('mujocoFlyOfficialRender.status.note')}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap items-center gap-3">
                <Badge variant="outline">{t('mujocoFlyOfficialRender.status.loading')}</Badge>
                <p className="text-sm text-muted-foreground">
                  {t('mujocoFlyOfficialRender.status.note')}
                </p>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>
    </main>
  )
}
