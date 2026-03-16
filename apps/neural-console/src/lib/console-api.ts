import type {
  BrainAssetManifestPayload,
  BrainViewPayload,
  ClosedLoopSummaryPayload,
  ConsoleSessionPayload,
  PipelineStagePayload,
  RoiAssetPackPayload,
  TimelinePayload,
} from '@/types/console'

export interface ConsoleApiSnapshot {
  session: ConsoleSessionPayload
  pipeline: PipelineStagePayload[]
  brainView: BrainViewPayload
  brainAssets: BrainAssetManifestPayload | null
  roiAssets: RoiAssetPackPayload | null
  timeline: TimelinePayload
  summary: ClosedLoopSummaryPayload
  videoSrc: string
}

const API_BASE_URL = import.meta.env.VITE_CONSOLE_API_BASE_URL?.trim() ?? ''

export async function fetchConsoleSnapshot(): Promise<ConsoleApiSnapshot> {
  const [session, pipelinePayload, brainView, brainAssets, roiAssets, timeline, summary] =
    await Promise.all([
      fetchJson<ConsoleSessionPayload>('/api/console/session'),
      fetchJson<{ stages: PipelineStagePayload[] }>('/api/console/pipeline'),
      fetchJson<BrainViewPayload>('/api/console/brain-view'),
      fetchOptionalJson<BrainAssetManifestPayload>('/api/console/brain-assets'),
      fetchOptionalJson<RoiAssetPackPayload>('/api/console/roi-assets'),
      fetchJson<TimelinePayload>('/api/console/timeline'),
      fetchJson<ClosedLoopSummaryPayload & { video_url?: string | null }>('/api/console/summary'),
    ])

  return {
    session,
    pipeline: pipelinePayload.stages,
    brainView,
    brainAssets,
    roiAssets,
    timeline,
    summary,
    videoSrc: summary.video_url ? resolveUrl(summary.video_url) : '',
  }
}

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(resolveUrl(path))
  if (!response.ok) {
    throw new Error(`console api request failed: ${path} (${response.status})`)
  }
  return (await response.json()) as T
}

async function fetchOptionalJson<T>(path: string): Promise<T | null> {
  const response = await fetch(resolveUrl(path))
  if (!response.ok) {
    return null
  }
  return (await response.json()) as T
}

function resolveUrl(path: string): string {
  if (!API_BASE_URL) {
    return path
  }
  return `${API_BASE_URL.replace(/\/$/, '')}${path}`
}
