import { lazy, Suspense } from 'react'

import { BodyReplayInspector } from '@/components/body-replay-inspector'
import { ConsolePageHeader } from '@/components/console-page-header'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { useConsolePreferences } from '@/providers/console-preferences-provider'
import type {
  BrainAssetManifestPayload,
  BrainViewPayload,
  ConsoleAction,
  ConsoleField,
  ConsolePanel,
  PipelineStagePayload,
  RoiAssetPackPayload,
  TimelinePayload,
} from '@/types/console'

const BrainShellViewport = lazy(async () => {
  const module = await import('@/components/brain-shell-viewport')
  return { default: module.BrainShellViewport }
})

interface ExperimentConsolePageProps {
  brainAssets: BrainAssetManifestPayload | null
  roiAssets: RoiAssetPackPayload | null
  brainView: BrainViewPayload
  errorMessage: string | null
  executionLog: string[]
  leftPanels: ConsolePanel[]
  pipeline: PipelineStagePayload[]
  sourceStatus: 'API UNAVAILABLE' | 'LIVE API' | 'LOADING' | 'MOCK FALLBACK'
  summary: {
    step_id?: number
    reward?: number
    forward_velocity?: number
    body_upright?: number
    terminated?: boolean
    data_status?: 'recorded' | 'unavailable'
    status: string
    task: string
    steps_requested: number
    steps_completed: number
    terminated_early: boolean
    reward_mean: number
    final_reward: number
    mean_action_norm: number
    forward_velocity_mean: number
    forward_velocity_std: number
    body_upright_mean: number
    final_heading_delta: number
  }
  timeline: TimelinePayload
  videoSrc: string
  replay: {
    available: boolean
    session: {
      session_id: string
      task: string
      default_camera: 'follow' | 'side' | 'top' | 'front-quarter'
      steps_requested: number
      steps_completed: number
      current_step: number
      status: 'paused' | 'playing'
      speed: number
      camera: 'follow' | 'side' | 'top' | 'front-quarter'
    } | null
    frameSrc: string
    loading: boolean
    errorMessage: string | null
    onPlayPause: () => void
    onPrevStep: () => void
    onNextStep: () => void
    onSeek: (step: number) => void
    onSetCamera: (camera: 'follow' | 'side' | 'top' | 'front-quarter') => void
    onSetSpeed: (speed: number) => void
    onResetView: () => void
  }
}

export function ExperimentConsolePage({
  brainAssets,
  roiAssets,
  brainView,
  errorMessage,
  executionLog,
  leftPanels,
  pipeline,
  sourceStatus,
  summary,
  timeline,
  videoSrc,
  replay,
}: ExperimentConsolePageProps) {
  const { t } = useConsolePreferences()
  const timelineProgress =
    timeline.steps_requested > 0 ? (timeline.current_step / timeline.steps_requested) * 100 : 0
  const hasRecordedBrainActivity =
    sourceStatus === 'LIVE API' && brainView.data_status !== 'unavailable'
  const hasRecordedTimeline = sourceStatus === 'LIVE API' && timeline.data_status !== 'unavailable'
  const hasRecordedSummary = sourceStatus === 'LIVE API' && summary.data_status !== 'unavailable'
  const environmentFields =
    leftPanels.find((panel) => panel.title === 'Environment Physics')?.fields?.map((field) => ({
      label: translateFieldLabel(field),
      value: field.value,
    })) ?? []
  const sensoryFields =
    leftPanels.find((panel) => panel.title === 'Sensory Inputs')?.fields?.map((field) => ({
      label:
        translateFieldLabel(field) === t('field.temperature')
          ? 'Temp'
          : translateFieldLabel(field),
      value: field.value,
    })) ?? []

  return (
    <div className="grid gap-4">
      <ConsolePageHeader
        title={t('experiment.header.title')}
        description={t('experiment.header.description')}
        metrics={[
          {
            label: t('app.metric.status'),
            value: t('app.status.ready'),
            tone: 'success',
          },
          {
            label: t('app.metric.session'),
            value: summary.task || 'straight_walking_v1',
          },
          {
            label: t('app.metric.dataSource'),
            value: translateSourceStatus(sourceStatus, t),
            tone:
              sourceStatus === 'LIVE API'
                ? 'info'
                : sourceStatus === 'API UNAVAILABLE'
                  ? 'danger'
                  : sourceStatus === 'LOADING'
                    ? 'warning'
                    : 'warning',
          },
          {
            label: t('app.metric.pendingChanges'),
            value: sourceStatus === 'LIVE API' ? '0' : '3',
            tone: sourceStatus === 'LIVE API' ? 'success' : 'warning',
          },
        ]}
      />

      {sourceStatus === 'API UNAVAILABLE' && errorMessage ? (
        <Card className="console-panel border border-rose-500/25 bg-rose-500/8 shadow-none">
          <CardHeader className="pb-3">
            <CardTitle>{t('experiment.strict.title')}</CardTitle>
            <CardDescription>{t('experiment.strict.description')}</CardDescription>
          </CardHeader>
          <CardContent className="text-sm text-rose-200 dark:text-rose-100">
            {errorMessage}
          </CardContent>
        </Card>
      ) : null}

      <Card className="console-panel border-none shadow-none">
        <CardHeader className="pb-3">
          <CardTitle>{t('experiment.pipeline.title')}</CardTitle>
          <CardDescription>{t('experiment.pipeline.description')}</CardDescription>
        </CardHeader>
        <CardContent>
          {pipeline.length ? (
            <div className="grid gap-3 lg:grid-cols-6">
              {pipeline.map((stage, index) => (
                <PipelineStage key={stage.name} stage={stage} index={index} />
              ))}
            </div>
          ) : (
            <div className="console-empty-state px-4 py-6 text-sm text-muted-foreground">
              Awaiting live pipeline data…
            </div>
          )}
        </CardContent>
      </Card>

      <main
        data-testid="experiment-layout"
        className="grid items-start gap-4 xl:grid-cols-[380px_minmax(0,1fr)]"
      >
        <section className="grid self-start gap-4">
          {leftPanels.map((panel) => (
            <ConsolePanelCard key={panel.title} panel={panel} />
          ))}
        </section>

        <section className="grid self-start gap-4">
          <div data-testid="experiment-right-stack" className="grid self-start gap-4">
            <Card
              data-testid="experiment-brain-card"
              className="console-panel border-none shadow-none"
            >
              <CardHeader className="pb-3">
                <CardTitle>{t('experiment.brain.title')}</CardTitle>
                <CardDescription>{t('experiment.brain.description')}</CardDescription>
              </CardHeader>
              <CardContent className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_320px]">
                <Suspense
                  fallback={
                    <div className="console-viewport-frame">
                      <div className="flex h-full items-center justify-center text-sm text-muted-foreground">
                        {t('experiment.brain.loading')}
                      </div>
                    </div>
                  }
                >
                  <BrainShellViewport shell={brainView.shell} brainAssets={brainAssets} />
                </Suspense>

                <div className="grid gap-4">
                  <section className="console-detail-section">
                    <div className="console-detail-header">
                      <h3 className="text-sm font-semibold text-foreground">
                        {t('experiment.brain.explanation.title')}
                      </h3>
                      <p className="text-sm text-muted-foreground">
                        {t('experiment.brain.explanation.description')}
                      </p>
                    </div>
                    <Separator className="my-3" />
                    <div className="grid gap-3 text-sm">
                      {hasRecordedBrainActivity ? (
                        <>
                          <MetricRow
                            label={t('experiment.brain.metric.afferent')}
                            value={formatNumber(brainView.afferent_activity)}
                          />
                          <MetricRow
                            label={t('experiment.brain.metric.intrinsic')}
                            value={formatNumber(brainView.intrinsic_activity)}
                          />
                          <MetricRow
                            label={t('experiment.brain.metric.efferent')}
                            value={formatNumber(brainView.efferent_activity)}
                          />
                          <Separator />
                          {brainView.top_regions.map((region) => (
                            <MetricRow
                              key={region.roi_id}
                              label={region.roi_id}
                              value={`${formatNumber(region.activity_value)} (${signed(region.activity_delta)})`}
                            />
                          ))}
                          <Separator />
                          <MetricRow
                            label={t('experiment.brain.metric.coverage')}
                            value={`${formatInteger(
                              brainView.mapping_coverage.roi_mapped_nodes,
                            )} / ${formatInteger(brainView.mapping_coverage.total_nodes)}`}
                          />
                          <MetricRow
                            label={t('experiment.brain.metric.shellAsset')}
                            value={brainView.shell?.asset_id ?? 'not configured'}
                          />
                          <MetricRow
                            label={t('experiment.brain.metric.shellFormat')}
                            value={brainAssets?.shell.render_format.toUpperCase() ?? 'n/a'}
                          />
                          <MetricRow
                            label={t('experiment.brain.metric.neuropilManifest')}
                            value={brainAssets ? String(brainAssets.roi_manifest.length) : 'n/a'}
                          />
                          <MetricRow
                            label={t('experiment.brain.metric.meshPack')}
                            value={roiAssets ? `${roiAssets.roi_meshes.length} meshes` : 'n/a'}
                          />
                          <MetricRow
                            label={t('experiment.brain.metric.topNeuropils')}
                            value={brainView.top_nodes
                              .map((node) => `${node.flow_role}:${node.node_idx}`)
                              .join(', ')}
                          />
                        </>
                      ) : (
                        <div className="console-empty-state px-3 py-4 text-sm text-muted-foreground">
                          {t('experiment.brain.unavailable')}
                        </div>
                      )}
                    </div>
                  </section>

                  <section className="console-detail-section">
                    <div className="console-detail-header">
                      <h3 className="text-sm font-semibold text-foreground">
                        {t('experiment.timeline.title')}
                      </h3>
                      <p className="text-sm text-muted-foreground">
                        {t('experiment.timeline.description')}
                      </p>
                    </div>
                    <Separator className="my-3" />
                    <div className="space-y-3 text-sm">
                      {hasRecordedTimeline ? (
                        <>
                          <div className="h-2 rounded-full bg-muted/70">
                            <div
                              className="h-2 rounded-full bg-[var(--console-accent-strong)]"
                              style={{ width: `${timelineProgress}%` }}
                            />
                          </div>
                          <div className="flex justify-between text-xs uppercase tracking-[0.18em] text-muted-foreground">
                            <span>
                              {t('experiment.timeline.step')} 0
                            </span>
                            <span>
                              {t('experiment.timeline.step')} {timeline.steps_requested}
                            </span>
                          </div>
                          <div className="grid gap-2">
                            {timeline.events.map((event) => (
                              <div
                                key={`${event.event_type}-${event.step_id}`}
                                className="rounded-xl border border-border/80 bg-background/65 px-3 py-2"
                              >
                                <div className="flex items-center justify-between gap-4">
                                  <span className="text-foreground">{event.label}</span>
                                  <span className="text-xs uppercase tracking-[0.18em] text-muted-foreground">
                                    {t('experiment.timeline.step')} {event.step_id}
                                  </span>
                                </div>
                              </div>
                            ))}
                          </div>
                        </>
                      ) : (
                        <div className="console-empty-state px-3 py-4 text-sm text-muted-foreground">
                          {t('experiment.timeline.unavailable')}
                        </div>
                      )}
                    </div>
                  </section>
                </div>
              </CardContent>
            </Card>

            <Card
              data-testid="experiment-body-card"
              className="console-panel border-none shadow-none"
            >
              <CardHeader className="pb-3">
                <CardTitle>{t('experiment.body.title')}</CardTitle>
                <CardDescription>{t('experiment.body.description')}</CardDescription>
              </CardHeader>
              <CardContent className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_320px]">
                <BodyReplayInspector
                  available={replay.available}
                  session={replay.session}
                  frameSrc={replay.frameSrc}
                  loading={replay.loading}
                  errorMessage={replay.errorMessage}
                  summary={summary}
                  statusFields={[...environmentFields, ...sensoryFields]}
                  videoSrc={videoSrc}
                  onPlayPause={replay.onPlayPause}
                  onPrevStep={replay.onPrevStep}
                  onNextStep={replay.onNextStep}
                  onSeek={replay.onSeek}
                  onSetCamera={replay.onSetCamera}
                  onSetSpeed={replay.onSetSpeed}
                  onResetView={replay.onResetView}
                />

                <div className="grid gap-4">
                  <section className="console-detail-section">
                    <div className="console-detail-header">
                      <h3 className="text-sm font-semibold text-foreground">
                        {t('experiment.body.summary.title')}
                      </h3>
                      <p className="text-sm text-muted-foreground">
                        {t('experiment.body.summary.description')}
                      </p>
                    </div>
                    <Separator className="my-3" />
                    {hasRecordedSummary ? (
                      <div className="grid gap-3 text-sm">
                        {summary.step_id != null ? (
                          <>
                            <MetricRow
                              label={t('experiment.timeline.step')}
                              value={`${summary.step_id} / ${summary.steps_completed}`}
                            />
                            <MetricRow
                              label={t('experiment.body.metric.terminated')}
                              value={summary.terminated != null ? String(summary.terminated) : 'false'}
                            />
                            <Separator />
                          </>
                        ) : null}
                        <MetricRow
                          label={t('experiment.body.metric.steps')}
                          value={`${summary.steps_completed} / ${summary.steps_requested}`}
                        />
                        {summary.reward != null ? (
                          <MetricRow
                            label={t('experiment.body.metric.rewardMean')}
                            value={formatNumber(summary.reward)}
                          />
                        ) : null}
                        <MetricRow
                          label={t('experiment.body.metric.rewardMean')}
                          value={formatNumber(summary.reward_mean)}
                        />
                        <MetricRow
                          label={t('experiment.body.metric.terminated')}
                          value={String(summary.terminated_early)}
                        />
                        <MetricRow
                          label={t('experiment.body.metric.forwardVelocity')}
                          value={formatNumber(summary.forward_velocity ?? summary.forward_velocity_mean)}
                        />
                        <MetricRow
                          label={t('experiment.body.metric.velocityStd')}
                          value={formatNumber(summary.forward_velocity_std)}
                        />
                        <MetricRow
                          label={t('experiment.body.metric.uprightness')}
                          value={formatNumber(summary.body_upright ?? summary.body_upright_mean)}
                        />
                        <MetricRow
                          label={t('experiment.body.metric.headingDrift')}
                          value={signed(summary.final_heading_delta)}
                        />
                      </div>
                    ) : (
                      <p className="text-sm text-muted-foreground">
                        {t('experiment.body.summaryUnavailable')}
                      </p>
                    )}
                  </section>

                  <section className="console-detail-section">
                    <div className="console-detail-header">
                      <h3 className="text-sm font-semibold text-foreground">
                        {t('experiment.log.title')}
                      </h3>
                      <p className="text-sm text-muted-foreground">
                        {t('experiment.log.description')}
                      </p>
                    </div>
                    <Separator className="my-3" />
                    <div className="grid gap-2 text-sm">
                      {executionLog.map((line) => (
                        <p key={line} className="text-muted-foreground">
                          {line}
                        </p>
                      ))}
                    </div>
                  </section>
                </div>
              </CardContent>
            </Card>
          </div>
        </section>
      </main>
    </div>
  )

  function translateFieldLabel(field: ConsoleField) {
    return field.labelKey ? t(field.labelKey) : field.label
  }
}

function ConsolePanelCard({ panel }: { panel: ConsolePanel }) {
  const { t } = useConsolePreferences()
  const title = panel.titleKey ? t(panel.titleKey) : panel.title
  const description = panel.descriptionKey ? t(panel.descriptionKey) : panel.description
  const note = panel.noteKey ? t(panel.noteKey) : panel.note

  return (
    <Card className="console-panel border-none shadow-none">
      <CardHeader className="pb-3">
        <CardTitle>{title}</CardTitle>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardContent className="grid gap-4">
        {panel.fields ? (
          <div className="grid gap-3">
            {panel.fields.map((field) => (
              <LabeledField key={`${title}-${field.label}`} field={field} />
            ))}
          </div>
        ) : null}

        {panel.actions ? (
          <div className="flex flex-wrap gap-2">
            {panel.actions.map((action) => (
              <ActionChip key={action.label} action={action} />
            ))}
          </div>
        ) : null}

        {panel.lines ? (
          <ul className="grid gap-2 text-sm text-muted-foreground">
            {panel.lines.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
        ) : null}

        {note ? <p className="text-xs text-muted-foreground">{note}</p> : null}
      </CardContent>
    </Card>
  )
}

function PipelineStage({ stage, index }: { stage: PipelineStagePayload; index: number }) {
  const { t } = useConsolePreferences()
  const tone =
    stage.status === 'done'
      ? 'border-emerald-500/25 bg-emerald-500/10'
      : stage.status === 'running'
        ? 'border-[var(--console-accent-strong)]/25 bg-[var(--console-accent-strong)]/10'
        : 'border-border/80 bg-background/70'

  return (
    <div className={`rounded-2xl border px-3 py-3 ${tone}`}>
      <div className="console-kicker">Stage {index + 1}</div>
      <div className="mt-2 text-sm font-medium text-foreground">
        {translatePipelineStage(stage.name, t)}
      </div>
      <div className="mt-3 text-xs uppercase tracking-[0.18em] text-muted-foreground">
        {stage.status}
      </div>
    </div>
  )
}

function LabeledField({ field }: { field: ConsoleField }) {
  const { t } = useConsolePreferences()
  const label = field.labelKey ? t(field.labelKey) : field.label
  const helper = field.helperKey ? t(field.helperKey) : field.helper

  return (
    <div className="grid gap-1.5">
      <Label className="text-xs uppercase tracking-[0.18em] text-muted-foreground">{label}</Label>
      <Input value={field.value} readOnly className="bg-background/70" />
      {helper ? <p className="text-xs text-muted-foreground">{helper}</p> : null}
    </div>
  )
}

function ActionChip({ action }: { action: ConsoleAction }) {
  const { t } = useConsolePreferences()
  const label = action.labelKey ? t(action.labelKey) : action.label
  return <Button variant={action.variant ?? 'default'}>{label}</Button>
}

function MetricRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-center justify-between gap-4">
      <span className="text-muted-foreground">{label}</span>
      <span className="text-right font-medium text-foreground">{value}</span>
    </div>
  )
}

function translatePipelineStage(name: string, t: (key: string) => string) {
  const mapping: Record<string, string> = {
    'Environment / Input': 'pipeline.environmentInput',
    Afferent: 'pipeline.afferent',
    'Whole-Brain': 'pipeline.wholeBrain',
    Efferent: 'pipeline.efferent',
    Decoder: 'pipeline.decoder',
    Body: 'pipeline.body',
  }

  return mapping[name] ? t(mapping[name]) : name
}

function translateSourceStatus(
  sourceStatus: ExperimentConsolePageProps['sourceStatus'],
  t: (key: string) => string,
) {
  switch (sourceStatus) {
    case 'LIVE API':
      return t('app.status.liveApi')
    case 'API UNAVAILABLE':
      return t('app.status.apiUnavailable')
    case 'LOADING':
      return t('app.status.loading')
    default:
      return t('app.status.mockFallback')
  }
}

function formatNumber(value: number | null) {
  return value === null ? 'n/a' : value.toFixed(2)
}

function formatInteger(value: number) {
  return new Intl.NumberFormat('en-US').format(value)
}

function signed(value: number) {
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}`
}
