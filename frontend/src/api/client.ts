// The only place that talks to the backend. Every call goes to a relative /api URL.
import type {
  CriticReport,
  GuardianResult,
  Health,
  Metrics,
  RealMode,
  ScenarioSummary,
  SessionView,
  TreeView,
  TurnResponse,
  WhatIfResult,
} from './models';

/** An API failure with a message that is safe to show to the user. */
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    /** The raw FastAPI `detail` when it is an object (e.g. {field, reason, message} from /friends). */
    public detail?: unknown,
  ) {
    super(message);
    this.name = 'ApiError';
  }
  /** True when the server could not be reached at all (offline, server down). */
  get offline(): boolean {
    return this.status === 0;
  }
}

const TIMEOUT_MS = 15000;

/** POST /friends/analyze: a draft friend from screenshots, the warning signs seen, and how urgent it is. */
export interface AnalyzeResult {
  draft: { personality: string; situation: string; sample_texts: string[]; guardedness: 'open' | 'guarded' };
  signs: string[];
  urgency: 'none' | 'check_in_soon' | 'tell_an_adult_now';
  /** The friend may act soon (a plan, a way, a time): show the emergency card above everything. */
  imminent: boolean;
}

/** fetch + JSON with timeouts and readable errors (FastAPI puts messages in `detail`). */
export async function request<T>(path: string, init: RequestInit & { timeoutMs?: number } = {}): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), init.timeoutMs ?? TIMEOUT_MS);
  let response: Response;
  try {
    response = await fetch(`/api${path}`, {
      ...init,
      signal: controller.signal,
      headers: { 'Content-Type': 'application/json', ...(init.headers ?? {}) },
    });
  } catch {
    throw new ApiError("Can't reach the FirstReply server. Check your connection and try again.", 0);
  } finally {
    clearTimeout(timer);
  }
  if (!response.ok) {
    let message = `Something went wrong (error ${response.status}).`;
    let detail: unknown;
    try {
      const body = await response.json();
      detail = body?.detail;
      if (typeof body?.detail === 'string') message = body.detail;
      else if (Array.isArray(body?.detail) && body.detail[0]?.msg) message = String(body.detail[0].msg);
      else if (typeof body?.detail?.message === 'string') message = body.detail.message;
    } catch {
      /* not JSON: keep the generic message */
    }
    throw new ApiError(message, response.status, detail);
  }
  if (response.status === 204) return undefined as T;
  try {
    return (await response.json()) as T;
  } catch {
    throw new ApiError('The server sent a response we could not read.', response.status);
  }
}

const post = <T>(path: string, body: unknown = {}) =>
  request<T>(path, { method: 'POST', body: JSON.stringify(body) });

export const api = {
  health: () => request<Health>('/health'),
  scenarios: (lang = 'en') => request<ScenarioSummary[]>(`/scenarios?lang=${encodeURIComponent(lang)}`),
  startSession: (scenario_id: string, locale: string, country: string) =>
    post<SessionView>('/sessions', { scenario_id, locale, country }),
  session: (id: string) => request<SessionView>(`/sessions/${encodeURIComponent(id)}`),
  send: (id: string, text: string, parent_node_id?: string) =>
    post<TurnResponse>(`/sessions/${encodeURIComponent(id)}/messages`, { text, parent_node_id }),
  rewind: (id: string, node_id: string) =>
    post<SessionView>(`/sessions/${encodeURIComponent(id)}/rewind`, { node_id }),
  tree: (id: string) => request<TreeView>(`/sessions/${encodeURIComponent(id)}/tree`),
  finish: (id: string) => post<CriticReport>(`/sessions/${encodeURIComponent(id)}/finish`),
  whatif: (id: string, node_id?: string | null) =>
    post<WhatIfResult>(`/sessions/${encodeURIComponent(id)}/whatif`, { node_id: node_id ?? null }),
  /** Add your own friend (custom scenario). 422 carries {detail: {field, reason, message}}. */
  createFriend: (body: {
    name: string;
    age: number;
    guardedness: 'open' | 'guarded';
    personality: string;
    situation: string;
    sample_texts: string[];
    locale: string;
  }) => post<{ friend: ScenarioSummary & { custom?: boolean }; notice: 'real_help' | null }>('/friends', body),
  friend: (id: string) => request<ScenarioSummary & { custom?: boolean }>(`/friends/${encodeURIComponent(id)}`),
  /** Delete a custom friend and every chat with it (204; 404 if it's already gone). */
  deleteFriend: (id: string) => request<void>(`/friends/${encodeURIComponent(id)}`, { method: 'DELETE' }),
  /** Read 1-3 redacted screenshots (JPEG data URLs) into a draft friend. Takes ~5-10 s. */
  analyzeFriend: (images: string[], locale: string) =>
    request<AnalyzeResult>('/friends/analyze', { method: 'POST', body: JSON.stringify({ images, locale }), timeoutMs: 60000 }),
  realmode: (lang: string, country: string) =>
    request<RealMode>(`/realmode?lang=${encodeURIComponent(lang)}&country=${encodeURIComponent(country)}`),
  guardianCheck: (text: string) => post<GuardianResult>('/guardian/check', { text }),
  metrics: () => request<Metrics>('/metrics'),
};
