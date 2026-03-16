import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { useConsolePreferences } from '@/providers/console-preferences-provider'

import type { LanguagePreference, ThemePreference } from '@/lib/preferences'

export type ConsolePageId = 'experiment' | 'training'

interface ConsoleSiteToolbarProps {
  currentPage: ConsolePageId
  onPageChange: (page: ConsolePageId) => void
}

export function ConsoleSiteToolbar({
  currentPage,
  onPageChange,
}: ConsoleSiteToolbarProps) {
  const {
    themePreference,
    resolvedTheme,
    setThemePreference,
    languagePreference,
    resolvedLanguage,
    setLanguagePreference,
    t,
  } = useConsolePreferences()

  return (
    <div className="console-toolbar rounded-xl border px-4 py-2.5">
      <div className="flex flex-col gap-3 xl:flex-row xl:items-center xl:justify-between">
        <div className="flex flex-col gap-2">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="secondary">{t('app.phase')}</Badge>
            <Badge variant="outline">{t('app.stack')}</Badge>
          </div>
          <div className="space-y-0.5">
            <div className="text-sm font-medium text-foreground">Fruitfly Console</div>
            <div className="text-xs text-muted-foreground">
              {t('app.page.experiment')} / {t('app.page.training')}
            </div>
          </div>
        </div>

        <div className="flex flex-col gap-3 xl:items-end">
          <div className="flex flex-wrap items-center gap-2">
            <Button
              variant={currentPage === 'experiment' ? 'default' : 'outline'}
              size="sm"
              onClick={() => onPageChange('experiment')}
            >
              {t('app.page.experiment')}
            </Button>
            <Button
              variant={currentPage === 'training' ? 'default' : 'outline'}
              size="sm"
              onClick={() => onPageChange('training')}
            >
              {t('app.page.training')}
            </Button>
          </div>

          <div className="grid gap-3 md:grid-cols-2 xl:min-w-[360px]">
            <PreferenceSelect
              label={t('app.theme.label')}
              value={themePreference}
              onChange={(value) => {
                if (value) {
                  setThemePreference(value as ThemePreference)
                }
              }}
              resolvedLabel={
                themePreference === 'system'
                  ? t(`app.theme.${resolvedTheme}` as const)
                  : undefined
              }
              options={[
                ['system', t('app.theme.system')],
                ['light', t('app.theme.light')],
                ['dark', t('app.theme.dark')],
              ]}
            />
            <PreferenceSelect
              label={t('app.language.label')}
              value={languagePreference}
              onChange={(value) => {
                if (value) {
                  setLanguagePreference(value as LanguagePreference)
                }
              }}
              resolvedLabel={
                languagePreference === 'system'
                  ? t(`app.language.${resolvedLanguage}` as const)
                  : undefined
              }
              options={[
                ['system', t('app.language.system')],
                ['en', t('app.language.en')],
                ['zh-CN', t('app.language.zh-CN')],
                ['zh-TW', t('app.language.zh-TW')],
                ['ja', t('app.language.ja')],
              ]}
            />
          </div>
        </div>
      </div>
    </div>
  )
}

function PreferenceSelect({
  label,
  value,
  onChange,
  options,
  resolvedLabel,
}: {
  label: string
  value: string
  onChange: (value: string | null) => void
  options: [string, string][]
  resolvedLabel?: string
}) {
  return (
    <div className="grid gap-1.5">
      <div className="console-kicker">{label}</div>
      <Select value={value} onValueChange={onChange}>
        <SelectTrigger className="w-full bg-background/70">
          <SelectValue />
        </SelectTrigger>
        <SelectContent align="end">
          {options.map(([optionValue, optionLabel]) => (
            <SelectItem key={optionValue} value={optionValue}>
              {optionLabel}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
      {resolvedLabel ? <div className="text-xs text-muted-foreground">{resolvedLabel}</div> : null}
    </div>
  )
}
