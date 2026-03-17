import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { ConsolePreferencesProvider } from '@/providers/console-preferences-provider'

import { TrainingConsolePage } from './training-console-page'

describe('TrainingConsolePage structure', () => {
  it('removes the header metric strip and top callout section', () => {
    const { container } = render(
      <ConsolePreferencesProvider>
        <TrainingConsolePage />
      </ConsolePreferencesProvider>,
    )

    const header = container.querySelector('header')

    expect(header?.querySelectorAll('.console-metric')).toHaveLength(0)
    expect(screen.queryByText(/training metadata unavailable/i)).not.toBeInTheDocument()
  })

  it('keeps all primary workflow sections and raw audit area visible', () => {
    render(
      <ConsolePreferencesProvider>
        <TrainingConsolePage />
      </ConsolePreferencesProvider>,
    )

    expect(screen.getByTestId('training-console-layout')).toBeInTheDocument()
    expect(screen.getByTestId('training-section-data')).toBeInTheDocument()
    expect(screen.getByTestId('training-section-graph')).toBeInTheDocument()
    expect(screen.getByTestId('training-section-train')).toBeInTheDocument()
    expect(screen.getByTestId('training-section-eval')).toBeInTheDocument()
    expect(screen.getByTestId('training-section-registry')).toBeInTheDocument()
    expect(screen.getByTestId('training-inspector')).toBeInTheDocument()
    expect(screen.getByTestId('training-raw-panel')).toBeInTheDocument()
    expect(screen.queryAllByRole('textbox')).toHaveLength(0)
  })
})
