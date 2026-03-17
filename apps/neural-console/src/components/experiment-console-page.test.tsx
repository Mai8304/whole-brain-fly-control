import { render, screen, within } from '@testing-library/react'
import { afterAll, beforeAll, describe, expect, it, vi } from 'vitest'

import {
  mockBrainAssetManifest,
  mockBrainViewPayload,
  mockClosedLoopSummary,
  mockExecutionLog,
  mockLeftPanels,
  mockPipelineStages,
  mockRoiAssetPack,
  mockTimelinePayload,
  mockVideoSrc,
} from '@/data/mockConsoleData'
import { ConsolePreferencesProvider } from '@/providers/console-preferences-provider'

import { ExperimentConsolePage } from './experiment-console-page'

beforeAll(() => {
  vi.stubGlobal(
    'ResizeObserver',
    class ResizeObserver {
      observe() {}
      unobserve() {}
      disconnect() {}
    },
  )
})

afterAll(() => {
  vi.unstubAllGlobals()
})

describe('ExperimentConsolePage layout', () => {
  it('uses content-sized columns instead of stretched right-side rows', () => {
    render(
      <ConsolePreferencesProvider>
        <ExperimentConsolePage
          brainAssets={mockBrainAssetManifest}
          roiAssets={mockRoiAssetPack}
          brainView={mockBrainViewPayload}
          errorMessage={null}
          executionLog={mockExecutionLog}
          leftPanels={mockLeftPanels}
          pipeline={mockPipelineStages}
          sourceStatus="LIVE API"
          summary={mockClosedLoopSummary}
          timeline={mockTimelinePayload}
          videoSrc={mockVideoSrc}
          replay={{
            available: false,
            session: null,
            frameSrc: '',
            loading: false,
            errorMessage: null,
            onPlayPause: () => undefined,
            onPrevStep: () => undefined,
            onNextStep: () => undefined,
            onSeek: () => undefined,
            onSetCamera: () => undefined,
            onSetSpeed: () => undefined,
            onResetView: () => undefined,
          }}
        />
      </ConsolePreferencesProvider>,
    )

    const layout = screen.getByTestId('experiment-layout')
    const rightStack = screen.getByTestId('experiment-right-stack')
    const brainCard = screen.getByTestId('experiment-brain-card')
    const bodyCard = screen.getByTestId('experiment-body-card')

    expect(layout.className).toContain('items-start')
    expect(rightStack.className).toContain('self-start')
    expect(rightStack.className).not.toContain('xl:grid-rows-[minmax(380px,1fr)_minmax(320px,0.9fr)]')
    expect(brainCard).toBeInTheDocument()
    expect(bodyCard).toBeInTheDocument()
    expect(brainCard.querySelectorAll('[data-testid="experiment-subcard"]').length).toBe(0)
    expect(bodyCard.querySelectorAll('[data-testid="experiment-subcard"]').length).toBe(0)
    expect(bodyCard.querySelectorAll('.console-video-stage').length).toBe(0)
    expect(bodyCard.querySelectorAll('.console-video-shell').length).toBe(0)
    expect(bodyCard.querySelectorAll('.console-video-frame').length).toBe(1)
  })

  it('renders a replay inspector surface when replay artifacts are available', () => {
    render(
      <ConsolePreferencesProvider>
        <ExperimentConsolePage
          brainAssets={mockBrainAssetManifest}
          roiAssets={mockRoiAssetPack}
          brainView={{ ...mockBrainViewPayload, step_id: 12 }}
          errorMessage={null}
          executionLog={mockExecutionLog}
          leftPanels={mockLeftPanels}
          pipeline={mockPipelineStages}
          sourceStatus="LIVE API"
          summary={mockClosedLoopSummary}
          timeline={{ ...mockTimelinePayload, current_step: 12 }}
          videoSrc={mockVideoSrc}
          replay={{
            available: true,
            session: {
              session_id: 'sess-1',
              task: 'straight_walking',
              default_camera: 'follow',
              steps_requested: 64,
              steps_completed: 64,
              current_step: 12,
              status: 'paused',
              speed: 1,
              camera: 'top',
            },
            frameSrc: '/api/console/replay/frame?cache=1',
            loading: false,
            errorMessage: null,
            onPlayPause: () => undefined,
            onPrevStep: () => undefined,
            onNextStep: () => undefined,
            onSeek: () => undefined,
            onSetCamera: () => undefined,
            onSetSpeed: () => undefined,
            onResetView: () => undefined,
          }}
        />
      </ConsolePreferencesProvider>,
    )

    const rightStack = screen.getByTestId('experiment-right-stack')
    const brainCard = screen.getByTestId('experiment-brain-card')
    const timelineCard = screen.getByTestId('experiment-replay-timeline-card')
    const timelineStrip = screen.getByTestId('replay-timeline-strip')
    const bodyInspector = screen.getByTestId('replay-inspector-root')
    const bodyCard = screen.getByTestId('experiment-body-card')

    expect(timelineCard).toHaveAttribute('data-layout', 'three-part-strip')
    expect(timelineStrip.className).toContain('xl:grid-cols')
    expect(timelineStrip.className).not.toContain('md:grid-cols')
    expect(rightStack.firstElementChild).toBe(brainCard)
    expect(rightStack.children[1]).toBe(timelineCard)
    expect(rightStack.lastElementChild).toBe(bodyCard)
    expect(screen.getByTestId('replay-timeline-left')).toBeInTheDocument()
    expect(screen.getByTestId('replay-timeline-middle')).toBeInTheDocument()
    expect(screen.getByTestId('replay-timeline-right')).toBeInTheDocument()

    expect(within(timelineStrip).getByText('Replay')).toBeInTheDocument()
    expect(within(timelineStrip).getByText('Step 12 / 64')).toBeInTheDocument()
    expect(within(timelineStrip).getByRole('button', { name: 'Play' })).toBeInTheDocument()
    expect(within(timelineStrip).getByRole('button', { name: 'Prev' })).toBeInTheDocument()
    expect(within(timelineStrip).getByRole('button', { name: 'Next' })).toBeInTheDocument()
    expect(within(timelineStrip).getByTestId('replay-timeline-slider')).toBeInTheDocument()
    expect(within(timelineStrip).getByTestId('replay-timeline-event-markers')).toBeInTheDocument()
    expect(within(timelineStrip).getByRole('combobox')).toBeInTheDocument()
    expect(within(bodyInspector).queryByRole('button', { name: 'Play' })).not.toBeInTheDocument()
    expect(within(bodyInspector).queryByRole('button', { name: 'Prev' })).not.toBeInTheDocument()
    expect(within(bodyInspector).queryByRole('button', { name: 'Next' })).not.toBeInTheDocument()
    expect(within(bodyInspector).getByRole('button', { name: 'Reset view' })).toBeInTheDocument()
    expect(screen.getByRole('img', { name: 'Replay frame' })).toHaveAttribute(
      'src',
      '/api/console/replay/frame?cache=1',
    )
    expect(screen.getByTestId('replay-inspector-root').className).toContain('min-w-0')
    expect(screen.getByTestId('replay-status-strip').className).not.toContain('justify-between')
    expect(screen.getByTestId('replay-local-controls')).toBeInTheDocument()
    expect(screen.queryByTitle('Fly rollout video')).not.toBeInTheDocument()
  })

  it('keeps step zero representable and derives status fields from stable panel ids', () => {
    const localizedPanels = mockLeftPanels.map((panel) => {
      if (panel.title === 'Environment Physics') {
        return { ...panel, id: 'environment', title: '环境物理（自定义标题）' }
      }
      if (panel.title === 'Sensory Inputs') {
        return { ...panel, id: 'sensory', title: '感觉输入（自定义标题）' }
      }
      return { ...panel, id: panel.title.toLowerCase() }
    })

    render(
      <ConsolePreferencesProvider>
        <ExperimentConsolePage
          brainAssets={mockBrainAssetManifest}
          roiAssets={mockRoiAssetPack}
          brainView={{ ...mockBrainViewPayload, step_id: 0 }}
          errorMessage={null}
          executionLog={mockExecutionLog}
          leftPanels={localizedPanels}
          pipeline={mockPipelineStages}
          sourceStatus="LIVE API"
          summary={mockClosedLoopSummary}
          timeline={{ ...mockTimelinePayload, current_step: 0 }}
          videoSrc={mockVideoSrc}
          replay={{
            available: true,
            session: {
              session_id: 'sess-0',
              task: 'straight_walking',
              default_camera: 'follow',
              steps_requested: 64,
              steps_completed: 64,
              current_step: 0,
              status: 'paused',
              speed: 1,
              camera: 'follow',
            },
            frameSrc: '/api/console/replay/frame?cache=0',
            loading: false,
            errorMessage: null,
            onPlayPause: () => undefined,
            onPrevStep: () => undefined,
            onNextStep: () => undefined,
            onSeek: () => undefined,
            onSetCamera: () => undefined,
            onSetSpeed: () => undefined,
            onResetView: () => undefined,
          }}
        />
      </ConsolePreferencesProvider>,
    )

    const timelineStrip = screen.getByTestId('replay-timeline-strip')
    const slider = within(timelineStrip).getByRole('slider')
    const statusStrip = screen.getByTestId('replay-status-strip')

    expect(within(timelineStrip).getByText('Step 0 / 64')).toBeInTheDocument()
    expect(slider).toHaveAttribute('aria-valuemin', '0')
    expect(slider).toHaveAttribute('aria-valuenow', '0')
    expect(statusStrip).toHaveTextContent('Terrain: flat')
    expect(statusStrip).toHaveTextContent('Temperature: 0.00')
  })
})
