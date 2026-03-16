import type { RoiAssetPackPayload } from '@/types/console'

export const mockRoiAssetPack: RoiAssetPackPayload = {
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
      asset_url: '/mock/roi_mesh/AL.glb',
    },
    {
      roi_id: 'FB',
      render_asset_path: 'roi_mesh/FB.glb',
      render_format: 'glb',
      asset_url: '/mock/roi_mesh/FB.glb',
    },
    {
      roi_id: 'LAL',
      render_asset_path: 'roi_mesh/LAL.glb',
      render_format: 'glb',
      asset_url: '/mock/roi_mesh/LAL.glb',
    },
  ],
  mapping_coverage: {
    roi_mapped_nodes: 118320,
    total_nodes: 139244,
  },
}
