import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { ConsolePreferencesProvider } from '@/providers/console-preferences-provider'
import type { BrainAssetManifestPayload, BrainShellPayload } from '@/types/console'

import { BrainShellViewport, ViewportRenderBoundary } from './brain-shell-viewport'

describe('BrainShellViewport', () => {
  it('describes grouped neuropil glow availability from grouped display payload', () => {
    const shell: BrainShellPayload = {
      asset_id: 'flywire_brain_v141',
      asset_url: '/api/console/brain-shell',
      base_color: '#89a5ff',
      opacity: 0.18,
    }

    const brainAssets: BrainAssetManifestPayload = {
      asset_id: 'flywire_brain_v141',
      asset_version: 'v141',
      source: {
        provider: 'flywire',
        cloudpath: 'precomputed://gs://example',
        info_url: 'https://example/info',
        mesh_segment_id: 1,
      },
      shell: {
        render_asset_path: 'brain_shell.glb',
        render_format: 'glb',
        vertex_count: 8997,
        face_count: 18000,
        bbox_min: [0, 0, 0],
        bbox_max: [1, 1, 1],
        base_color: '#89a5ff',
        opacity: 0.18,
        asset_url: '/api/console/brain-shell',
      },
      neuropil_manifest: [
        {
          neuropil: 'FB',
          short_label: 'FB',
          display_name: 'Fan-shaped Body',
          display_name_zh: '扇形体',
          group: 'core-processing',
          description_zh: 'test',
          default_color: '#f6bd60',
          priority: 4,
        render_asset_path: 'FB.glb',
        render_format: 'glb',
        asset_url: '/api/console/brain-mesh/FB',
      },
      ] as const,
    }

    const displayRegionActivity = [
      {
        group_neuropil_id: 'FB',
        raw_activity_mass: 0.9,
        signed_activity: 0.3,
        covered_weight_sum: 1,
        node_count: 4,
        member_neuropils: ['FB'],
        view_mode: 'grouped-neuropil-v1' as const,
        is_display_transform: true as const,
      },
    ] as const

    render(
      <ConsolePreferencesProvider>
        <BrainShellViewport
          shell={shell}
          brainAssets={brainAssets}
          displayRegionActivity={displayRegionActivity}
          glowAvailable
        />
      </ConsolePreferencesProvider>,
    )

    expect(screen.getByText(/grouped neuropil glow/i)).toBeInTheDocument()
  })

  it('falls back instead of crashing when the viewport subtree throws', () => {
    const consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {})

    function ThrowingViewport() {
      throw new Error('mesh 404')
      return null
    }

    render(
      <ViewportRenderBoundary fallback={<div>shell-only fallback</div>} resetKey="brain-shell">
        <ThrowingViewport />
      </ViewportRenderBoundary>,
    )

    expect(screen.getByText('shell-only fallback')).toBeInTheDocument()
    consoleErrorSpy.mockRestore()
  })
})
