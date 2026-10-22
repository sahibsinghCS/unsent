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

/** fetch + JSON with timeouts and readable errors (FastAPI puts messages in `detail`). */
export async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);
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
    try {
      const body = await response.json();
      if (typeof body?.detail === 'string') message = body.detail;
      else if (Array.isArray(body?.detail) && body.detail[0]?.msg) message = String(body.detail[0].msg);
    } catch {
      /* not JSON: keep the generic message */
    }
    throw new ApiError(message, response.status);
  }
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
  scenarios: () => request<ScenarioSummary[]>('/scenarios'),
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
  realmode: (lang: string, country: string) =>
    request<RealMode>(`/realmode?lang=${encodeURIComponent(lang)}&country=${encodeURIComponent(country)}`),
  guardianCheck: (text: string) => post<GuardianResult>('/guardian/check', { text }),
  metrics: () => request<Metrics>('/metrics'),
};
