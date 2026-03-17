import { afterEach, describe, expect, it, vi } from 'vitest'

import {
  buildReplayFrameUrl,
  controlReplay,
  fetchConsoleSnapshot,
  fetchReplaySnapshot,
  seekReplayStep,
  setReplayCamera,
} from './console-api'

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
          semantic_scope: 'neuropil',
          view_mode: 'grouped-neuropil-v1',
          mapping_mode: 'node_neuropil_occupancy',
          activity_metric: 'activity_mass',
          validation_passed: true,
          graph_scope_validation_passed: true,
          roster_alignment_passed: false,
          mapping_coverage: { neuropil_mapped_nodes: 120000, total_nodes: 139244 },
          region_activity: [
            {
              neuropil_id: 'AL_L',
              display_name: 'AL',
              raw_activity_mass: 0.8,
              signed_activity: -0.2,
              covered_weight_sum: 1.0,
              node_count: 3,
              is_display_grouped: true,
            },
          ],
          top_regions: [
            {
              neuropil_id: 'AL_L',
              display_name: 'AL',
              raw_activity_mass: 0.8,
              signed_activity: -0.2,
              covered_weight_sum: 1.0,
              node_count: 3,
              is_display_grouped: true,
            },
          ],
          top_nodes: [
            {
              node_idx: 5,
              source_id: '1005',
              activity_value: 0.7,
              flow_role: 'intrinsic',
              neuropil_memberships: [
                {
                  neuropil: 'AL_L',
                  occupancy_fraction: 0.75,
                  synapse_count: 3,
                },
              ],
              display_group_hint: 'AL',
            },
          ],
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
    expect(snapshot.brainView.mapping_mode).toBe('node_neuropil_occupancy')
    expect(snapshot.brainView.activity_metric).toBe('activity_mass')
    expect(snapshot.brainView.mapping_coverage.neuropil_mapped_nodes).toBe(120000)
    expect(snapshot.brainView.region_activity[0]?.neuropil_id).toBe('AL_L')
    expect(snapshot.brainView.top_nodes[0]?.neuropil_memberships[0]?.occupancy_fraction).toBe(0.75)
  })

  it('loads replay payloads and posts replay controls', async () => {
    const requests: string[] = []
    const jsonResponse = (payload: unknown) =>
      Promise.resolve({
        ok: true,
        json: async () => payload,
      } as Response)

    vi.spyOn(globalThis, 'fetch').mockImplementation((input, init) => {
      const url = String(input)
      requests.push(`${init?.method ?? 'GET'} ${url}`)
      if (url.endsWith('/api/console/replay/session')) {
        return jsonResponse({
          session_id: 'sess-1',
          task: 'straight_walking',
          default_camera: 'follow',
          steps_requested: 64,
          steps_completed: 64,
          current_step: 8,
          status: 'paused',
          speed: 1,
          camera: 'side',
        })
      }
      if (url.endsWith('/api/console/replay/summary')) {
        return jsonResponse({
          status: 'ok',
          task: 'straight_walking',
          steps_requested: 64,
          steps_completed: 64,
          terminated_early: false,
          reward_mean: 1,
          final_reward: 1,
          mean_action_norm: 2,
          forward_velocity_mean: 0.5,
          forward_velocity_std: 0.1,
          body_upright_mean: 0.9,
          final_heading_delta: 0,
          step_id: 8,
          reward: 0.25,
          forward_velocity: 0.3,
          body_upright: 0.92,
          terminated: false,
        })
      }
      if (url.endsWith('/api/console/replay/brain-view')) {
        return jsonResponse({
          step_id: 8,
          semantic_scope: 'neuropil',
          view_mode: 'grouped-neuropil-v1',
          mapping_mode: 'node_neuropil_occupancy',
          activity_metric: 'activity_mass',
          validation_passed: true,
          graph_scope_validation_passed: true,
          roster_alignment_passed: true,
          mapping_coverage: { neuropil_mapped_nodes: 120000, total_nodes: 139255 },
          region_activity: [
            {
              neuropil_id: 'FB',
              display_name: 'FB',
              raw_activity_mass: 0.9,
              signed_activity: 0.4,
              covered_weight_sum: 1.0,
              node_count: 4,
              is_display_grouped: false,
            },
          ],
          top_regions: [
            {
              neuropil_id: 'FB',
              display_name: 'FB',
              raw_activity_mass: 0.9,
              signed_activity: 0.4,
              covered_weight_sum: 1.0,
              node_count: 4,
              is_display_grouped: false,
            },
          ],
          top_nodes: [
            {
              node_idx: 7,
              source_id: '1007',
              activity_value: 0.6,
              flow_role: 'efferent',
              neuropil_memberships: [
                {
                  neuropil: 'FB',
                  occupancy_fraction: 1,
                  synapse_count: 4,
                },
              ],
              display_group_hint: 'FB',
            },
          ],
          afferent_activity: 0.2,
          intrinsic_activity: 0.4,
          efferent_activity: 0.1,
        })
      }
      if (url.endsWith('/api/console/replay/timeline')) {
        return jsonResponse({
          data_status: 'recorded',
          steps_requested: 64,
          steps_completed: 64,
          current_step: 8,
          brain_view_ref: 'step_id',
          body_view_ref: 'step_id',
          events: [],
        })
      }
      if (url.endsWith('/api/console/replay/seek')) {
        expect(init?.method).toBe('POST')
        expect(init?.body).toBe(JSON.stringify({ step: 12 }))
        return jsonResponse({ current_step: 12 })
      }
      if (url.endsWith('/api/console/replay/control')) {
        expect(init?.method).toBe('POST')
        expect(init?.body).toBe(JSON.stringify({ action: 'next' }))
        return jsonResponse({ status: 'paused', current_step: 9 })
      }
      if (url.endsWith('/api/console/replay/camera')) {
        expect(init?.method).toBe('POST')
        expect(init?.body).toBe(JSON.stringify({ camera: 'top' }))
        return jsonResponse({ camera: 'top', current_step: 8 })
      }
      return Promise.reject(new Error(`unexpected url: ${url}`))
    })

    const replaySnapshot = await fetchReplaySnapshot()
    const seekPayload = await seekReplayStep(12)
    const controlPayload = await controlReplay('next')
    const cameraPayload = await setReplayCamera('top')

    expect(replaySnapshot.session.current_step).toBe(8)
    expect(replaySnapshot.summary.step_id).toBe(8)
    expect(replaySnapshot.brainView.step_id).toBe(8)
    expect(replaySnapshot.brainView.mapping_mode).toBe('node_neuropil_occupancy')
    expect(replaySnapshot.brainView.top_nodes[0]?.display_group_hint).toBe('FB')
    expect(replaySnapshot.timeline.current_step).toBe(8)
    expect(seekPayload.current_step).toBe(12)
    expect(controlPayload.current_step).toBe(9)
    expect(cameraPayload.camera).toBe('top')
    expect(buildReplayFrameUrl({ width: 640, height: 360, cacheKey: '8-1' })).toBe(
      '/api/console/replay/frame?width=640&height=360&cache=8-1',
    )
    expect(requests).toContain('GET /api/console/replay/session')
  })
})
