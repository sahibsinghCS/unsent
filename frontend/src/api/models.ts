// Friendly names for the generated OpenAPI types (src/api/types.ts, `npm run gen:api`).
import type { components } from './types';

type S = components['schemas'];
export type ScenarioSummary = S['ScenarioSummary'];
export type SessionView = S['SessionView'];
export type Node = S['Node'];
export type State = S['State'];
export type GuardianResult = S['GuardianResult'];
export type TurnResponse = S['TurnResponse'];
export type TreeView = S['TreeView'];
export type CriticReport = S['CriticReport'];
export type MessageScore = S['MessageScore'];
export type Highlight = S['Highlight'];
export type TurningPoint = S['TurningPoint'];
export type WhatIfResult = S['WhatIfResult'];
export type WhatIfPath = S['WhatIfPath'];
export type SkillLabel = S['SkillLabel'];
export type Reaction = S['Reaction'];
export type SkillProbs = Partial<Record<SkillLabel, number>>;

/** /api/realmode is untyped on the server (plain dict), so it is described here. */
export interface CrisisLine {
  country: string;
  name: string;
  call: string | null;
  text: string | null;
  url: string | null;
  languages: string[];
}
export interface RealModeStep {
  id: string;
  title: string;
  body: string;
}
export interface RealMode {
  lang: string;
  title: string;
  intro: string;
  steps: RealModeStep[];
  for_you: string;
  disclaimer: string;
  needs_native_review?: boolean;
  crisis: { country: string; lines: CrisisLine[]; emergency: string; verified_on: string | null };
}

/** One record from eval/reports/*.json (see eval/README.md). */
export interface MetricRecord {
  lane: string;
  metric: string;
  value: number | string;
  n?: number | null;
  split?: string | null;
  notes?: string | null;
  created?: string | null;
}
/** Localized text pair from content/headline_metrics.json. */
export type Localized = { en: string; es?: string };
/** One curated headline number (GET /api/metrics → headline). found=false means not measured yet. */
export interface HeadlineMetric {
  id: string;
  lane: string;
  metric: string;
  split: string;
  format: 'percent' | 'score' | 'messages' | 'count';
  better: 'higher' | 'lower';
  label: Localized;
  explain: Localized;
  found: boolean;
  value: number | null;
  n: number | null;
  notes?: string | null;
  baseline?: { label: Localized; value: number | null; n: number | null } | null;
}
export interface Metrics {
  components: Record<string, string>;
  records: MetricRecord[];
  headline?: HeadlineMetric[];
}
/** /api/health `llm` block (contracts 1.1): the OpenAI "voice" gateway's live status. */
export interface LlmStatus {
  enabled: boolean;
  fake: boolean;
  has_key: boolean;
  model_actor: string;
  spent_today_usd: number;
  daily_budget_usd: number;
}
export interface Health {
  ok: boolean;
  contracts_version: string;
  components: Record<string, string>;
  llm?: LlmStatus;
}
