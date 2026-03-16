import { render, screen } from '@testing-library/react'
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

    expect(screen.getByText('Replay')).toBeInTheDocument()
    expect(screen.getByText('Step 12 / 64')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Play' })).toBeInTheDocument()
    expect(screen.getByRole('img', { name: 'Replay frame' })).toHaveAttribute(
      'src',
      '/api/console/replay/frame?cache=1',
    )
    expect(screen.getByTestId('replay-inspector-root').className).toContain('min-w-0')
    expect(screen.getByTestId('replay-status-strip').className).not.toContain('justify-between')
    expect(screen.getByTestId('replay-control-grid').className).not.toContain(
      'lg:grid-cols-[auto_auto_auto_minmax(180px,1fr)_minmax(120px,160px)_minmax(120px,160px)_auto]',
    )
    expect(screen.queryByTitle('Fly rollout video')).not.toBeInTheDocument()
  })
})
