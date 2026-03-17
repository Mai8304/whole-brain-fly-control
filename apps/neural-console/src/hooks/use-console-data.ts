import { startTransition, useEffect, useRef, useState } from 'react'

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
import {
  buildReplayFrameUrl,
  controlReplay,
  fetchConsoleSnapshot,
  fetchReplaySnapshot,
  seekReplayStep,
  setReplayCamera,
} from '@/lib/console-api'
import type {
  BrainViewPayload,
  ClosedLoopSummaryPayload,
  ConsolePanel,
  PipelineStagePayload,
  ReplayCameraPreset,
  ReplaySessionPayload,
  TimelinePayload,
} from '@/types/console'

type DataSourceStatus = 'API UNAVAILABLE' | 'LIVE API' | 'LOADING' | 'MOCK FALLBACK'

interface ReplayInspectorState {
  available: boolean
  session: ReplaySessionPayload | null
  frameSrc: string
  loading: boolean
  errorMessage: string | null
  onPlayPause: () => void
  onPrevStep: () => void
  onNextStep: () => void
  onSeek: (step: number) => void
  onSetCamera: (camera: ReplayCameraPreset) => void
  onSetSpeed: (speed: number) => void
  onResetView: () => void
}

export interface ConsoleDataState {
  sourceStatus: DataSourceStatus
  errorMessage: string | null
  leftPanels: ConsolePanel[]
  pipeline: PipelineStagePayload[]
  brainView: BrainViewPayload
  brainAssets: typeof mockBrainAssetManifest | null
  roiAssets: typeof mockRoiAssetPack | null
  timeline: TimelinePayload
  summary: ClosedLoopSummaryPayload
  executionLog: string[]
  videoSrc: string
  replay: ReplayInspectorState
}

const ENABLE_MOCK_FALLBACK = import.meta.env.VITE_ENABLE_MOCK_FALLBACK === 'true'
const REPLAY_FRAME_WIDTH = 960
const REPLAY_FRAME_HEIGHT = 540
const REPLAY_BASE_FPS = 8

const unavailableBrainView: BrainViewPayload = {
  data_status: 'unavailable',
  semantic_scope: 'neuropil',
  view_mode: 'grouped-neuropil-v1',
  mapping_mode: 'node_neuropil_occupancy',
  activity_metric: 'activity_mass',
  shell: null,
  mapping_coverage: { neuropil_mapped_nodes: 0, total_nodes: 0 },
  region_activity: [],
  top_regions: [],
  top_nodes: [],
  afferent_activity: null,
  intrinsic_activity: null,
  efferent_activity: null,
}

const unavailableTimeline: TimelinePayload = {
  data_status: 'unavailable',
  steps_requested: 0,
  steps_completed: 0,
  current_step: 0,
  brain_view_ref: 'step_id',
  body_view_ref: 'step_id',
  events: [],
}

const unavailableSummary: ClosedLoopSummaryPayload = {
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
}

function createReplayUnavailableState(message: string | null = null): ReplayInspectorState {
  return {
    available: false,
    session: null,
    frameSrc: '',
    loading: false,
    errorMessage: message,
    onPlayPause: () => undefined,
    onPrevStep: () => undefined,
    onNextStep: () => undefined,
    onSeek: () => undefined,
    onSetCamera: () => undefined,
    onSetSpeed: () => undefined,
    onResetView: () => undefined,
  }
}

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
  replay: createReplayUnavailableState(),
}

const loadingState: ConsoleDataState = {
  sourceStatus: 'LOADING',
  errorMessage: null,
  leftPanels: buildUnavailablePanels('Loading live API…'),
  pipeline: [],
  brainView: unavailableBrainView,
  brainAssets: null,
  roiAssets: null,
  timeline: unavailableTimeline,
  summary: unavailableSummary,
  executionLog: ['[strict] waiting for live API'],
  videoSrc: '',
  replay: createReplayUnavailableState(),
}

function buildUnavailableState(message: string): ConsoleDataState {
  return {
    ...loadingState,
    sourceStatus: 'API UNAVAILABLE',
    errorMessage: message,
    leftPanels: buildUnavailablePanels(message),
    executionLog: [`[strict] ${message}`],
    replay: createReplayUnavailableState(message),
  }
}

export function useConsoleData(): ConsoleDataState {
  const [state, setState] = useState<ConsoleDataState>(
    ENABLE_MOCK_FALLBACK ? mockState : loadingState,
  )
  const stateRef = useRef(state)
  const replayCacheRef = useRef(0)
  const replayBusyRef = useRef(false)

  useEffect(() => {
    stateRef.current = state
  }, [state])

  useEffect(() => {
    if (typeof fetch !== 'function') {
      return
    }

    let cancelled = false

    async function loadInitialState() {
      try {
        const snapshot = await fetchConsoleSnapshot()
        if (cancelled) {
          return
        }

        const baseState = buildLiveState(snapshot)
        startTransition(() => {
          setState(baseState)
        })

        try {
          const replaySnapshot = await fetchReplaySnapshot()
          if (cancelled) {
            return
          }
          startTransition(() => {
            setState((previous) =>
              applyReplaySnapshot({
                previous,
                replaySnapshot,
                message: '[live] replay session loaded from /api/console/replay/session',
              }),
            )
          })
        } catch {
          if (cancelled) {
            return
          }
          startTransition(() => {
            setState((previous) => ({
              ...previous,
              replay: createReplayUnavailableState('Replay inspector is unavailable.'),
            }))
          })
        }
      } catch {
        if (cancelled) {
          return
        }
        startTransition(() => {
          setState(
            ENABLE_MOCK_FALLBACK
              ? {
                  ...mockState,
                  errorMessage: 'Live API unavailable. Falling back to mock data.',
                }
              : buildUnavailableState(
                  'Live API unavailable. Research mode disables mock fallback.',
                ),
          )
        })
      }
    }

    void loadInitialState()

    return () => {
      cancelled = true
    }
  }, [])

  useEffect(() => {
    if (!state.replay.available || state.replay.session?.status !== 'playing') {
      return
    }

    const intervalMs = Math.max(
      80,
      Math.round(1000 / (REPLAY_BASE_FPS * (state.replay.session?.speed ?? 1))),
    )
    const timer = window.setInterval(() => {
      const currentState = stateRef.current
      const session = currentState.replay.session
      if (!currentState.replay.available || session == null) {
        return
      }
      if (session.current_step >= session.steps_completed) {
        void mutateReplay(async () => {
          await controlReplay('pause')
        })
        return
      }
      void mutateReplay(async () => {
        await controlReplay('next')
      })
    }, intervalMs)

    return () => window.clearInterval(timer)
  }, [state.replay.available, state.replay.session?.status, state.replay.session?.speed])

  async function mutateReplay(action: () => Promise<unknown>) {
    if (replayBusyRef.current) {
      return
    }
    replayBusyRef.current = true
    startTransition(() => {
      setState((previous) => ({
        ...previous,
        replay: {
          ...previous.replay,
          loading: true,
          errorMessage: null,
        },
      }))
    })

    try {
      await action()
      const replaySnapshot = await fetchReplaySnapshot()
      replayCacheRef.current += 1
      startTransition(() => {
        setState((previous) =>
          applyReplaySnapshot({
            previous,
            replaySnapshot,
            cacheKey: replayCacheRef.current,
          }),
        )
      })
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Replay control failed.'
      startTransition(() => {
        setState((previous) => ({
          ...previous,
          replay: {
            ...previous.replay,
            loading: false,
            errorMessage: message,
          },
          executionLog: [...previous.executionLog, `[strict] ${message}`],
        }))
      })
    } finally {
      replayBusyRef.current = false
    }
  }

  function setReplaySpeed(speed: number) {
    startTransition(() => {
      setState((previous) => {
        if (!previous.replay.available || previous.replay.session == null) {
          return previous
        }
        return {
          ...previous,
          replay: {
            ...previous.replay,
            session: {
              ...previous.replay.session,
              speed,
            },
          },
        }
      })
    })
  }

  return {
    ...state,
    replay: {
      ...state.replay,
      onPlayPause: () => {
        if (!stateRef.current.replay.available || stateRef.current.replay.session == null) {
          return
        }
        const nextAction = stateRef.current.replay.session.status === 'playing' ? 'pause' : 'play'
        void mutateReplay(async () => {
          await controlReplay(nextAction)
        })
      },
      onPrevStep: () => {
        void mutateReplay(async () => {
          await controlReplay('prev')
        })
      },
      onNextStep: () => {
        void mutateReplay(async () => {
          await controlReplay('next')
        })
      },
      onSeek: (step) => {
        void mutateReplay(async () => {
          await seekReplayStep(step)
        })
      },
      onSetCamera: (camera) => {
        void mutateReplay(async () => {
          await setReplayCamera(camera)
        })
      },
      onSetSpeed: (speed) => {
        setReplaySpeed(speed)
      },
      onResetView: () => {
        void mutateReplay(async () => {
          await setReplayCamera('follow')
        })
      },
    },
  }
}

function buildUnavailablePanels(message: string): ConsolePanel[] {
  return [
    {
      id: 'session',
      title: 'Session',
      titleKey: 'experiment.panel.session.title',
      description: 'Only real console session data is shown in research strict mode.',
      descriptionKey: 'experiment.panel.session.unavailableDescription',
      lines: [message],
    },
    {
      id: 'model',
      title: 'Model',
      titleKey: 'experiment.panel.model.title',
      description: 'Live model configuration has not been loaded yet.',
      descriptionKey: 'experiment.panel.model.unavailableDescription',
      lines: ['Awaiting /api/console/session'],
    },
    {
      id: 'environment',
      title: 'Environment Physics',
      titleKey: 'experiment.panel.environment.title',
      description: 'Real environment physics parameters have not been loaded yet.',
      descriptionKey: 'experiment.panel.environment.unavailableDescription',
      lines: ['Awaiting live environment state'],
    },
    {
      id: 'sensory',
      title: 'Sensory Inputs',
      titleKey: 'experiment.panel.sensory.title',
      description: 'Real sensory inputs have not been loaded yet.',
      descriptionKey: 'experiment.panel.sensory.unavailableDescription',
      lines: ['Awaiting live sensory state'],
    },
    {
      id: 'run',
      title: 'Run',
      titleKey: 'experiment.panel.run.title',
      description: 'Research strict mode does not show fabricated run control state.',
      descriptionKey: 'experiment.panel.run.unavailableDescription',
      lines: ['Connect API to enable run controls'],
    },
    {
      id: 'log',
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
      id: 'session',
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
      id: 'model',
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
      id: 'environment',
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
      id: 'sensory',
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
      id: 'run',
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
      id: 'log',
      title: 'Intervention Log',
      titleKey: 'experiment.panel.log.title',
      description: 'Read-only log proving there is no direct action or joint override.',
      descriptionKey: 'experiment.panel.log.description',
      lines: session.intervention_log,
    },
  ]
}

function buildLiveState(snapshot: Awaited<ReturnType<typeof fetchConsoleSnapshot>>): ConsoleDataState {
  return {
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
    replay: createReplayUnavailableState(),
  }
}

function applyReplaySnapshot({
  previous,
  replaySnapshot,
  cacheKey = 0,
  message,
}: {
  previous: ConsoleDataState
  replaySnapshot: Awaited<ReturnType<typeof fetchReplaySnapshot>>
  cacheKey?: number
  message?: string
}): ConsoleDataState {
  const effectiveSpeed =
    previous.replay.available && previous.replay.session != null
      ? previous.replay.session.speed
      : replaySnapshot.session.speed

  return {
    ...previous,
    brainView: replaySnapshot.brainView,
    timeline: replaySnapshot.timeline,
    summary: {
      ...previous.summary,
      ...replaySnapshot.summary,
      data_status: 'recorded',
    },
    executionLog: message
      ? [...previous.executionLog, message]
      : previous.executionLog,
    replay: {
      ...previous.replay,
      available: true,
      loading: false,
      errorMessage: null,
      session: {
        ...replaySnapshot.session,
        speed: effectiveSpeed,
      },
      frameSrc: buildReplayFrameUrl({
        width: REPLAY_FRAME_WIDTH,
        height: REPLAY_FRAME_HEIGHT,
        cacheKey: `${replaySnapshot.session.current_step}-${cacheKey}`,
      }),
    },
  }
}

function camelCase(value: string) {
  return value
    .replace(/[^a-zA-Z0-9]+(.)/g, (_, chr: string) => chr.toUpperCase())
    .replace(/^[A-Z]/, (match) => match.toLowerCase())
}
