/**
 * Initials-art avatar for the simulated friends: a deterministic dusk gradient per name, a soft
 * highlight, and an optional "story ring" (like a messaging app's unread story). Decorative only.
 */
// Nine palettes so the five current friends each get a clearly different one (all dark enough for
// white initials). Order matters only for which name lands where.
const PALETTES: [string, string][] = [
  ['#3A1FB0', '#0E7C86'], // deep violet → lagoon
  ['#1F5F8B', '#7A2E9E'], // night blue → plum
  ['#7A2E9E', '#B4492D'], // plum → rust
  ['#0E6B5C', '#3A1FB0'], // pine → deep violet (Eli)
  ['#B03A5B', '#6A2BB8'], // rose → violet (Priya)
  ['#5838EE', '#C13923'], // dusk violet → ember (Maya)
  ['#1D4FA8', '#0E7C86'], // cobalt → lagoon (Jordan)
  ['#A64B16', '#8A2453'], // amber → wine (Sam)
  ['#2E3192', '#B03A5B'], // indigo → rose
];

/** Same name → same colors, every time. */
export function paletteFor(name: string): [string, string] {
  let hash = 0;
  for (const ch of name) hash = (hash * 31 + ch.charCodeAt(0)) >>> 0;
  return PALETTES[hash % PALETTES.length];
}

export function Avatar({ name, size = 'md', ring = false }: { name: string; size?: 'sm' | 'md' | 'lg'; ring?: boolean }) {
  const [from, to] = paletteFor(name || '?');
  const box = size === 'lg' ? 'h-16 w-16 text-2xl' : size === 'sm' ? 'h-9 w-9 text-sm' : 'h-12 w-12 text-lg';
  return (
    <span
      className={`relative inline-grid shrink-0 place-items-center rounded-full ${ring ? 'p-[3px]' : ''}`}
      style={ring ? { background: `conic-gradient(from 210deg, ${from}, ${to}, rgb(var(--glow)), ${from})` } : undefined}
      aria-hidden="true"
    >
      <span
        className={`${box} relative grid place-items-center overflow-hidden rounded-full font-display font-semibold italic text-white ${ring ? 'ring-2 ring-surface' : ''}`}
        style={{ background: `linear-gradient(140deg, ${from}, ${to})` }}
      >
        <span className="absolute -left-1/4 -top-1/4 h-3/4 w-3/4 rounded-full bg-white/25 blur-md" />
        <span className="relative">{(name || '?').slice(0, 1).toUpperCase()}</span>
      </span>
    </span>
  );
}
