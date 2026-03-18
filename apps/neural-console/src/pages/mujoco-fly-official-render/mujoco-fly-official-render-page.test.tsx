import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { ConsolePreferencesProvider } from '@/providers/console-preferences-provider'

import { MujocoFlyOfficialRenderPage } from './mujoco-fly-official-render-page'

describe('MujocoFlyOfficialRenderPage', () => {
  it('renders the official render shell with viewport, controls, and runtime status', () => {
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
    expect(screen.getByRole('button', { name: /follow/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /side/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /top/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /front quarter/i })).toBeInTheDocument()
    expect(screen.getByText(/runtime status/i)).toBeInTheDocument()
    expect(screen.getByText(/loading/i)).toBeInTheDocument()
  })
})
