import { lazy, Suspense, useState } from 'react'

import { BodyReplayInspector } from '@/components/body-replay-inspector'
import { ConsolePageHeader } from '@/components/console-page-header'
import { ReplayTimeline } from '@/components/replay-timeline'
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
  BrainRegionPayload,
  DisplayRegionActivityPayload,
  BrainTopNodePayload,
  BrainViewPayload,
  ConsoleAction,
  ConsoleField,
  ConsolePanel,
  PipelineStagePayload,
  TimelinePayload,
} from '@/types/console'

const BrainShellViewport = lazy(async () => {
  const module = await import('@/components/brain-shell-viewport')
  return { default: module.BrainShellViewport }
})

interface ExperimentConsolePageProps {
  brainAssets: BrainAssetManifestPayload | null
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
  brainView,
  errorMessage,
  executionLog,
  leftPanels,
  pipeline: _pipeline,
  sourceStatus,
  summary,
  timeline,
  videoSrc,
  replay,
}: ExperimentConsolePageProps) {
  const { t } = useConsolePreferences()
  const [showFormalNeuropilDetail, setShowFormalNeuropilDetail] = useState(false)
  const unavailableLabel = t('shared.unavailable')
  const hasRecordedBrainActivity =
    sourceStatus === 'LIVE API' && brainView.data_status !== 'unavailable'
  const hasRecordedSummary = sourceStatus === 'LIVE API' && summary.data_status !== 'unavailable'
  const viewportGlowAvailable =
    brainView.graph_scope_validation_passed === true &&
    (brainView.display_region_activity?.length ?? 0) > 0
  const groupedSummary = getSortedDisplayRegionActivity(brainView.display_region_activity)
  const brainViewProvenance = formatBrainViewProvenance(brainView, t)
  const environmentFields = getTranslatedStatusFields(leftPanels, 'environment', t)
  const sensoryFields = getTranslatedStatusFields(leftPanels, 'sensory', t)

  return (
    <div className="grid gap-4">
      <ConsolePageHeader
        title={t('experiment.header.title')}
        description={t('experiment.header.description')}
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
                  <BrainShellViewport
                    shell={brainView.shell}
                    brainAssets={brainAssets}
                    displayRegionActivity={brainView.display_region_activity ?? []}
                    glowAvailable={viewportGlowAvailable}
                  />
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
                            value={formatNumber(brainView.afferent_activity, unavailableLabel)}
                          />
                          <MetricRow
                            label={t('experiment.brain.metric.intrinsic')}
                            value={formatNumber(brainView.intrinsic_activity, unavailableLabel)}
                          />
                          <MetricRow
                            label={t('experiment.brain.metric.efferent')}
                            value={formatNumber(brainView.efferent_activity, unavailableLabel)}
                          />
                          <Separator />
                          {groupedSummary.map((region) => (
                            <MetricRow
                              key={region.group_neuropil_id}
                              label={region.group_neuropil_id}
                              value={formatGroupedRegionSummary(region, t, unavailableLabel)}
                            />
                          ))}
                          <Separator />
                          <MetricRow
                            label={t('experiment.brain.metric.coverage')}
                            value={`${formatInteger(
                              brainView.mapping_coverage.neuropil_mapped_nodes,
                            )} / ${formatInteger(brainView.mapping_coverage.total_nodes)}`}
                          />
                          {brainViewProvenance ? (
                            <MetricRow
                              label={t('experiment.brain.metric.provenance')}
                              value={brainViewProvenance}
                            />
                          ) : null}
                          <MetricRow
                            label={t('experiment.brain.metric.shellAsset')}
                            value={brainView.shell?.asset_id ?? unavailableLabel}
                          />
                          <MetricRow
                            label={t('experiment.brain.metric.shellFormat')}
                            value={brainAssets?.shell.render_format.toUpperCase() ?? unavailableLabel}
                          />
                          <MetricRow
                            label={t('experiment.brain.metric.neuropilManifest')}
                            value={brainAssets ? String(brainAssets.neuropil_manifest.length) : unavailableLabel}
                          />
                          <MetricRow
                            label={t('experiment.brain.metric.topNodeMemberships')}
                            value={
                              brainView.top_nodes.length
                                ? brainView.top_nodes
                                    .map((node) =>
                                      formatTopNodeMembershipSummary(node, t, unavailableLabel),
                                    )
                                    .join('; ')
                                : unavailableLabel
                            }
                          />
                          <Separator />
                          <div className="grid gap-3">
                            <Button
                              type="button"
                              variant="outline"
                              className="w-full justify-between text-left"
                              aria-expanded={showFormalNeuropilDetail}
                              onClick={() =>
                                setShowFormalNeuropilDetail((current) => !current)
                              }
                            >
                              <span>Formal Neuropil Detail（正式神经纤维区明细）</span>
                              <span className="text-xs text-muted-foreground">
                                {showFormalNeuropilDetail ? '−' : '+'}
                              </span>
                            </Button>
                            {showFormalNeuropilDetail ? (
                              <div className="grid gap-3 rounded-lg border border-border/60 bg-background/50 p-3">
                                <p className="text-xs text-muted-foreground">
                                  Fine-grained formal data（细粒度正式数据）; not the grouped 3D glow
                                  layer.
                                </p>
                                {brainView.top_regions.length ? (
                                  brainView.top_regions.map((region) => (
                                    <MetricRow
                                      key={`formal-${region.neuropil_id}`}
                                      label={region.neuropil_id}
                                      value={formatRegionSummary(region, t, unavailableLabel)}
                                    />
                                  ))
                                ) : (
                                  <p className="text-sm text-muted-foreground">{unavailableLabel}</p>
                                )}
                              </div>
                            ) : null}
                          </div>
                        </>
                      ) : (
                        <div className="console-empty-state px-3 py-4 text-sm text-muted-foreground">
                          {t('experiment.brain.unavailable')}
                        </div>
                      )}
                    </div>
                  </section>
                </div>
              </CardContent>
            </Card>

            <ReplayTimeline
              available={replay.available}
              session={replay.session}
              timeline={timeline}
              loading={replay.loading}
              onPlayPause={replay.onPlayPause}
              onPrevStep={replay.onPrevStep}
              onNextStep={replay.onNextStep}
              onSeek={replay.onSeek}
              onSetSpeed={replay.onSetSpeed}
            />

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
                  statusFields={[...environmentFields, ...sensoryFields]}
                  videoSrc={videoSrc}
                  onSetCamera={replay.onSetCamera}
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
                            value={formatNumber(summary.reward, unavailableLabel)}
                          />
                        ) : null}
                        <MetricRow
                          label={t('experiment.body.metric.rewardMean')}
                          value={formatNumber(summary.reward_mean, unavailableLabel)}
                        />
                        <MetricRow
                          label={t('experiment.body.metric.terminated')}
                          value={String(summary.terminated_early)}
                        />
                        <MetricRow
                          label={t('experiment.body.metric.forwardVelocity')}
                          value={formatNumber(
                            summary.forward_velocity ?? summary.forward_velocity_mean,
                            unavailableLabel,
                          )}
                        />
                        <MetricRow
                          label={t('experiment.body.metric.velocityStd')}
                          value={formatNumber(summary.forward_velocity_std, unavailableLabel)}
                        />
                        <MetricRow
                          label={t('experiment.body.metric.uprightness')}
                          value={formatNumber(
                            summary.body_upright ?? summary.body_upright_mean,
                            unavailableLabel,
                          )}
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

}

function getTranslatedStatusFields(
  panels: ConsolePanel[],
  panelId: string,
  t: (key: string) => string,
) {
  return (
    panels.find((panel) => panel.id === panelId)?.fields?.map((field) => ({
      label: field.labelKey ? t(field.labelKey) : field.label,
      value: field.value,
    })) ?? []
  )
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
              <LabeledField key={`${panel.id ?? title}-${field.labelKey ?? field.label}`} field={field} />
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

function formatNumber(value: number | null | undefined, unavailableLabel: string) {
  return value == null ? unavailableLabel : value.toFixed(2)
}

function formatInteger(value: number) {
  return new Intl.NumberFormat('en-US').format(value)
}

function signed(value: number) {
  return `${value >= 0 ? '+' : ''}${value.toFixed(2)}`
}

function formatSigned(
  value: number | null | undefined,
  unavailableLabel: string,
) {
  return value == null ? unavailableLabel : signed(value)
}

export function formatRegionSummary(
  region: BrainRegionPayload,
  t: (key: string) => string,
  unavailableLabel: string,
) {
  const parts = [
    `${formatNumber(region.raw_activity_mass, unavailableLabel)} ${t(
      'experiment.brain.metric.activityMass',
    ).toLowerCase()}`,
    `${formatSigned(region.signed_activity, unavailableLabel)} ${t(
      'experiment.brain.metric.signedActivity',
    ).toLowerCase()}`,
  ]
  if (region.is_display_grouped) {
    parts.push(
      `${t('experiment.brain.metric.displayGrouping').toLowerCase()}: ${region.display_name}`,
    )
  }
  return parts.join(' | ')
}

function formatGroupedRegionSummary(
  region: DisplayRegionActivityPayload,
  t: (key: string) => string,
  unavailableLabel: string,
) {
  return [
    `${formatNumber(region.raw_activity_mass, unavailableLabel)} ${t(
      'experiment.brain.metric.activityMass',
    ).toLowerCase()}`,
    `${formatSigned(region.signed_activity, unavailableLabel)} ${t(
      'experiment.brain.metric.signedActivity',
    ).toLowerCase()}`,
  ].join(' | ')
}

function getSortedDisplayRegionActivity(
  regions?: DisplayRegionActivityPayload[],
): DisplayRegionActivityPayload[] {
  return [...(regions ?? [])].sort(
    (a, b) => b.raw_activity_mass - a.raw_activity_mass,
  )
}

function formatTopNodeMembershipSummary(
  node: BrainTopNodePayload,
  t: (key: string) => string,
  unavailableLabel: string,
) {
  const memberships = node.neuropil_memberships.length
    ? node.neuropil_memberships
        .map(
          (membership) =>
            `${membership.neuropil} ${formatNumber(
              membership.occupancy_fraction,
              unavailableLabel,
            )}`,
        )
        .join(', ')
    : unavailableLabel
  const displayGroup = node.display_group_hint
    ? ` | ${t('experiment.brain.metric.displayGrouping').toLowerCase()}: ${node.display_group_hint}`
    : ''
  return `${node.flow_role}:${node.node_idx} | ${memberships}${displayGroup}`
}

function formatBrainViewProvenance(
  brainView: BrainViewPayload,
  t: (key: string) => string,
) {
  if (brainView.artifact_contract_version == null || brainView.artifact_origin == null) {
    return null
  }
  return `${t('experiment.brain.provenance.formalTruth')} · ${t(
    'experiment.brain.provenance.contract',
  )} v${brainView.artifact_contract_version} · ${brainView.artifact_origin}`
}
