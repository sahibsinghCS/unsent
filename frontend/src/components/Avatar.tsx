/**
 * A friend's avatar: a circle with their initial. The chat keeps the phone's plain gray (`tone`
 * omitted); story cards pass `tone` for a calm solid color per name (no gradients). Decorative only.
 */
// Solid, muted tones, all dark enough for white initials (AA). Same name → same tone.
const TONES = ['#34558B', '#2E6E5E', '#93482A', '#8A3A55', '#276C7A', '#5E6B2E', '#4A4A5A'];

export function toneFor(name: string): string {
  let hash = 0;
  for (const ch of name) hash = (hash * 31 + ch.charCodeAt(0)) >>> 0;
  return TONES[hash % TONES.length];
}

export function Avatar({ name, size = 'md', tone = false }: { name: string; size?: 'sm' | 'md' | 'lg'; tone?: boolean; ring?: boolean }) {
  const box = size === 'lg' ? 'h-14 w-14 text-2xl' : size === 'sm' ? 'h-9 w-9 text-base' : 'h-11 w-11 text-lg';
  return (
    <span
      className={`${box} grid shrink-0 place-items-center rounded-full font-semibold text-white ${tone ? 'font-display font-bold' : 'bg-[#6E6E73] dark:bg-[#636366]'}`}
      style={tone ? { background: toneFor(name || '?') } : undefined}
      aria-hidden="true"
    >
      {(name || '?').slice(0, 1).toUpperCase()}
    </span>
  );
}
