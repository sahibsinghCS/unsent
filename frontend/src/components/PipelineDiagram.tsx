/**
 * Inline SVG of the pipeline: You → Guardian → Skill detector → State engine → Line bank →
 * Verifier → Friend. The Guardian can stop a message early (crisis pause / blocked). Drawn
 * horizontally on wide screens and vertically on phones; colors come from the theme tokens.
 */
import { usePrefs } from '../i18n';

const STEPS = ['you', 'guardian', 'skills', 'engine', 'lines', 'verifier', 'friend'] as const;
const ACCENT: Record<string, string> = { guardian: 'var(--warm)', skills: 'var(--brand)', engine: 'var(--brand)', lines: 'var(--brand)', verifier: 'var(--brand)' };

function Box({ x, y, w, h, step }: { x: number; y: number; w: number; h: number; step: (typeof STEPS)[number] }) {
  const { t } = usePrefs();
  const accent = ACCENT[step];
  const ends = step === 'you' || step === 'friend';
  return (
    <g>
      <rect x={x} y={y} width={w} height={h} rx={14} fill={ends ? 'rgb(var(--sunken))' : 'rgb(var(--surface))'} stroke={accent ? `rgb(${accent})` : 'rgb(var(--line))'} strokeWidth={accent ? 2 : 1.5} />
      {accent && <rect x={x} y={y} width={6} height={h} rx={3} fill={`rgb(${accent})`} />}
      <text x={x + w / 2 + (accent ? 3 : 0)} y={y + h / 2 - 4} textAnchor="middle" fontSize={14} fontWeight={700} fill="rgb(var(--ink))">
        {t(`how.pipeline.${step}.name`)}
      </text>
      <text x={x + w / 2 + (accent ? 3 : 0)} y={y + h / 2 + 15} textAnchor="middle" fontSize={10.5} fill="rgb(var(--muted))">
        {t(`how.pipeline.${step}.desc`)}
      </text>
    </g>
  );
}

function Arrowhead() {
  return (
    <defs>
      <marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
        <path d="M0 0 L10 5 L0 10 z" fill="rgb(var(--muted))" />
      </marker>
    </defs>
  );
}

export function PipelineDiagram() {
  const { t } = usePrefs();
  const title = STEPS.map((s) => t(`how.pipeline.${s}.name`)).join(' → ');
  // Horizontal layout
  const W = 150, H = 84, GAP = 22, Y = 24;
  // Vertical layout
  const VW = 210, VH = 62, VGAP = 22, VX = 16;
  return (
    <figure>
      <svg viewBox={`0 0 ${STEPS.length * (W + GAP) - GAP + 8} 210`} className="hidden w-full md:block" role="img" aria-label={title}>
        <Arrowhead />
        {STEPS.map((step, i) => {
          const x = 4 + i * (W + GAP);
          return (
            <g key={step}>
              <Box x={x} y={Y} w={W} h={H} step={step} />
              {i < STEPS.length - 1 && <line x1={x + W + 2} y1={Y + H / 2} x2={x + W + GAP - 3} y2={Y + H / 2} stroke="rgb(var(--muted))" strokeWidth={2} markerEnd="url(#arrow)" />}
            </g>
          );
        })}
        {/* Guardian early exits */}
        <path d={`M${4 + (W + GAP) + W / 2} ${Y + H} v 34`} stroke="rgb(var(--warm))" strokeWidth={2} strokeDasharray="5 4" markerEnd="url(#arrow)" fill="none" />
        <g fontSize={11.5} fontWeight={600}>
          <rect x={4 + (W + GAP) - 40} y={Y + H + 40} width={W + 80} height={50} rx={12} fill="rgb(var(--warm-soft))" />
          <text x={4 + (W + GAP) + W / 2} y={Y + H + 61} textAnchor="middle" fill="rgb(var(--ink))">crisis → pause + resources</text>
          <text x={4 + (W + GAP) + W / 2} y={Y + H + 79} textAnchor="middle" fill="rgb(var(--ink))">block → teaching card</text>
        </g>
      </svg>

      <svg viewBox={`0 0 340 ${STEPS.length * (VH + VGAP) - VGAP + 8}`} className="mx-auto w-full max-w-sm md:hidden" role="img" aria-label={title}>
        <Arrowhead />
        {STEPS.map((step, i) => {
          const y = 4 + i * (VH + VGAP);
          return (
            <g key={step}>
              <Box x={VX} y={y} w={VW} h={VH} step={step} />
              {i < STEPS.length - 1 && <line x1={VX + VW / 2} y1={y + VH + 2} x2={VX + VW / 2} y2={y + VH + VGAP - 3} stroke="rgb(var(--muted))" strokeWidth={2} markerEnd="url(#arrow)" />}
            </g>
          );
        })}
        <path d={`M${VX + VW} ${4 + VH + VGAP + VH / 2} h 22`} stroke="rgb(var(--warm))" strokeWidth={2} strokeDasharray="4 3" markerEnd="url(#arrow)" fill="none" />
        <g fontSize={10.5} fontWeight={600}>
          <rect x={VX + VW + 26} y={4 + VH + VGAP + 2} width={92} height={58} rx={10} fill="rgb(var(--warm-soft))" />
          <text x={VX + VW + 72} y={4 + VH + VGAP + 22} textAnchor="middle" fill="rgb(var(--ink))">crisis → pause</text>
          <text x={VX + VW + 72} y={4 + VH + VGAP + 42} textAnchor="middle" fill="rgb(var(--ink))">block → teach</text>
        </g>
      </svg>
      <figcaption className="sr-only">{title}</figcaption>
    </figure>
  );
}
