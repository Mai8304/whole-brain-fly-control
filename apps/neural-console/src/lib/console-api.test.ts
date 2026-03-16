import { afterEach, describe, expect, it, vi } from 'vitest'

import { fetchConsoleSnapshot } from './console-api'

afterEach(() => {
  vi.restoreAllMocks()
})

describe('console api client', () => {
  it('parses roi asset pack payloads when the backend exposes them', async () => {
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
          checkpoint: '/tmp/epoch_0001.pt',
          task: 'straight_walking',
          pending_changes: 0,
          applied_state: {
            environment_physics: {
              Terrain: 'flat',
              Friction: '1.00',
              Wind: '0.00',
              Rain: '0.00',
            },
            sensory_inputs: {
              Temperature: '0.00',
              Odor: '0.00',
            },
          },
          intervention_log: [],
          action_provenance: {
            direct_action_editing: false,
            joint_override: false,
          },
        })
      }
      if (url.endsWith('/api/console/pipeline')) {
        return jsonResponse({ stages: [] })
      }
      if (url.endsWith('/api/console/brain-view')) {
        return jsonResponse({
          view_mode: 'region-aggregated',
          mapping_coverage: { roi_mapped_nodes: 120000, total_nodes: 139244 },
          region_activity: [],
          top_regions: [],
          top_nodes: [],
          afferent_activity: 0.1,
          intrinsic_activity: 0.2,
          efferent_activity: 0.3,
        })
      }
      if (url.endsWith('/api/console/brain-assets')) {
        return jsonResponse({
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
            vertex_count: 1,
            face_count: 1,
            bbox_min: [0, 0, 0],
            bbox_max: [1, 1, 1],
            base_color: '#89a5ff',
            opacity: 0.18,
            asset_url: '/api/console/brain-shell',
          },
          roi_manifest: [],
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
          current_step: 64,
          brain_view_ref: 'step_id',
          body_view_ref: 'step_id',
          events: [],
        })
      }
      if (url.endsWith('/api/console/summary')) {
        return jsonResponse({
          status: 'ok',
          task: 'straight_walking',
          steps_requested: 64,
          steps_completed: 64,
          terminated_early: false,
          reward_mean: 1,
          final_reward: 1,
          mean_action_norm: 2.0,
          forward_velocity_mean: 0.5,
          forward_velocity_std: 0.1,
          body_upright_mean: 0.9,
          final_heading_delta: 0.0,
          video_url: '/api/console/video',
        })
      }
      return Promise.reject(new Error(`unexpected url: ${url}`))
    })

    const snapshot = await fetchConsoleSnapshot()

    expect(snapshot.roiAssets?.asset_id).toBe('flywire_roi_pack_v1')
    expect(snapshot.roiAssets?.roi_meshes[0]?.asset_url).toBe('/api/console/roi-mesh/AL')
  })
})
