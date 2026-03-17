import { RotateCcwIcon } from 'lucide-react'

import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { useConsolePreferences } from '@/providers/console-preferences-provider'
import type { ReplayCameraPreset, ReplaySessionPayload } from '@/types/console'

const CAMERA_PRESETS: ReplayCameraPreset[] = ['follow', 'side', 'top', 'front-quarter']

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
  statusFields: StatusField[]
  videoSrc: string
  onSetCamera: (camera: ReplayCameraPreset) => void
  onResetView: () => void
}

export function BodyReplayInspector({
  available,
  session,
  frameSrc,
  loading,
  errorMessage,
  statusFields,
  videoSrc,
  onSetCamera,
  onResetView,
}: BodyReplayInspectorProps) {
  const { t } = useConsolePreferences()

  return (
    <div data-testid="replay-inspector-root" className="console-video-panel min-w-0">
      <div className="grid gap-3">
        <div className="flex flex-wrap items-center gap-2">
          <Badge variant="secondary">{t('experiment.replay.badge')}</Badge>
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

      <div data-testid="replay-local-controls" className="grid min-w-0 gap-3 sm:grid-cols-[minmax(0,1fr)_auto]">
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
          <Button
            variant="outline"
            onClick={onResetView}
            disabled={!available || loading}
            className="sm:justify-self-start"
          >
            <RotateCcwIcon className="size-4" />
            {t('experiment.replay.resetView')}
          </Button>
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
            title={t('experiment.body.videoTitle')}
          >
            {t('experiment.body.videoPlaybackUnsupported')}
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
