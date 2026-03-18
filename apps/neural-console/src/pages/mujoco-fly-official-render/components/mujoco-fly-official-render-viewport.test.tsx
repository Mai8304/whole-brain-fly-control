import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { MujocoFlyOfficialRenderViewport } from './mujoco-fly-official-render-viewport'

describe('MujocoFlyOfficialRenderViewport', () => {
  it('renders the official render frame as the primary surface when a frame src is available', () => {
    render(
      <MujocoFlyOfficialRenderViewport
        frameSrc="/api/mujoco-fly-official-render/frame?width=1280&height=720&camera=track&cache=1"
        frameAlt="Official render frame"
        status="paused"
        reason={null}
      />,
    )

    expect(screen.getByRole('img', { name: /official render frame/i })).toHaveAttribute(
      'src',
      '/api/mujoco-fly-official-render/frame?width=1280&height=720&camera=track&cache=1',
    )
  })

  it('fails closed and surfaces the official runtime reason when the render runtime is unavailable', () => {
    render(
      <MujocoFlyOfficialRenderViewport
        frameSrc={null}
        frameAlt="Official render frame"
        status="unavailable"
        reason="Official walking policy checkpoint is unavailable"
      />,
    )

    expect(screen.queryByRole('img', { name: /official render frame/i })).not.toBeInTheDocument()
    expect(
      screen.getAllByText(/official walking policy checkpoint is unavailable/i).length,
    ).toBeGreaterThan(0)
  })
})
