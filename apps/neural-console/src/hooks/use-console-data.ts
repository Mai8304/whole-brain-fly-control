import { useEffect, useState } from 'react'

import {
  mockBrainAssetManifest,
  mockBrainViewPayload,
  mockClosedLoopSummary,
  mockExecutionLog,
  mockLeftPanels,
  mockPipelineStages,
  mockRoiAssetPack,
  mockSession,
  mockTimelinePayload,
  mockVideoSrc,
} from '@/data/mockConsoleData'
import { fetchConsoleSnapshot } from '@/lib/console-api'
import type { ConsolePanel, PipelineStagePayload } from '@/types/console'

type DataSourceStatus = 'API UNAVAILABLE' | 'LIVE API' | 'LOADING' | 'MOCK FALLBACK'

export interface ConsoleDataState {
  sourceStatus: DataSourceStatus
  errorMessage: string | null
  leftPanels: ConsolePanel[]
  pipeline: PipelineStagePayload[]
  brainView: typeof mockBrainViewPayload
  brainAssets: typeof mockBrainAssetManifest | null
  roiAssets: typeof mockRoiAssetPack | null
  timeline: typeof mockTimelinePayload
  summary: typeof mockClosedLoopSummary
  executionLog: string[]
  videoSrc: string
}

const ENABLE_MOCK_FALLBACK = import.meta.env.VITE_ENABLE_MOCK_FALLBACK === 'true'

const mockState: ConsoleDataState = {
  sourceStatus: 'MOCK FALLBACK',
  errorMessage: null,
  leftPanels: mockLeftPanels,
  pipeline: mockPipelineStages,
  brainView: mockBrainViewPayload,
  brainAssets: mockBrainAssetManifest,
  roiAssets: mockRoiAssetPack,
  timeline: mockTimelinePayload,
  summary: mockClosedLoopSummary,
  executionLog: mockExecutionLog,
  videoSrc: mockVideoSrc,
}

const loadingState: ConsoleDataState = {
  sourceStatus: 'LOADING',
  errorMessage: null,
  leftPanels: buildUnavailablePanels('Loading live API…'),
  pipeline: [],
  brainView: {
    data_status: 'unavailable',
    semantic_scope: 'neuropil',
    view_mode: 'region-aggregated',
    shell: null,
    mapping_coverage: { roi_mapped_nodes: 0, total_nodes: 0 },
    region_activity: [],
    top_regions: [],
    top_nodes: [],
    afferent_activity: null,
    intrinsic_activity: null,
    efferent_activity: null,
  },
  brainAssets: null,
  roiAssets: null,
  timeline: {
    data_status: 'unavailable',
    steps_requested: 0,
    steps_completed: 0,
    current_step: 0,
    brain_view_ref: 'step_id',
    body_view_ref: 'step_id',
    events: [],
  },
  summary: {
    status: 'unavailable',
    task: 'straight_walking',
    steps_requested: 0,
    steps_completed: 0,
    terminated_early: false,
    reward_mean: 0,
    final_reward: 0,
    mean_action_norm: 0,
    forward_velocity_mean: 0,
    forward_velocity_std: 0,
    body_upright_mean: 0,
    final_heading_delta: 0,
  },
  executionLog: ['[strict] waiting for live API'],
  videoSrc: '',
}

function buildUnavailableState(message: string): ConsoleDataState {
  return {
    ...loadingState,
    sourceStatus: 'API UNAVAILABLE',
    errorMessage: message,
    leftPanels: buildUnavailablePanels(message),
    executionLog: [`[strict] ${message}`],
  }
}

export function useConsoleData(): ConsoleDataState {
  const [state, setState] = useState<ConsoleDataState>(ENABLE_MOCK_FALLBACK ? mockState : loadingState)

  useEffect(() => {
    if (typeof fetch !== 'function') {
      return
    }

    let cancelled = false

    fetchConsoleSnapshot()
      .then((snapshot) => {
        if (cancelled) {
          return
        }
        setState({
          sourceStatus: 'LIVE API',
          errorMessage: null,
          leftPanels: buildPanelsFromLiveSnapshot(snapshot.session),
          pipeline: snapshot.pipeline,
          brainView: snapshot.brainView,
          brainAssets: snapshot.brainAssets,
          roiAssets: snapshot.roiAssets,
          timeline: snapshot.timeline,
          summary: snapshot.summary,
          executionLog: [
            '[live] session loaded from /api/console/session',
            '[live] summary loaded from /api/console/summary',
            '[live] brain assets loaded from /api/console/brain-assets',
            '[live] roi assets loaded from /api/console/roi-assets',
            '[live] timeline loaded from /api/console/timeline',
          ],
          videoSrc: snapshot.videoSrc,
        })
      })
      .catch(() => {
        if (cancelled) {
          return
        }
        setState(
          ENABLE_MOCK_FALLBACK
            ? {
                ...mockState,
                errorMessage: 'Live API unavailable. Falling back to mock data.',
              }
            : buildUnavailableState('Live API unavailable. Research mode disables mock fallback.'),
        )
      })

    return () => {
      cancelled = true
    }
  }, [])

  return state
}

function buildUnavailablePanels(message: string): ConsolePanel[] {
  return [
    {
      title: 'Session',
      titleKey: 'experiment.panel.session.title',
      description: 'Only real console session data is shown in research strict mode.',
      descriptionKey: 'experiment.panel.session.unavailableDescription',
      lines: [message],
    },
    {
      title: 'Model',
      titleKey: 'experiment.panel.model.title',
      description: 'Live model configuration has not been loaded yet.',
      descriptionKey: 'experiment.panel.model.unavailableDescription',
      lines: ['Awaiting /api/console/session'],
    },
    {
      title: 'Environment Physics',
      titleKey: 'experiment.panel.environment.title',
      description: 'Real environment physics parameters have not been loaded yet.',
      descriptionKey: 'experiment.panel.environment.unavailableDescription',
      lines: ['Awaiting live environment state'],
    },
    {
      title: 'Sensory Inputs',
      titleKey: 'experiment.panel.sensory.title',
      description: 'Real sensory inputs have not been loaded yet.',
      descriptionKey: 'experiment.panel.sensory.unavailableDescription',
      lines: ['Awaiting live sensory state'],
    },
    {
      title: 'Run',
      titleKey: 'experiment.panel.run.title',
      description: 'Research strict mode does not show fabricated run control state.',
      descriptionKey: 'experiment.panel.run.unavailableDescription',
      lines: ['Connect API to enable run controls'],
    },
    {
      title: 'Intervention Log',
      titleKey: 'experiment.panel.log.title',
      description: 'Read-only logs are shown only when a real session exists.',
      descriptionKey: 'experiment.panel.log.unavailableDescription',
      lines: ['No live intervention log available'],
    },
  ]
}

function buildPanelsFromLiveSnapshot(session: typeof mockSession): ConsolePanel[] {
  return [
    {
      title: 'Session',
      titleKey: 'experiment.panel.session.title',
      description: 'Manage session mode, run name, and random seed.',
      descriptionKey: 'experiment.panel.session.description',
      fields: [
        { label: 'Mode', labelKey: 'field.mode', value: session.mode },
        { label: 'Run name', labelKey: 'field.runName', value: 'straight_walking_live' },
        { label: 'Seed', labelKey: 'field.seed', value: '0' },
      ],
    },
    {
      title: 'Model',
      titleKey: 'experiment.panel.model.title',
      description: 'Select the active whole-brain checkpoint and task.',
      descriptionKey: 'experiment.panel.model.description',
      fields: [
        {
          label: 'Checkpoint',
          labelKey: 'field.checkpoint',
          value: session.checkpoint.split('/').at(-1) ?? session.checkpoint,
        },
        { label: 'Task', labelKey: 'field.task', value: session.task },
        { label: 'Policy mode', labelKey: 'field.policyMode', value: 'Deterministic' },
      ],
    },
    {
      title: 'Environment Physics',
      titleKey: 'experiment.panel.environment.title',
      description: 'Physical environment variables applied to the tabletop and body dynamics.',
      descriptionKey: 'experiment.panel.environment.description',
      fields: Object.entries(session.applied_state.environment_physics).map(([label, value]) => ({
        label,
        labelKey: `field.${camelCase(label)}`,
        value: String(value),
      })),
    },
    {
      title: 'Sensory Inputs',
      titleKey: 'experiment.panel.sensory.title',
      description: 'Abstract sensory input scalars injected into afferent neurons.',
      descriptionKey: 'experiment.panel.sensory.description',
      fields: Object.entries(session.applied_state.sensory_inputs).map(([label, value]) => ({
        label,
        labelKey: `field.${camelCase(label)}`,
        value: String(value),
      })),
      note: 'Temperature / Odor are injected as sensory inputs to afferent neurons.',
      noteKey: 'experiment.panel.sensory.note',
    },
    {
      title: 'Run',
      titleKey: 'experiment.panel.run.title',
      description: 'Control rollout length, run mode, and output artifacts.',
      descriptionKey: 'experiment.panel.run.description',
      fields: [
        { label: 'Max steps', labelKey: 'field.maxSteps', value: '64' },
        { label: 'Run mode', labelKey: 'field.runMode', value: 'Single Run' },
        { label: 'Camera', labelKey: 'field.camera', value: 'side' },
        { label: 'Render FPS', labelKey: 'field.renderFps', value: '8' },
      ],
      actions: [
        { label: 'Apply & Run', labelKey: 'action.applyRun' },
        { label: 'Stop', labelKey: 'action.stop', variant: 'outline' },
        { label: 'Reset', labelKey: 'action.reset', variant: 'outline' },
        { label: 'Save MP4', labelKey: 'action.saveMp4', variant: 'outline' },
      ],
    },
    {
      title: 'Intervention Log',
      titleKey: 'experiment.panel.log.title',
      description: 'Read-only log proving there is no direct action or joint override.',
      descriptionKey: 'experiment.panel.log.description',
      lines: session.intervention_log,
    },
  ]
}

function camelCase(value: string) {
  return value
    .replace(/[^a-zA-Z0-9]+(.)/g, (_, chr: string) => chr.toUpperCase())
    .replace(/^[A-Z]/, (match) => match.toLowerCase())
}
