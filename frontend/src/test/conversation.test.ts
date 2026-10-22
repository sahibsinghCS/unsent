import type { Node } from '../api/models';
import { buildChildren, pathIds } from '../components/TreeDrawer';
import { labelsSeen, trustPoints } from '../lib/conversation';

const state = (trust: number, last_delta = 0) => ({ trust, level: 0, turn: 0, status: 'active' as const, last_delta, flags: { asked_directly_ever: false, promised_secrecy: false, referral_turns: [] } });
const node = (id: string, parent_id: string | null, role: Node['role'], trust: number, extra: Partial<Node> = {}): Node => ({
  id,
  parent_id,
  role,
  bubbles: [id],
  state_after: state(trust, extra.state_after?.last_delta ?? 0),
  seen_no_reply: false,
  created_at: Number(id.replace(/\D/g, '')),
  ...extra,
});

const path: Node[] = [
  node('n1', null, 'friend', 30),
  node('n2', 'n1', 'user', 36, { events: { checked_in: 0.9 }, state_after: state(36, 6) }),
  node('n3', 'n2', 'friend', 36),
  node('n4', 'n3', 'user', 14, { events: { dismissed: 0.9, checked_in: 0.1 }, state_after: state(14, -22) }),
  node('n5', 'n4', 'friend', 14, { seen_no_reply: true, bubbles: [] }),
  node('n6', 'n5', 'user', 14, { events: null, guardian: { level: 'none', action: 'block_message', categories: [], evidence: [], score: 1, sources: [], latency_ms: 1 } }),
];

describe('trust graph data', () => {
  it('starts at the opening trust and adds one point per scored helper message', () => {
    expect(trustPoints(path)).toEqual([
      { trust: 30, delta: 0, label: null },
      { trust: 36, delta: 6, label: 'checked_in' },
      { trust: 14, delta: -22, label: 'dismissed' },
    ]);
  });
  it('tracks every skill seen and the latest message', () => {
    const { seen, latest } = labelsSeen(path);
    expect([...seen].sort()).toEqual(['checked_in', 'dismissed']);
    expect([...latest]).toEqual(['dismissed']);
  });
});

describe('conversation tree', () => {
  const branch = node('n7', 'n3', 'user', 50);
  const all = [...path, branch];
  it('groups children by parent in creation order', () => {
    expect(buildChildren(all).get('n3')!.map((n) => n.id)).toEqual(['n4', 'n7']);
  });
  it('finds the current path from the head back to the root', () => {
    expect([...pathIds(all, 'n7')].sort()).toEqual(['n1', 'n2', 'n3', 'n7']);
  });
});
