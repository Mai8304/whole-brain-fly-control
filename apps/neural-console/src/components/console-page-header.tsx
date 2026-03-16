import { Badge } from '@/components/ui/badge'
import { useConsolePreferences } from '@/providers/console-preferences-provider'

interface ConsolePageHeaderProps {
  title: string
  description: string
  metrics: {
    label: string
    value: string
    tone?: 'default' | 'success' | 'warning' | 'danger' | 'info'
  }[]
}

export function ConsolePageHeader({
  title,
  description,
  metrics,
}: ConsolePageHeaderProps) {
  const { t } = useConsolePreferences()

  return (
    <header className="console-hero rounded-xl px-4 py-4">
      <div className="flex flex-col gap-4">
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="secondary">{t('app.phase')}</Badge>
            <Badge variant="outline">{t('app.stack')}</Badge>
          </div>
          <div className="space-y-1">
              <h1 className="text-2xl font-semibold tracking-tight text-foreground">{title}</h1>
              <p className="max-w-4xl text-sm leading-6 text-muted-foreground">{description}</p>
            </div>
          </div>

        <div className="grid gap-2 md:grid-cols-2 xl:grid-cols-4">
          {metrics.map((metric) => (
            <div
              key={metric.label}
              className="console-metric rounded-2xl border px-3 py-2"
            >
              <div className="console-kicker">{metric.label}</div>
              <div className={metricToneClass(metric.tone)}>{metric.value}</div>
            </div>
          ))}
        </div>
      </div>
    </header>
  )
}

function metricToneClass(tone: ConsolePageHeaderProps['metrics'][number]['tone']) {
  switch (tone) {
    case 'success':
      return 'mt-1 text-sm font-medium text-emerald-500 dark:text-emerald-300'
    case 'warning':
      return 'mt-1 text-sm font-medium text-amber-500 dark:text-amber-300'
    case 'danger':
      return 'mt-1 text-sm font-medium text-rose-500 dark:text-rose-300'
    case 'info':
      return 'mt-1 text-sm font-medium text-sky-600 dark:text-sky-300'
    default:
      return 'mt-1 text-sm font-medium text-foreground'
  }
}
