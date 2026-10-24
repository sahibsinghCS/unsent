/**
 * A contact avatar like a phone's: a plain gray circle with the friend's initial. Decorative only.
 * (`ring` is accepted for older call sites and ignored: no story rings.)
 */
export function Avatar({ name, size = 'md' }: { name: string; size?: 'sm' | 'md' | 'lg'; ring?: boolean }) {
  const box = size === 'lg' ? 'h-14 w-14 text-2xl' : size === 'sm' ? 'h-9 w-9 text-base' : 'h-11 w-11 text-lg';
  return (
    <span className={`${box} grid shrink-0 place-items-center rounded-full bg-[#6E6E73] font-semibold text-white dark:bg-[#636366]`} aria-hidden="true">
      {(name || '?').slice(0, 1).toUpperCase()}
    </span>
  );
}
