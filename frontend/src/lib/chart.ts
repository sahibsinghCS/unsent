// Register the Chart.js pieces we use once, and read theme colors from the CSS tokens.
import {
  Chart,
  Filler,
  Legend,
  LinearScale,
  CategoryScale,
  LineElement,
  PointElement,
  RadialLinearScale,
  Tooltip,
} from 'chart.js';

Chart.register(LineElement, PointElement, LinearScale, CategoryScale, RadialLinearScale, Filler, Tooltip, Legend);
Chart.defaults.font.family = 'ui-sans-serif, system-ui, -apple-system, "Segoe UI", Roboto, sans-serif';

/** A CSS token (see index.css) as an rgb()/rgba() string for Chart.js. */
export function tokenColor(name: string, alpha = 1): string {
  if (typeof window === 'undefined') return `rgba(0,0,0,${alpha})`;
  const value = getComputedStyle(document.documentElement).getPropertyValue(`--${name}`).trim() || '0 0 0';
  return `rgba(${value.split(/\s+/).join(',')},${alpha})`;
}
