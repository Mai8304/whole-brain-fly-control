import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

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
})
