import type {
  BrainAssetManifestPayload,
  BrainViewPayload,
  ClosedLoopSummaryPayload,
  ConsolePanel,
  ConsoleSessionPayload,
  PipelineStagePayload,
  TimelinePayload,
} from '@/types/console'
import { mockRoiAssetPack } from '@/data/mockRoiAssetPack'

export const mockSession: ConsoleSessionPayload = {
  mode: 'Experiment',
  checkpoint: 'epoch_0001.pt',
  task: 'straight_walking',
  pending_changes: 3,
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
  intervention_log: [
    'changed: terrain, wind, temperature',
    'type: physical + sensory',
    'no direct action override',
    'no joint override',
    'actions are model-generated',
  ],
  action_provenance: {
    direct_action_editing: false,
    joint_override: false,
  },
}

export const mockPipelineStages: PipelineStagePayload[] = [
  { name: 'Environment / Input', status: 'done' },
  { name: 'Afferent', status: 'done' },
  { name: 'Whole-Brain', status: 'running' },
  { name: 'Efferent', status: 'queued' },
  { name: 'Decoder', status: 'queued' },
  { name: 'Body', status: 'queued' },
]

export const mockBrainViewPayload: BrainViewPayload = {
  data_status: 'recorded',
  semantic_scope: 'neuropil',
  view_mode: 'grouped-neuropil-v1',
  mapping_mode: 'node_neuropil_occupancy',
  activity_metric: 'activity_mass',
  validation_passed: true,
  graph_scope_validation_passed: true,
  roster_alignment_passed: false,
  validation_scope: 'graph_source_ids',
  materialization: 783,
  dataset: 'public',
  shell: {
    asset_id: 'flywire_brain_v141',
    asset_url: '/mock/brain_shell.glb',
    base_color: '#89a5ff',
    opacity: 0.18,
  },
  mapping_coverage: {
    neuropil_mapped_nodes: 118320,
    total_nodes: 139244,
  },
  region_activity: [
    {
      neuropil_id: 'AL_L',
      display_name: 'AL',
      raw_activity_mass: 0.42,
      signed_activity: 0.05,
      covered_weight_sum: 1.0,
      node_count: 835,
      is_display_grouped: true,
    },
    {
      neuropil_id: 'FB',
      display_name: 'FB',
      raw_activity_mass: 0.67,
      signed_activity: 0.09,
      covered_weight_sum: 1.0,
      node_count: 980,
      is_display_grouped: false,
    },
    {
      neuropil_id: 'LAL_R',
      display_name: 'LAL',
      raw_activity_mass: 0.53,
      signed_activity: 0.04,
      covered_weight_sum: 1.0,
      node_count: 611,
      is_display_grouped: true,
    },
    {
      neuropil_id: 'EB',
      display_name: 'EB',
      raw_activity_mass: 0.49,
      signed_activity: -0.01,
      covered_weight_sum: 1.0,
      node_count: 402,
      is_display_grouped: false,
    },
    {
      neuropil_id: 'PB',
      display_name: 'PB',
      raw_activity_mass: 0.44,
      signed_activity: 0.07,
      covered_weight_sum: 1.0,
      node_count: 731,
      is_display_grouped: false,
    },
  ],
  top_regions: [],
  top_nodes: [],
  afferent_activity: 0.41,
  intrinsic_activity: 0.73,
  efferent_activity: 0.18,
  formal_truth: {
    occupancy_exists: true,
    validation_path: '/mock/neuropil_truth_validation.json',
    validation_passed: true,
    graph_scope_validation_passed: true,
    validation_scope: 'graph_source_ids',
    roster_alignment_passed: false,
    graph_only_root_count: 15,
    proofread_only_root_count: 26,
    mapped_nodes: 118320,
    materialization: 783,
    dataset: 'public',
    reason: 'graph-scoped formal neuropil truth present; proofread roster alignment differs',
  },
}

export const mockBrainAssetManifest: BrainAssetManifestPayload = {
  asset_id: 'flywire_brain_v141',
  asset_version: 'v141',
  source: {
    provider: 'flywire',
    cloudpath: 'precomputed://gs://flywire_neuropil_meshes/whole_neuropil/brain_mesh_v141.surf',
    info_url: 'https://storage.googleapis.com/flywire_neuropil_meshes/whole_neuropil/brain_mesh_v141.surf/info',
    mesh_segment_id: 1,
  },
  shell: {
    render_asset_path: 'brain_shell.glb',
    render_format: 'glb',
    vertex_count: 8997,
    face_count: 18000,
    bbox_min: [213120, 77504, 760],
    bbox_max: [840512, 388160, 269560],
    base_color: '#89a5ff',
    opacity: 0.18,
    asset_url: '/mock/brain_shell.glb',
  },
  roi_manifest: [
    {
      roi_id: 'AL',
      short_label: 'AL',
      display_name: 'Antennal Lobe',
      display_name_zh: '触角叶',
      group: 'input-associated',
      description_zh: 'V1 中作为气味输入相关脑区的代表。',
      default_color: '#7dcfb6',
      priority: 1,
    },
    {
      roi_id: 'LAL',
      short_label: 'LAL',
      display_name: 'Lateral Accessory Lobe',
      display_name_zh: '外侧附属叶',
      group: 'output-associated',
      description_zh: 'V1 中作为接近运动输出的代表脑区。',
      default_color: '#ef6f6c',
      priority: 5,
    },
    {
      roi_id: 'FB',
      short_label: 'FB',
      display_name: 'Fan-shaped Body',
      display_name_zh: '扇形体',
      group: 'core-processing',
      description_zh: 'V1 中作为中央复合体处理层展示。',
      default_color: '#f6bd60',
      priority: 4,
    },
  ],
}

export { mockRoiAssetPack }

export const mockTimelinePayload: TimelinePayload = {
  data_status: 'recorded',
  steps_requested: 64,
  steps_completed: 64,
  current_step: 32,
  brain_view_ref: 'step_id',
  body_view_ref: 'step_id',
  events: [
    { step_id: 4, event_type: 'input', label: 'temperature injected' },
    { step_id: 12, event_type: 'efferent-rise', label: 'efferent activity rise' },
    { step_id: 18, event_type: 'body-shift', label: 'heading drift begins' },
  ],
}

export const mockClosedLoopSummary: ClosedLoopSummaryPayload = {
  status: 'ok',
  task: 'straight_walking',
  steps_requested: 32,
  steps_completed: 32,
  terminated_early: false,
  reward_mean: 1.0,
  final_reward: 1.0,
  mean_action_norm: 3.4189116948706526,
  forward_velocity_mean: 0.9368082285850408,
  forward_velocity_std: 0.5724203710372776,
  body_upright_mean: 0.9817876248612085,
  final_heading_delta: -108.5324557665515,
}

export const mockExecutionLog = [
  '[15:33:03] pending changes staged',
  '[15:33:03] apply inputs',
  '[15:33:03] reset environment',
  '[15:33:03] inject sensory inputs',
  '[15:33:03] whole-brain propagation running',
  '[15:33:03] rollout started',
]

export const mockVideoSrc = '/mock/rollout.mp4'

export const mockLeftPanels: ConsolePanel[] = [
  {
    id: 'session',
    title: 'Session',
    description: '管理会话模式、运行名与随机种子。',
    fields: [
      { label: 'Mode', value: mockSession.mode },
      { label: 'Run name', value: 'straight_walking_v1' },
      { label: 'Seed', value: '0' },
    ],
  },
  {
    id: 'model',
    title: 'Model',
    description: '选择当前使用的全脑检查点和任务。',
    fields: [
      { label: 'Checkpoint', value: mockSession.checkpoint },
      { label: 'Task', value: mockSession.task },
      { label: 'Policy mode', value: 'Deterministic' },
    ],
  },
  {
    id: 'environment',
    title: 'Environment Physics',
    description: '真实物理环境变量，作用于桌面与身体动力学。',
    fields: Object.entries(mockSession.applied_state.environment_physics).map(([label, value]) => ({ label, value })),
  },
  {
    id: 'sensory',
    title: 'Sensory Inputs',
    description: '抽象感觉输入标量，注入 afferent neurons（输入神经元）。',
    fields: Object.entries(mockSession.applied_state.sensory_inputs).map(([label, value]) => ({ label, value })),
    note: 'Temperature / Odor are injected as sensory inputs to afferent neurons.',
  },
  {
    id: 'run',
    title: 'Run',
    description: '控制回合长度、运行方式和输出工件。',
    fields: [
      { label: 'Max steps', value: '64' },
      { label: 'Run mode', value: 'Single Run' },
      { label: 'Camera', value: 'side' },
      { label: 'Render FPS', value: '8' },
    ],
    actions: [
      { label: 'Apply & Run' },
      { label: 'Stop', variant: 'outline' },
      { label: 'Reset', variant: 'outline' },
      { label: 'Save MP4', variant: 'outline' },
    ],
  },
  {
    id: 'log',
    title: 'Intervention Log',
    description: '只读日志，证明没有直接动作或关节覆盖。',
    lines: mockSession.intervention_log,
  },
]
