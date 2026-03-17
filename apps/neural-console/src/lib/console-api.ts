import type {
  BrainAssetManifestPayload,
  BrainViewPayload,
  ClosedLoopSummaryPayload,
  ConsoleSessionPayload,
  PipelineStagePayload,
  ReplayCameraPreset,
  ReplaySessionPayload,
  TimelinePayload,
} from '@/types/console'

export interface ConsoleApiSnapshot {
  session: ConsoleSessionPayload
  pipeline: PipelineStagePayload[]
  brainView: BrainViewPayload
  brainAssets: BrainAssetManifestPayload | null
  timeline: TimelinePayload
  summary: ClosedLoopSummaryPayload
  videoSrc: string
}

export interface ReplayApiSnapshot {
  session: ReplaySessionPayload
  summary: ClosedLoopSummaryPayload
  brainView: BrainViewPayload
  timeline: TimelinePayload
}

const API_BASE_URL = import.meta.env.VITE_CONSOLE_API_BASE_URL?.trim() ?? ''

export async function fetchConsoleSnapshot(): Promise<ConsoleApiSnapshot> {
  const [session, pipelinePayload, brainView, brainAssets, timeline, summary] =
    await Promise.all([
      fetchJson<ConsoleSessionPayload>('/api/console/session'),
      fetchJson<{ stages: PipelineStagePayload[] }>('/api/console/pipeline'),
      fetchJson<BrainViewPayload>('/api/console/brain-view'),
      fetchOptionalJson<BrainAssetManifestPayload>('/api/console/brain-assets'),
      fetchJson<TimelinePayload>('/api/console/timeline'),
      fetchJson<ClosedLoopSummaryPayload & { video_url?: string | null }>('/api/console/summary'),
    ])

  return {
    session,
    pipeline: pipelinePayload.stages,
    brainView,
    brainAssets,
    timeline,
    summary,
    videoSrc: summary.video_url ? resolveUrl(summary.video_url) : '',
  }
}

export async function fetchReplaySnapshot(): Promise<ReplayApiSnapshot> {
  const [session, summary, brainView, timeline] = await Promise.all([
    fetchJson<ReplaySessionPayload>('/api/console/replay/session'),
    fetchJson<ClosedLoopSummaryPayload>('/api/console/replay/summary'),
    fetchJson<BrainViewPayload>('/api/console/replay/brain-view'),
    fetchJson<TimelinePayload>('/api/console/replay/timeline'),
  ])

  return {
    session,
    summary,
    brainView,
    timeline,
  }
}

export async function seekReplayStep(step: number): Promise<{ current_step: number }> {
  return postJson<{ current_step: number }>('/api/console/replay/seek', { step })
}

export async function controlReplay(
  action: 'play' | 'pause' | 'next' | 'prev',
): Promise<{ status: string; current_step: number }> {
  return postJson<{ status: string; current_step: number }>('/api/console/replay/control', {
    action,
  })
}

export async function setReplayCamera(
  camera: ReplayCameraPreset,
): Promise<{ camera: ReplayCameraPreset; current_step: number }> {
  return postJson<{ camera: ReplayCameraPreset; current_step: number }>(
    '/api/console/replay/camera',
    { camera },
  )
}

export function buildReplayFrameUrl(params?: {
  width?: number
  height?: number
  cacheKey?: string | number
}): string {
  const query = new URLSearchParams()
  if (params?.width != null) {
    query.set('width', String(params.width))
  }
  if (params?.height != null) {
    query.set('height', String(params.height))
  }
  if (params?.cacheKey != null) {
    query.set('cache', String(params.cacheKey))
  }

  const suffix = query.size ? `?${query.toString()}` : ''
  return resolveUrl(`/api/console/replay/frame${suffix}`)
}

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(resolveUrl(path))
  if (!response.ok) {
    throw new Error(`console api request failed: ${path} (${response.status})`)
  }
  return (await response.json()) as T
}

async function postJson<T>(path: string, body: Record<string, unknown>): Promise<T> {
  const response = await fetch(resolveUrl(path), {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  })
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
