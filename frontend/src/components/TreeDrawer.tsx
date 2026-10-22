/**
 * The conversation tree (GET /tree). Rewinding creates branches; this shows them as an indented
 * outline with trust after each helper message. Straight runs of messages stay at one indent, and
 * only real branch points indent, so deep conversations stay readable on a phone.
 */
import { useEffect, useMemo, useState } from 'react';
import { api } from '../api/client';
import type { Node, TreeView } from '../api/models';
import { usePrefs } from '../i18n';
import { Modal } from './Modal';
import { ErrorBox, Spinner } from './Status';

export function buildChildren(nodes: Node[]): Map<string, Node[]> {
  const children = new Map<string, Node[]>();
  for (const node of [...nodes].sort((a, b) => (a.created_at ?? 0) - (b.created_at ?? 0))) {
    if (!node.parent_id) continue;
    children.set(node.parent_id, [...(children.get(node.parent_id) ?? []), node]);
  }
  return children;
}

export function pathIds(nodes: Node[], headId: string): Set<string> {
  const byId = new Map(nodes.map((n) => [n.id, n]));
  const ids = new Set<string>();
  for (let cur = byId.get(headId); cur; cur = cur.parent_id ? byId.get(cur.parent_id) : undefined) ids.add(cur.id);
  return ids;
}

export function TreeDrawer({ sessionId, open, onClose, onJump }: { sessionId: string; open: boolean; onClose: () => void; onJump: (nodeId: string) => void }) {
  const { t } = usePrefs();
  const [tree, setTree] = useState<TreeView | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) return;
    setTree(null);
    setError(null);
    api.tree(sessionId).then(setTree, (e) => setError(e.message));
  }, [open, sessionId]);

  const model = useMemo(() => {
    if (!tree) return null;
    return { byId: new Map(tree.nodes.map((n) => [n.id, n])), children: buildChildren(tree.nodes), onPath: pathIds(tree.nodes, tree.head_id) };
  }, [tree]);

  function Row({ node }: { node: Node }) {
    const on = model!.onPath.has(node.id);
    const head = tree!.head_id === node.id;
    const text = node.seen_no_reply ? t('chat.seen') : node.bubbles.join(' ') || t('chat.empty_reply');
    return (
      <li>
        <button
          type="button"
          onClick={() => onJump(node.id)}
          className={`flex w-full items-center gap-2 rounded-lg px-2 py-1.5 text-left text-sm transition hover:bg-sunken ${on ? 'bg-brand-soft/70' : 'opacity-75'}`}
          aria-current={head ? 'step' : undefined}
        >
          <span
            className={`h-2.5 w-2.5 shrink-0 rounded-full ${node.role === 'user' ? 'bg-me' : node.role === 'system' ? 'bg-warm' : 'bg-muted/60'}`}
            aria-hidden="true"
          />
          <span className={`min-w-0 flex-1 truncate ${node.role === 'user' ? 'font-medium' : 'text-muted'}`}>
            {node.role === 'user' ? `${t('chat.you')}: ` : ''}
            {text}
          </span>
          {node.role === 'user' && <span className="mono-num shrink-0 rounded bg-surface px-1.5 text-xs">{Math.round(node.state_after.trust)}</span>}
          {head && <span className="chip shrink-0 border-transparent bg-brand px-2 py-0 text-[10px] text-brand-ink">{t('tree.current')}</span>}
        </button>
      </li>
    );
  }

  /** Render a straight chain from `start`, then indent each branch at the first fork. */
  function Chain({ start }: { start: Node }) {
    const run: Node[] = [start];
    let kids = model!.children.get(start.id) ?? [];
    while (kids.length === 1) {
      run.push(kids[0]);
      kids = model!.children.get(kids[0].id) ?? [];
    }
    return (
      <>
        {run.map((n) => (
          <Row key={n.id} node={n} />
        ))}
        {kids.length > 1 && (
          <li>
            <ul className="ml-3 space-y-0.5 border-l-2 border-line pl-2">
              {kids.map((k) => (
                <li key={k.id}>
                  <ul className="space-y-0.5">
                    <Chain start={k} />
                  </ul>
                </li>
              ))}
            </ul>
          </li>
        )}
      </>
    );
  }

  const root = tree && model?.byId.get(tree.root_id);
  return (
    <Modal open={open} title={t('tree.title')} onClose={onClose}>
      <p className="mb-3 text-sm text-muted">{t('tree.desc')}</p>
      {error && <ErrorBox message={error} />}
      {!error && !root && <Spinner />}
      {root && (
        <ul className="space-y-0.5" data-testid="tree">
          <Chain start={root} />
        </ul>
      )}
    </Modal>
  );
}
