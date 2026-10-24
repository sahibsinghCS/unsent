// Several trust curves on one chart (What-if). The best path is thick; "what you said" is dashed.
import { Line } from 'react-chartjs-2';
import type { ChartOptions } from 'chart.js';
import '../lib/chart';
import { tokenColor } from '../lib/chart';
import { usePrefs } from '../i18n';

export interface Series {
  label: string;
  values: number[];
  color: string;
  emphasis?: 'best' | 'actual' | 'normal';
}

export function OverlayChart({ series, height = 260 }: { series: Series[]; height?: number }) {
  const { t, theme } = usePrefs();
  const length = Math.max(0, ...series.map((s) => s.values.length));
  const data = {
    labels: Array.from({ length }, (_, i) => (i === 0 ? t('whatif.start') : t('whatif.step', { n: i }))),
    datasets: series.map((s) => ({
      label: s.label,
      data: s.values,
      borderColor: s.color,
      backgroundColor: s.color,
      borderWidth: s.emphasis === 'best' ? 4 : 2,
      borderDash: s.emphasis === 'actual' ? [6, 5] : [],
      pointRadius: s.emphasis === 'best' ? 5 : 3,
      tension: 0.35,
      order: s.emphasis === 'best' ? 0 : 1,
    })),
  };
  const options: ChartOptions<'line'> = {
    responsive: true,
    maintainAspectRatio: false,
    interaction: { mode: 'index', intersect: false },
    scales: {
      y: { min: 0, max: 100, ticks: { stepSize: 25, color: tokenColor('muted') }, grid: { color: tokenColor('line', 0.7) }, border: { display: false } },
      x: { ticks: { color: tokenColor('muted') }, grid: { display: false }, border: { display: false } },
    },
    plugins: {
      legend: { position: 'bottom', labels: { color: tokenColor('ink'), usePointStyle: true, boxWidth: 8, padding: 14 } },
      tooltip: { callbacks: { label: (i) => `${i.dataset.label}: ${Math.round(Number(i.raw))}` } },
    },
  };
  return (
    <div style={{ height }}>
      <Line key={theme} data={data} options={options} role="img" aria-label={series.map((s) => `${s.label}: ${s.values.map(Math.round).join(', ')}`).join('; ')} />
    </div>
  );
}
