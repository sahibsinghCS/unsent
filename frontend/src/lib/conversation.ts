// Pure helpers that read a conversation path (root → head nodes). Shared by Chat and Feedback.
import type { Node, SkillLabel } from '../api/models';
import type { TrustPoint } from '../components/TrustChart';
import { activeLabels, strongestLabel } from './labels';

/** A helper message that went through the skill detector (not blocked, not a crisis pause). */
export const isScoredUserNode = (node: Node) => node.role === 'user' && !!node.events;

/** Trust after each scored helper message, starting from the opening trust. */
export function trustPoints(nodes: Node[]): TrustPoint[] {
  if (nodes.length === 0) return [];
  const points: TrustPoint[] = [{ trust: nodes[0].state_after.trust, delta: 0, label: null }];
  for (const node of nodes) {
    if (!isScoredUserNode(node)) continue;
    points.push({ trust: node.state_after.trust, delta: node.state_after.last_delta ?? 0, label: strongestLabel(node.events) });
  }
  return points;
}

/** Every label detected so far, and the labels in the latest helper message. */
export function labelsSeen(nodes: Node[]): { seen: Set<SkillLabel>; latest: Set<SkillLabel> } {
  const scored = nodes.filter(isScoredUserNode);
  const seen = new Set<SkillLabel>(scored.flatMap((n) => activeLabels(n.events)));
  const latest = new Set<SkillLabel>(scored.length ? activeLabels(scored[scored.length - 1].events) : []);
  return { seen, latest };
}

export const isEnded = (status?: string) => status === 'ended_success' || status === 'ended_fail';
