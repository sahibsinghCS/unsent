/**
 * Accessible modal dialog: traps focus, restores focus on close, locks page scroll.
 * `dismissible={false}` removes Escape/backdrop closing (used for the crisis pause, which must be
 * acknowledged before the user can go back).
 */
import { useEffect, useId, useRef, type ReactNode } from 'react';

interface Props {
  open: boolean;
  title: ReactNode;
  onClose?: () => void;
  dismissible?: boolean;
  children: ReactNode;
  tone?: 'default' | 'warm';
  icon?: ReactNode;
}

const FOCUSABLE = 'a[href], button:not([disabled]), input:not([disabled]), textarea, select, [tabindex]:not([tabindex="-1"])';

export function Modal({ open, title, onClose, dismissible = true, children, tone = 'default', icon }: Props) {
  const titleId = useId();
  const panel = useRef<HTMLDivElement>(null);
  // Keep the latest onClose in a ref so re-renders don't re-run the focus effect below.
  const closeRef = useRef(onClose);
  closeRef.current = onClose;

  useEffect(() => {
    if (!open) return;
    const previous = document.activeElement as HTMLElement | null;
    const overflow = document.body.style.overflow;
    document.body.style.overflow = 'hidden';
    // Focus the first control (or the panel itself) once rendered.
    const first = panel.current?.querySelector<HTMLElement>(FOCUSABLE);
    (first ?? panel.current)?.focus();

    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape' && dismissible) closeRef.current?.();
      if (event.key !== 'Tab' || !panel.current) return;
      const items = Array.from(panel.current.querySelectorAll<HTMLElement>(FOCUSABLE));
      if (items.length === 0) return;
      const [head, tail] = [items[0], items[items.length - 1]];
      if (event.shiftKey && document.activeElement === head) {
        event.preventDefault();
        tail.focus();
      } else if (!event.shiftKey && document.activeElement === tail) {
        event.preventDefault();
        head.focus();
      }
    };
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('keydown', onKey);
      document.body.style.overflow = overflow;
      previous?.focus?.();
    };
  }, [open, dismissible]);

  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-end justify-center p-0 sm:items-center sm:p-4">
      <div
        className="absolute inset-0 bg-black/50 backdrop-blur-[2px] animate-pop-in"
        onClick={dismissible ? onClose : undefined}
        aria-hidden="true"
      />
      <div
        ref={panel}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        tabIndex={-1}
        className={`relative max-h-[92vh] w-full overflow-y-auto rounded-t-3xl border border-line bg-surface p-6 shadow-phone animate-pop-in sm:max-w-lg sm:rounded-3xl ${
          tone === 'warm' ? 'border-t-4 border-t-warm' : ''
        }`}
      >
        <div className="mb-4 flex items-start gap-3">
          {icon}
          <h2 id={titleId} className="flex-1 text-xl font-bold leading-snug">
            {title}
          </h2>
          {dismissible && onClose && (
            <button type="button" onClick={onClose} className="-m-1 rounded-full p-1.5 text-muted hover:bg-sunken" aria-label="Close">
              <svg viewBox="0 0 24 24" className="h-5 w-5" fill="none" stroke="currentColor" strokeWidth={2} aria-hidden="true">
                <path d="M6 6l12 12M18 6 6 18" strokeLinecap="round" />
              </svg>
            </button>
          )}
        </div>
        {children}
      </div>
    </div>
  );
}
