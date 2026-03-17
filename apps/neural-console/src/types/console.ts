export interface ConsoleField {
  label: string
  value: string
  helper?: string
  labelKey?: string
  helperKey?: string
}

export interface ConsoleAction {
  label: string
  variant?: 'default' | 'outline' | 'secondary'
  labelKey?: string
}

export interface ConsolePanel {
  id?: string
  title: string
  description: string
  titleKey?: string
  descriptionKey?: string
  fields?: ConsoleField[]
  actions?: ConsoleAction[]
  lines?: string[]
  note?: string
  noteKey?: string
}

export interface ConsoleSessionPayload {
  mode: string
  checkpoint: string
  task: string
  pending_changes: number
  applied_state: {
    environment_physics: Record<string, string>
    sensory_inputs: Record<string, string>
  }
  intervention_log: string[]
  action_provenance: {
    direct_action_editing: boolean
    joint_override: boolean
  }
}

export interface PipelineStagePayload {
  name: string
  status: 'queued' | 'running' | 'done'
}

export interface BrainRegionPayload {
  neuropil_id: string
  display_name: string
  raw_activity_mass: number
  signed_activity: number
  covered_weight_sum: number
  node_count: number
  is_display_grouped: boolean
}

export interface BrainNeuropilMembershipPayload {
  neuropil: string
  occupancy_fraction: number
  synapse_count: number
}

export interface BrainTopNodePayload {
  node_idx: number
  source_id: string
  activity_value: number
  flow_role: string
  neuropil_memberships: BrainNeuropilMembershipPayload[]
  display_group_hint?: string
}

export interface BrainShellPayload {
  asset_id: string
  asset_url: string
  base_color: string
  opacity: number
}

export interface DisplayRegionActivityPayload {
  group_neuropil_id: string
  raw_activity_mass: number
  signed_activity: number
  covered_weight_sum: number
  node_count: number
  member_neuropils: readonly string[]
  view_mode: 'grouped-neuropil-v1'
  is_display_transform: true
}

export interface BrainViewPayload {
  step_id?: number
  data_status?: 'recorded' | 'unavailable'
  artifact_contract_version?: number
  artifact_origin?: 'initial-materialized' | 'replay-live-step'
  semantic_scope?: string
  view_mode: string
  mapping_mode: string
  activity_metric: string
  validation_passed?: boolean
  graph_scope_validation_passed?: boolean
  roster_alignment_passed?: boolean
  validation_scope?: string | null
  materialization?: number | null
  dataset?: string | null
  shell?: BrainShellPayload | null
  mapping_coverage: {
    neuropil_mapped_nodes: number
    total_nodes: number
  }
  display_region_activity?: DisplayRegionActivityPayload[]
  region_activity: BrainRegionPayload[]
  top_regions: BrainRegionPayload[]
  top_nodes: BrainTopNodePayload[]
  afferent_activity: number | null
  intrinsic_activity: number | null
  efferent_activity: number | null
  formal_truth?: {
    occupancy_exists?: boolean
    validation_path?: string
    validation_passed: boolean
    graph_scope_validation_passed?: boolean
    validation_scope?: string | null
    roster_alignment_passed?: boolean | null
    graph_only_root_count?: number | null
    proofread_only_root_count?: number | null
    mapped_nodes?: number
    materialization?: number | null
    dataset?: string | null
    reason?: string
  }
}

export interface BrainAssetNeuropilPayload {
  neuropil: string
  short_label: string
  display_name: string
  display_name_zh: string
  group: string
  description_zh: string
  default_color: string
  priority: number
  render_asset_path: string
  render_format: string
  asset_url?: string
}

export interface BrainAssetManifestPayload {
  asset_id: string
  asset_version: string
  source: {
    provider: string
    cloudpath: string
    info_url: string
    mesh_segment_id: number
  }
  shell: {
    render_asset_path: string
    render_format: string
    vertex_count: number
    face_count: number
    bbox_min: number[]
    bbox_max: number[]
    base_color: string
    opacity: number
    asset_url?: string
  }
  neuropil_manifest: BrainAssetNeuropilPayload[]
}

export interface TimelineEventPayload {
  step_id: number
  event_type: string
  label: string
}

export interface TimelinePayload {
  data_status?: 'recorded' | 'unavailable'
  steps_requested: number
  steps_completed: number
  current_step: number
  brain_view_ref: string
  body_view_ref: string
  events: TimelineEventPayload[]
}

export interface ClosedLoopSummaryPayload {
  step_id?: number
  reward?: number
  forward_velocity?: number
  body_upright?: number
  terminated?: boolean
  data_status?: 'recorded' | 'unavailable'
  status: string
  task: string
  steps_requested: number
  steps_completed: number
  terminated_early: boolean
  reward_mean: number
  final_reward: number
  mean_action_norm: number
  forward_velocity_mean: number
  forward_velocity_std: number
  body_upright_mean: number
  final_heading_delta: number
}

export type ReplayStatus = 'paused' | 'playing'
export type ReplayCameraPreset = 'follow' | 'side' | 'top' | 'front-quarter'

export interface ReplaySessionPayload {
  session_id: string
  task: string
  default_camera: ReplayCameraPreset
  steps_requested: number
  steps_completed: number
  current_step: number
  status: ReplayStatus
  speed: number
  camera: ReplayCameraPreset
}
