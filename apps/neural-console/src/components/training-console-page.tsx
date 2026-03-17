import { useMemo } from 'react'

import { DefinitionHint } from '@/components/definition-hint'
import { ConsolePageHeader } from '@/components/console-page-header'
import { Badge } from '@/components/ui/badge'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { useConsolePreferences } from '@/providers/console-preferences-provider'

export function TrainingConsolePage() {
  const { t } = useConsolePreferences()
  const sections = useMemo(() => buildTrainingSections(t), [t])

  return (
    <div className="grid gap-4">
      <ConsolePageHeader
        title={t('training.header.title')}
        description={t('training.header.description')}
      />

      <main
        data-testid="training-console-layout"
        className="grid gap-4 xl:grid-cols-[300px_minmax(0,1fr)_360px]"
      >
        <section className="grid gap-4">
          <Card className="console-panel border-none shadow-none">
            <CardHeader className="pb-3">
              <CardTitle>{t('training.navigator.title')}</CardTitle>
              <CardDescription>{t('training.navigator.description')}</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-3">
              <ol className="grid gap-3">
                {sections.map((section, index) => (
                  <li
                    key={section.id}
                    className="rounded-xl border border-border/70 bg-background/40 px-3 py-3"
                  >
                  <div className="console-kicker">
                    {index + 1}. {section.title}
                  </div>
                  <div className="mt-2 flex items-center justify-between gap-3">
                    <span className="text-sm text-foreground">{section.description}</span>
                    <Badge variant="outline">{section.state}</Badge>
                  </div>
                  </li>
                ))}
              </ol>
            </CardContent>
          </Card>
        </section>

        <section className="grid gap-4">
          {sections.map((section) => (
            <Card
              key={section.id}
              data-testid={`training-section-${section.id}`}
              className="console-panel border-none shadow-none"
            >
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between gap-4">
                  <div>
                    <CardTitle>{section.title}</CardTitle>
                    <CardDescription>{section.description}</CardDescription>
                  </div>
                  <Badge variant="outline">{section.state}</Badge>
                </div>
              </CardHeader>
              <CardContent className="grid gap-3">
                {section.primaryFields.map((field) => (
                  <TrainingFieldRow
                    key={`${section.id}-${field.label}`}
                    label={field.label}
                    definition={field.definition}
                    value={field.value}
                  />
                ))}
              </CardContent>
            </Card>
          ))}
        </section>

        <section className="grid gap-4">
          <Card data-testid="training-inspector" className="console-panel border-none shadow-none">
            <CardHeader className="pb-3">
              <CardTitle>{t('training.inspector.title')}</CardTitle>
              <CardDescription>{t('training.inspector.description')}</CardDescription>
            </CardHeader>
            <CardContent className="grid gap-4">
              {sections.map((section, index) => (
                <div key={section.id} className="grid gap-3">
                  {index ? <Separator /> : null}
                  <div>
                    <div className="console-kicker">{section.title}</div>
                    <div className="mt-1 text-sm text-muted-foreground">{section.description}</div>
                  </div>
                  {section.fullFields.map((field) => (
                    <TrainingFieldRow
                      key={`${section.id}-full-${field.label}`}
                      label={field.label}
                      definition={field.definition}
                      value={field.value}
                    />
                  ))}
                </div>
              ))}
            </CardContent>
          </Card>
        </section>
      </main>

      <Card data-testid="training-raw-panel" className="console-panel border-none shadow-none">
        <CardHeader className="pb-3">
          <CardTitle>{t('training.raw.title')}</CardTitle>
          <CardDescription>{t('training.callout.description')}</CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="config">
            <TabsList>
              <TabsTrigger value="config">{t('training.raw.config')}</TabsTrigger>
              <TabsTrigger value="status">{t('training.raw.status')}</TabsTrigger>
              <TabsTrigger value="logs">{t('training.raw.logs')}</TabsTrigger>
              <TabsTrigger value="artifacts">{t('training.raw.artifacts')}</TabsTrigger>
            </TabsList>
            <TabsContent value="config">
              <RawPanel
                value={JSON.stringify(
                  {
                    status: 'unavailable',
                    reason: 'training metadata backend pending',
                  },
                  null,
                  2,
                )}
              />
            </TabsContent>
            <TabsContent value="status">
              <RawPanel
                value={JSON.stringify(
                  {
                    data: 'missing',
                    graph: 'missing',
                    train: 'idle',
                    eval: 'idle',
                    registry: 'unregistered',
                  },
                  null,
                  2,
                )}
              />
            </TabsContent>
            <TabsContent value="logs">
              <RawPanel value="[strict] training metadata unavailable\n[strict] no fabricated job state shown" />
            </TabsContent>
            <TabsContent value="artifacts">
              <RawPanel
                value={JSON.stringify(
                  {
                    dataset: null,
                    graph: null,
                    checkpoint: null,
                    eval: null,
                    validation: null,
                  },
                  null,
                  2,
                )}
              />
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  )
}

function TrainingFieldRow({
  label,
  definition,
  value,
}: {
  label: string
  definition: string
  value: string
}) {
  return (
    <div className="console-field-row">
      <div className="flex items-center gap-2 text-xs uppercase tracking-[0.18em] text-muted-foreground">
        <span>{label}</span>
        <DefinitionHint label={label} definition={definition} />
      </div>
      <div className="console-field-value">{value}</div>
    </div>
  )
}

function RawPanel({ value }: { value: string }) {
  return (
    <pre className="mt-3 overflow-x-auto rounded-2xl border border-border/70 bg-background/70 p-4 text-xs leading-6 text-muted-foreground">
      {value}
    </pre>
  )
}

function buildTrainingSections(t: (key: string) => string) {
  return [
    {
      id: 'data',
      title: t('training.section.data.title'),
      description: t('training.section.data.description'),
      state: t('training.state.missing'),
      primaryFields: [
        field(t, 'training.field.datasetName', 'training.definition.datasetName'),
        field(t, 'training.field.sampleCount', 'training.definition.sampleCount'),
        field(t, 'training.field.contractStatus', 'training.definition.contractStatus'),
      ],
      fullFields: [
        field(t, 'training.field.datasetPath', 'training.definition.datasetPath'),
        field(t, 'training.field.datasetName', 'training.definition.datasetName'),
        field(t, 'training.field.sampleCount', 'training.definition.sampleCount'),
        field(t, 'training.field.contractStatus', 'training.definition.contractStatus'),
      ],
    },
    {
      id: 'graph',
      title: t('training.section.graph.title'),
      description: t('training.section.graph.description'),
      state: t('training.state.missing'),
      primaryFields: [
        field(t, 'training.field.compiledGraphDir', 'training.definition.compiledGraphDir'),
        field(t, 'training.field.nodeCount', 'training.definition.nodeCount'),
        field(t, 'training.field.compileStatus', 'training.definition.compileStatus'),
      ],
      fullFields: [
        field(t, 'training.field.snapshotDir', 'training.definition.snapshotDir'),
        field(t, 'training.field.compiledGraphDir', 'training.definition.compiledGraphDir'),
        field(t, 'training.field.nodeCount', 'training.definition.nodeCount'),
        field(t, 'training.field.compileStatus', 'training.definition.compileStatus'),
      ],
    },
    {
      id: 'train',
      title: t('training.section.train.title'),
      description: t('training.section.train.description'),
      state: t('training.state.idle'),
      primaryFields: [
        field(t, 'training.field.taskFamily', 'training.definition.taskFamily'),
        field(t, 'training.field.taskVariant', 'training.definition.taskVariant'),
        field(t, 'training.field.trainStatus', 'training.definition.trainStatus'),
        field(t, 'training.field.latestCheckpoint', 'training.definition.latestCheckpoint'),
      ],
      fullFields: [
        field(t, 'training.field.taskFamily', 'training.definition.taskFamily'),
        field(t, 'training.field.taskVariant', 'training.definition.taskVariant'),
        field(t, 'training.field.epochs', 'training.definition.epochs'),
        field(t, 'training.field.batchSize', 'training.definition.batchSize'),
        field(t, 'training.field.learningRate', 'training.definition.learningRate'),
        field(t, 'training.field.hiddenDim', 'training.definition.hiddenDim'),
        field(t, 'training.field.actionDim', 'training.definition.actionDim'),
        field(t, 'training.field.trainStatus', 'training.definition.trainStatus'),
        field(t, 'training.field.currentEpoch', 'training.definition.currentEpoch'),
        field(t, 'training.field.lastLoss', 'training.definition.lastLoss'),
        field(t, 'training.field.latestCheckpoint', 'training.definition.latestCheckpoint'),
      ],
    },
    {
      id: 'eval',
      title: t('training.section.eval.title'),
      description: t('training.section.eval.description'),
      state: t('training.state.idle'),
      primaryFields: [
        field(t, 'training.field.evalStatus', 'training.definition.evalStatus'),
        field(t, 'training.field.stepsCompleted', 'training.definition.stepsCompleted'),
        field(t, 'training.field.rewardMean', 'training.definition.rewardMean'),
      ],
      fullFields: [
        field(t, 'training.field.evalStatus', 'training.definition.evalStatus'),
        field(t, 'training.field.stepsCompleted', 'training.definition.stepsCompleted'),
        field(t, 'training.field.rewardMean', 'training.definition.rewardMean'),
        field(t, 'training.field.videoPath', 'training.definition.videoPath'),
      ],
    },
    {
      id: 'registry',
      title: t('training.section.registry.title'),
      description: t('training.section.registry.description'),
      state: t('training.state.unregistered'),
      primaryFields: [
        field(t, 'training.field.registrationStatus', 'training.definition.registrationStatus'),
        field(t, 'training.field.researchLabel', 'training.definition.researchLabel'),
      ],
      fullFields: [
        field(t, 'training.field.registrationStatus', 'training.definition.registrationStatus'),
        field(t, 'training.field.researchLabel', 'training.definition.researchLabel'),
        field(t, 'training.field.datasetRef', 'training.definition.datasetRef'),
        field(t, 'training.field.graphRef', 'training.definition.graphRef'),
        field(t, 'training.field.checkpointRef', 'training.definition.checkpointRef'),
        field(t, 'training.field.evalRef', 'training.definition.evalRef'),
      ],
    },
  ]
}

function field(
  t: (key: string) => string,
  labelKey: string,
  definitionKey: string,
) {
  return {
    label: t(labelKey),
    definition: t(definitionKey),
    value: t('shared.unavailable'),
  }
}
