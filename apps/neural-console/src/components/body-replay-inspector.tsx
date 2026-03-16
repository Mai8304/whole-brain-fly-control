import { ChevronLeftIcon, ChevronRightIcon, PauseIcon, PlayIcon, RotateCcwIcon } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Slider } from '@/components/ui/slider'
import { useConsolePreferences } from '@/providers/console-preferences-provider'
import type { ClosedLoopSummaryPayload, ReplayCameraPreset, ReplaySessionPayload } from '@/types/console'

const CAMERA_PRESETS: ReplayCameraPreset[] = ['follow', 'side', 'top', 'front-quarter']
const SPEED_OPTIONS = [0.25, 0.5, 1, 2]

interface StatusField {
  label: string
  value: string
}

interface BodyReplayInspectorProps {
  available: boolean
  session: ReplaySessionPayload | null
  frameSrc: string
  loading: boolean
  errorMessage: string | null
  summary: ClosedLoopSummaryPayload
  statusFields: StatusField[]
  videoSrc: string
  onPlayPause: () => void
  onPrevStep: () => void
  onNextStep: () => void
  onSeek: (step: number) => void
  onSetCamera: (camera: ReplayCameraPreset) => void
  onSetSpeed: (speed: number) => void
  onResetView: () => void
}

export function BodyReplayInspector({
  available,
  session,
  frameSrc,
  loading,
  errorMessage,
  summary,
  statusFields,
  videoSrc,
  onPlayPause,
  onPrevStep,
  onNextStep,
  onSeek,
  onSetCamera,
  onSetSpeed,
  onResetView,
}: BodyReplayInspectorProps) {
  const { t } = useConsolePreferences()
  const maxStep = Math.max(session?.steps_completed ?? summary.steps_completed ?? 0, 1)
  const currentStep = session?.current_step ?? summary.step_id ?? 0
  const isPlaying = session?.status === 'playing'

  return (
    <div data-testid="replay-inspector-root" className="console-video-panel min-w-0">
      <div className="grid gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="secondary">{t('experiment.replay.badge')}</Badge>
          <Badge variant="outline">
            {t('experiment.timeline.step')} {currentStep} / {maxStep}
          </Badge>
          {session ? <Badge variant="outline">{t(cameraLabelKey(session.camera))}</Badge> : null}
        </div>
        {statusFields.length ? (
          <div data-testid="replay-status-strip" className="console-status-strip w-full justify-start">
            {statusFields.map((field) => (
              <span key={`${field.label}-${field.value}`}>
                {field.label}: {field.value}
              </span>
            ))}
          </div>
        ) : null}
      </div>

      <div data-testid="replay-control-grid" className="grid min-w-0 gap-3">
        <div className="grid gap-3 md:grid-cols-[auto_auto_auto_minmax(0,1fr)]">
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
          <div className="grid min-w-0 gap-2">
            <div className="flex items-center justify-between gap-3 text-xs uppercase tracking-[0.18em] text-muted-foreground">
              <span>{t('experiment.replay.seek')}</span>
              <span className="shrink-0">
                {t('experiment.timeline.step')} {currentStep}
              </span>
            </div>
            <Slider
              value={[currentStep]}
              min={1}
              max={maxStep}
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
          </div>
        </div>

        <div className="grid gap-3 sm:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto]">
          <Select
            value={String(session?.speed ?? 1)}
            onValueChange={(value) => {
              onSetSpeed(Number(value))
            }}
            disabled={!available}
          >
            <SelectTrigger className="w-full bg-background/70">
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
          <Select
            value={session?.camera ?? 'follow'}
            onValueChange={(value) => {
              onSetCamera(value as ReplayCameraPreset)
            }}
            disabled={!available || loading}
          >
            <SelectTrigger className="w-full bg-background/70">
              <SelectValue placeholder={t('experiment.replay.camera')} />
            </SelectTrigger>
            <SelectContent>
              {CAMERA_PRESETS.map((camera) => (
                <SelectItem key={camera} value={camera}>
                  {t(cameraLabelKey(camera))}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button variant="outline" onClick={onResetView} disabled={!available || loading}>
            <RotateCcwIcon className="size-4" />
            {t('experiment.replay.resetView')}
          </Button>
        </div>
      </div>

      <div className="console-video-frame">
        {available && frameSrc ? (
          <img
            data-testid="replay-frame"
            className="aspect-video w-full object-cover"
            src={frameSrc}
            alt={t('experiment.replay.frameAlt')}
          />
        ) : videoSrc ? (
          <video
            className="aspect-video w-full object-cover"
            controls
            muted
            loop
            playsInline
            autoPlay
            src={videoSrc}
            title="Fly rollout video"
          >
            浏览器无法播放当前 rollout.mp4（视频文件）。
          </video>
        ) : (
          <div className="flex aspect-video items-center justify-center px-6 text-center text-sm text-muted-foreground">
            {errorMessage ?? t('experiment.body.videoUnavailable')}
          </div>
        )}
      </div>
    </div>
  )
}

function cameraLabelKey(camera: ReplayCameraPreset) {
  return `experiment.replay.camera.${camera}` as const
}
