import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterAll, afterEach, beforeAll, describe, expect, it, vi } from 'vitest'

import App from './App'

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

afterEach(() => {
  vi.restoreAllMocks()
  window.history.replaceState(null, '', '/')
})

afterAll(() => {
  vi.unstubAllGlobals()
})

describe('Neural console shell', () => {
  it('renders unavailable state instead of fake data when the API is offline', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValue(new Error('offline'))

    render(<App />)

    expect(screen.getByRole('heading', { name: /whole-brain fly console/i })).toBeInTheDocument()
    await waitFor(() => {
      expect(screen.getByText(/^API UNAVAILABLE$/i)).toBeInTheDocument()
    })
    expect(screen.getByRole('button', { name: /experiment console/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /training console/i })).toBeInTheDocument()
    expect(screen.getByText(/^English$/i)).toBeInTheDocument()
    expect(screen.getAllByText(/disables mock fallback/i).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/^Session$/).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/^Environment Physics$/).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/^Sensory Inputs$/).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/^Brain View$/).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/^Fly Body Live$/).length).toBeGreaterThan(0)
    expect(screen.getByTestId('experiment-brain-card')).toBeInTheDocument()
    expect(screen.getByTestId('experiment-body-card')).toBeInTheDocument()
    expect(
      screen.getAllByText(/live api unavailable\. research mode disables mock fallback\./i).length,
    ).toBeGreaterThan(0)
    expect(screen.getByText(/^API UNAVAILABLE$/i)).toBeInTheDocument()
    expect(screen.queryByText(/^LIVE API$/i)).not.toBeInTheDocument()
  })

  it('switches to the training console page without altering experiment data behavior', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValue(new Error('offline'))

    const user = userEvent.setup()

    render(<App />)

    await waitFor(() => {
      expect(screen.getByText(/^API UNAVAILABLE$/i)).toBeInTheDocument()
    })

    await user.click(screen.getByRole('button', { name: /training console/i }))

    expect(screen.getByRole('heading', { name: /training console/i })).toBeInTheDocument()
    expect(screen.getByTestId('training-console-layout')).toBeInTheDocument()
    expect(screen.getByTestId('training-section-data')).toBeInTheDocument()
    expect(screen.getByTestId('training-section-registry')).toBeInTheDocument()
    expect(screen.getByTestId('training-raw-panel')).toBeInTheDocument()
    expect(screen.getAllByText(/^Data$/).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/^Graph$/).length).toBeGreaterThan(0)
    expect(screen.getAllByText(/^Registry$/).length).toBeGreaterThan(0)
  })

  it('opens the training page from the pathname without changing the home page default', async () => {
    vi.spyOn(globalThis, 'fetch').mockRejectedValue(new Error('offline'))
    window.history.replaceState(null, '', '/training')

    render(<App />)

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /training console/i })).toBeInTheDocument()
    })

    expect(screen.queryByRole('heading', { name: /whole-brain fly console/i })).not.toBeInTheDocument()
  })

  it('hydrates from the read-only UI backend when API responses are available', async () => {
    const jsonResponse = (payload: unknown) =>
      Promise.resolve({
        ok: true,
        json: async () => payload,
      } as Response)

    vi.spyOn(globalThis, 'fetch').mockImplementation((input) => {
      const url = String(input)
      if (url.endsWith('/api/console/session')) {
        return jsonResponse({
          mode: 'Experiment',
          checkpoint: '/tmp/live_epoch.pt',
          task: 'straight_walking',
          applied_state: {
            environment_physics: {
              Terrain: 'rough',
              Friction: '0.82',
              Wind: '0.30',
              Rain: '0.10',
            },
            sensory_inputs: {
              Temperature: '0.25',
              Odor: '0.40',
            },
          },
          pending_state: {},
          pending_changes: 0,
          intervention_log: ['live session loaded'],
          action_provenance: {
            direct_action_editing: false,
            joint_override: false,
          },
        })
      }
      if (url.endsWith('/api/console/pipeline')) {
        return jsonResponse({
          stages: [
            { name: 'Environment / Input', status: 'done' },
            { name: 'Afferent', status: 'done' },
            { name: 'Whole-Brain', status: 'done' },
            { name: 'Efferent', status: 'done' },
            { name: 'Decoder', status: 'done' },
            { name: 'Body', status: 'done' },
          ],
        })
      }
      if (url.endsWith('/api/console/brain-view')) {
        return jsonResponse({
          semantic_scope: 'neuropil',
          view_mode: 'grouped-neuropil-v1',
          mapping_mode: 'node_neuropil_occupancy',
          activity_metric: 'activity_mass',
          data_status: 'recorded',
          validation_passed: true,
          graph_scope_validation_passed: true,
          roster_alignment_passed: false,
          shell: {
            asset_id: 'flywire_brain_v141',
            asset_url: '/api/console/brain-shell',
            base_color: '#89a5ff',
            opacity: 0.18,
          },
          mapping_coverage: { neuropil_mapped_nodes: 120000, total_nodes: 139244 },
          region_activity: [],
          top_regions: [],
          top_nodes: [],
          afferent_activity: 0.2,
          intrinsic_activity: 0.4,
          efferent_activity: 0.6,
        })
      }
      if (url.endsWith('/api/console/brain-assets')) {
        return jsonResponse({
          asset_id: 'flywire_brain_v141',
          asset_version: 'v141',
          source: {
            provider: 'flywire',
            cloudpath: 'precomputed://gs://flywire_neuropil_meshes/whole_neuropil/brain_mesh_v141.surf',
            info_url:
              'https://storage.googleapis.com/flywire_neuropil_meshes/whole_neuropil/brain_mesh_v141.surf/info',
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
          roi_manifest: [
            {
              roi_id: 'MB',
              short_label: 'MB',
              display_name: 'Mushroom Body',
              display_name_zh: '蘑菇体',
              group: 'core-processing',
              description_zh: 'V1 中作为核心处理中间脑区展示。',
              default_color: '#f7b267',
              priority: 1,
            },
          ],
        })
      }
      if (url.endsWith('/api/console/roi-assets')) {
        return jsonResponse({
          asset_id: 'flywire_roi_pack_v1',
          asset_version: 'v1',
          shell: {
            render_asset_path: 'brain_shell.glb',
            render_format: 'glb',
          },
          roi_manifest_path: 'roi_manifest.json',
          node_roi_map_path: 'node_roi_map.parquet',
          roi_meshes: [
            {
              roi_id: 'AL',
              render_asset_path: 'roi_mesh/AL.glb',
              render_format: 'glb',
              asset_url: '/api/console/roi-mesh/AL',
            },
          ],
          mapping_coverage: { roi_mapped_nodes: 120000, total_nodes: 139244 },
        })
      }
      if (url.endsWith('/api/console/timeline')) {
        return jsonResponse({
          steps_requested: 64,
          steps_completed: 64,
          current_step: 48,
          brain_view_ref: 'step_id',
          body_view_ref: 'step_id',
          events: [{ step_id: 12, event_type: 'brain', label: 'whole-brain propagation' }],
        })
      }
      if (url.endsWith('/api/console/summary')) {
        return jsonResponse({
          status: 'ok',
          task: 'straight_walking',
          steps_requested: 64,
          steps_completed: 64,
          terminated_early: false,
          reward_mean: 0.8,
          final_reward: 1.0,
          mean_action_norm: 2.1,
          forward_velocity_mean: 0.45,
          forward_velocity_std: 0.12,
          body_upright_mean: 0.99,
          final_heading_delta: -8.5,
          video_url: '/api/console/video',
        })
      }
      if (url.endsWith('/api/console/replay/session')) {
        return jsonResponse({
          session_id: 'sess-1',
          task: 'straight_walking',
          default_camera: 'follow',
          steps_requested: 64,
          steps_completed: 64,
          current_step: 12,
          status: 'paused',
          speed: 1,
          camera: 'top',
        })
      }
      if (url.endsWith('/api/console/replay/summary')) {
        return jsonResponse({
          status: 'ok',
          task: 'straight_walking',
          steps_requested: 64,
          steps_completed: 64,
          terminated_early: false,
          reward_mean: 0.8,
          final_reward: 1.0,
          mean_action_norm: 2.1,
          forward_velocity_mean: 0.45,
          forward_velocity_std: 0.12,
          body_upright_mean: 0.99,
          final_heading_delta: -8.5,
          step_id: 12,
          reward: 0.52,
          forward_velocity: 0.31,
          body_upright: 0.97,
          terminated: false,
        })
      }
      if (url.endsWith('/api/console/replay/brain-view')) {
        return jsonResponse({
          step_id: 12,
          semantic_scope: 'neuropil',
          view_mode: 'grouped-neuropil-v1',
          mapping_mode: 'node_neuropil_occupancy',
          activity_metric: 'activity_mass',
          data_status: 'recorded',
          validation_passed: true,
          graph_scope_validation_passed: true,
          roster_alignment_passed: true,
          shell: {
            asset_id: 'flywire_brain_v141',
            asset_url: '/api/console/brain-shell',
            base_color: '#89a5ff',
            opacity: 0.18,
          },
          mapping_coverage: { neuropil_mapped_nodes: 120000, total_nodes: 139244 },
          region_activity: [],
          top_regions: [],
          top_nodes: [],
          afferent_activity: 0.2,
          intrinsic_activity: 0.4,
          efferent_activity: 0.6,
        })
      }
      if (url.endsWith('/api/console/replay/timeline')) {
        return jsonResponse({
          data_status: 'recorded',
          steps_requested: 64,
          steps_completed: 64,
          current_step: 12,
          brain_view_ref: 'step_id',
          body_view_ref: 'step_id',
          events: [{ step_id: 12, event_type: 'brain', label: 'whole-brain propagation' }],
        })
      }
      return Promise.reject(new Error(`unexpected url: ${url}`))
    })

    render(<App />)

    await waitFor(() => {
      expect(screen.getByText(/live api/i)).toBeInTheDocument()
    })

    expect(screen.getByDisplayValue('rough')).toBeInTheDocument()
    expect(screen.getAllByText(/step 12/i).length).toBeGreaterThan(0)
    expect(screen.getByRole('img', { name: /replay frame/i })).toHaveAttribute(
      'src',
      expect.stringContaining('/api/console/replay/frame'),
    )
    expect(screen.getAllByText(/flywire_brain_v141/i).length).toBeGreaterThan(0)
  })
})
