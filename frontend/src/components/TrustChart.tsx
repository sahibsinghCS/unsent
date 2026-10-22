/**
 * Live trust graph: one point per helper message (state_after.trust), starting from the opening
 * trust. Each marker is colored by the strongest label detected in that message; the tooltip shows
 * the change. Also used (with several series) for the What-if overlay.
 */
import { Line } from 'react-chartjs-2';
import type { ChartOptions, ScriptableContext } from 'chart.js';
import '../lib/chart';
import { tokenColor } from '../lib/chart';
import { usePrefs } from '../i18n';
import { NEUTRAL_COLOR, LABEL_COLOR } from '../lib/labels';
import { signed } from '../lib/trustMath';
import type { SkillLabel } from '../api/models';

export interface TrustPoint {
  trust: number;
  delta: number;
  label: SkillLabel | null;
}

export function TrustChart({ points, height = 170 }: { points: TrustPoint[]; height?: number }) {
  const { t, theme } = usePrefs();
  const brand = tokenColor('brand');
  const color = (i: number) => (i === 0 ? tokenColor('muted') : points[i]?.label ? LABEL_COLOR[points[i].label!] : NEUTRAL_COLOR);

  const data = {
    labels: points.map((_, i) => (i === 0 ? t('whatif.start') : String(i))),
    datasets: [
      {
        data: points.map((p) => p.trust),
        borderColor: brand,
        borderWidth: 2.5,
        tension: 0.35,
        fill: true,
        backgroundColor: (ctx: ScriptableContext<'line'>) => {
          const { chartArea, ctx: c } = ctx.chart;
          if (!chartArea) return tokenColor('brand', 0.12);
          const gradient = c.createLinearGradient(0, chartArea.top, 0, chartArea.bottom);
          gradient.addColorStop(0, tokenColor('brand', 0.28));
          gradient.addColorStop(1, tokenColor('brand', 0));
          return gradient;
        },
        pointBackgroundColor: points.map((_, i) => color(i)),
        pointBorderColor: tokenColor('surface'),
        pointBorderWidth: 2,
        pointRadius: points.map((_, i) => (i === points.length - 1 ? 6.5 : 5)),
        pointHoverRadius: 8,
      },
    ],
  };

  const options: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    animation: { duration: 600, easing: 'easeOutCubic' },
    layout: { padding: { top: 6, right: 8 } },
    scales: {
      y: {
        min: 0,
        max: 100,
        ticks: { stepSize: 25, color: tokenColor('muted'), font: { size: 10 } },
        grid: { color: tokenColor('line', 0.7) },
        border: { display: false },
      },
      x: { ticks: { color: tokenColor('muted'), font: { size: 10 } }, grid: { display: false }, border: { display: false } },
    },
    plugins: {
      legend: { display: false },
      tooltip: {
        displayColors: false,
        callbacks: {
          title: (items) => (items[0].dataIndex === 0 ? t('whatif.start') : t('chat.turn', { n: items[0].dataIndex })),
          label: (item) => {
            const p = points[item.dataIndex];
            const head = `${t('chat.trust')} ${Math.round(p.trust)}`;
            if (item.dataIndex === 0) return head;
            return [`${head} (${signed(p.delta)})`, p.label ? t(`labels.${p.label}`) : ''].filter(Boolean);
          },
        },
      },
    },
  };

  const last = points[points.length - 1]?.trust ?? 0;
  return (
    <div style={{ height }} className="relative">
      {/* key={theme} re-creates the chart so canvas colors follow light/dark mode */}
      <Line key={theme} data={data} options={options} aria-label={t('chat.trust_graph_desc', { start: Math.round(points[0]?.trust ?? 0), now: Math.round(last) })} role="img" />
    </div>
  );
}
