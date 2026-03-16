import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it } from 'vitest'

import { DefinitionHint } from './definition-hint'

describe('DefinitionHint', () => {
  it('uses a unified icon trigger and reveals the definition in a tooltip', async () => {
    const user = userEvent.setup()

    render(<DefinitionHint label="Learning rate" definition="Optimizer step size." />)

    const trigger = screen.getByRole('button', { name: /learning rate: optimizer step size/i })
    expect(trigger.querySelector('svg')).not.toBeNull()
    expect(screen.queryByText('Optimizer step size.')).not.toBeInTheDocument()

    await user.hover(trigger)

    expect(await screen.findByText('Optimizer step size.')).toBeInTheDocument()
  })
})
