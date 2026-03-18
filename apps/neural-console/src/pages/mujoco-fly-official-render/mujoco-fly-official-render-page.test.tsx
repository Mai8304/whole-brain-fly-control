import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { ConsolePreferencesProvider } from '@/providers/console-preferences-provider'

import { MujocoFlyOfficialRenderPage } from './mujoco-fly-official-render-page'

describe('MujocoFlyOfficialRenderPage', () => {
  it('renders the official render shell with the contract camera presets and session placeholders', () => {
    render(
      <ConsolePreferencesProvider>
        <MujocoFlyOfficialRenderPage />
      </ConsolePreferencesProvider>,
    )

    expect(
      screen.getByRole('heading', { name: /mujoco fly official render/i }),
    ).toBeInTheDocument()
    expect(
      screen.getByText(/official render viewport placeholder/i),
    ).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /start/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /pause/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /^reset$/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /track/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /side/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /back/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /top/i })).toBeInTheDocument()
    expect(screen.getByText(/^official session contract$/i)).toBeInTheDocument()
    expect(screen.getByText(/session available/i)).toBeInTheDocument()
    expect(screen.getByText(/session status/i)).toBeInTheDocument()
    expect(screen.getByText(/scene version/i)).toBeInTheDocument()
    expect(screen.getByText(/not wired/i)).toBeInTheDocument()
    expect(screen.getByText(/contract only/i)).toBeInTheDocument()
    expect(screen.getAllByText(/^pending$/i)).toHaveLength(2)
    expect(screen.queryByText(/^Loading$/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/^Paused$/i)).not.toBeInTheDocument()
  })
})
