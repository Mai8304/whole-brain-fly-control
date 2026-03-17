import { ChevronLeftIcon, ChevronRightIcon, PauseIcon, PlayIcon } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Slider } from '@/components/ui/slider'
import { useConsolePreferences } from '@/providers/console-preferences-provider'
import type { ReplaySessionPayload, TimelinePayload } from '@/types/console'

const SPEED_OPTIONS = [0.25, 0.5, 1, 2]

interface ReplayTimelineProps {
  available: boolean
  session: ReplaySessionPayload | null
  timeline: TimelinePayload
  loading: boolean
  onPlayPause: () => void
  onPrevStep: () => void
  onNextStep: () => void
  onSeek: (step: number) => void
  onSetSpeed: (speed: number) => void
}

export function ReplayTimeline({
  available,
  session,
  timeline,
  loading,
  onPlayPause,
  onPrevStep,
  onNextStep,
  onSeek,
  onSetSpeed,
}: ReplayTimelineProps) {
  const { t } = useConsolePreferences()
  const currentStep = session?.current_step ?? timeline.current_step ?? 0
  const maxStep = Math.max(session?.steps_completed ?? timeline.steps_completed ?? currentStep, currentStep)
  const minStep = currentStep === 0 ? 0 : maxStep > 0 ? 1 : 0
  const sliderMax = Math.max(maxStep, minStep + 1)
  const sliderValue = Math.min(Math.max(currentStep, minStep), maxStep)
  const isPlaying = session?.status === 'playing'

  return (
    <Card
      data-testid="experiment-replay-timeline-card"
      data-layout="three-part-strip"
      className="console-panel border-none bg-card/85 py-3 shadow-none"
    >
      <CardContent
        data-testid="replay-timeline-strip"
        className="grid items-center gap-3 px-4 xl:grid-cols-[auto_1fr_auto]"
      >
        <div data-testid="replay-timeline-left" className="flex flex-wrap items-center gap-2">
          <Button variant="secondary" onClick={onPlayPause} disabled={!available || loading}>
            {isPlaying ? <PauseIcon className="size-4" /> : <PlayIcon className="size-4" />}
            {isPlaying ? t('experiment.replay.pause') : t('experiment.replay.play')}
          </Button>
          <Button variant="outline" onClick={onPrevStep} disabled={!available || loading}>
            <ChevronLeftIcon className="size-4" />
            {t('experiment.replay.prev')}
          </Button>
          <Button variant="outline" onClick={onNextStep} disabled={!available || loading}>
            <ChevronRightIcon className="size-4" />
            {t('experiment.replay.next')}
          </Button>
        </div>

        <div data-testid="replay-timeline-middle" className="grid min-w-0 gap-2 xl:min-w-[18rem]">
          <div className="flex items-center justify-between gap-3 text-xs uppercase tracking-[0.18em] text-muted-foreground">
            <span>{t('experiment.timeline.title')}</span>
            <span className="shrink-0">
              {t('experiment.timeline.step')} {currentStep}
            </span>
          </div>
          <Slider
            data-testid="replay-timeline-slider"
            value={[sliderValue]}
            min={minStep}
            max={sliderMax}
            step={1}
            onValueCommit={(value) => {
              const next = value[0]
              if (next != null) {
                onSeek(next)
              }
            }}
            disabled={!available || loading}
            aria-label={t('experiment.replay.seek')}
          />
          <div data-testid="replay-timeline-event-markers" className="relative h-4">
            {timeline.events.map((event) => {
              const range = Math.max(maxStep - minStep, 1)
              const position =
                maxStep > minStep
                  ? Math.min(100, Math.max(0, ((event.step_id - minStep) / range) * 100))
                  : 0
              return (
                <span
                  key={`${event.event_type}-${event.step_id}`}
                  data-testid="replay-event-marker"
                  title={`${event.label} · ${t('experiment.timeline.step')} ${event.step_id}`}
                  className="absolute top-0 size-2 -translate-x-1/2 rounded-full bg-[var(--console-accent-strong)]"
                  style={{ left: `${position}%` }}
                />
              )
            })}
          </div>
        </div>

        <div
          data-testid="replay-timeline-right"
          className="flex flex-wrap items-center gap-2 md:justify-end"
        >
          <Badge variant="secondary">{t('experiment.replay.badge')}</Badge>
          <Badge variant="outline">
            {t('experiment.timeline.step')} {currentStep} / {maxStep}
          </Badge>
          <Select
            value={String(session?.speed ?? 1)}
            onValueChange={(value) => {
              onSetSpeed(Number(value))
            }}
            disabled={!available}
          >
            <SelectTrigger className="w-[104px] bg-background/70">
              <SelectValue placeholder={t('experiment.replay.speed')} />
            </SelectTrigger>
            <SelectContent>
              {SPEED_OPTIONS.map((speed) => (
                <SelectItem key={speed} value={String(speed)}>
                {speed}x
              </SelectItem>
            ))}
          </SelectContent>
          </Select>
        </div>
      </CardContent>
    </Card>
  )
}
