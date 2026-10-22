// 7-skill radar chart for the feedback page (skill_summary values are 0..1).
import { Radar } from 'react-chartjs-2';
import type { ChartOptions } from 'chart.js';
import '../lib/chart';
import { tokenColor } from '../lib/chart';
import { usePrefs } from '../i18n';
import { RUBRIC_SKILLS } from '../lib/labels';

export function SkillRadar({ summary }: { summary: Record<string, number> }) {
  const { t, theme } = usePrefs();
  const values = RUBRIC_SKILLS.map((s) => Math.round((summary[s] ?? 0) * 100));
  const data = {
    labels: RUBRIC_SKILLS.map((s) => t(`skills.${s}`)),
    datasets: [
      {
        data: values,
        borderColor: tokenColor('brand'),
        backgroundColor: tokenColor('brand', 0.2),
        pointBackgroundColor: tokenColor('brand'),
        pointBorderColor: tokenColor('surface'),
        borderWidth: 2,
        pointRadius: 4,
      },
    ],
  };
  const options: ChartOptions<'radar'> = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { legend: { display: false }, tooltip: { callbacks: { label: (i) => `${i.raw}%` } } },
    scales: {
      r: {
        min: 0,
        max: 100,
        ticks: { stepSize: 25, display: false },
        grid: { color: tokenColor('line') },
        angleLines: { color: tokenColor('line') },
        pointLabels: { color: tokenColor('ink'), font: { size: 12, weight: 600 } },
      },
    },
  };
  const description = RUBRIC_SKILLS.map((s, i) => `${t(`skills.${s}`)} ${values[i]}%`).join(', ');
  return (
    <div className="relative h-72 w-full">
      <Radar key={theme} data={data} options={options} role="img" aria-label={description} />
    </div>
  );
}
