// The phone mockup and iMessage-style message pieces, shared by Landing, Chat and What-if.
import type { ReactNode } from 'react';
import { Avatar } from './Avatar';

/**
 * A phone-shaped frame. `header` is the contact bar; children scroll inside the screen.
 * bezelOnMobile=false drops the bezel and notch below the sm breakpoint (the chat on a real phone
 * shouldn't waste width on a drawn phone); the landing demo keeps it everywhere.
 */
export function PhoneFrame({
  header,
  children,
  footer,
  className = '',
  bezelOnMobile = true,
}: {
  header?: ReactNode;
  children: ReactNode;
  footer?: ReactNode;
  className?: string;
  bezelOnMobile?: boolean;
}) {
  const bezel = bezelOnMobile
    ? 'rounded-[2.6rem] border-[7px] border-[#17121f] shadow-phone dark:border-[#05030b]'
    : 'rounded-2xl border border-line shadow-card sm:rounded-[2.6rem] sm:border-[7px] sm:border-[#17121f] sm:shadow-phone sm:dark:border-[#05030b]';
  return (
    <div className={`im-screen relative flex flex-col overflow-hidden ${bezel} ring-1 ring-white/10 ${className}`}>
      <div className={`pointer-events-none absolute left-1/2 top-2 z-10 h-6 w-28 -translate-x-1/2 rounded-full bg-[#17121f] dark:bg-[#05030b] ${bezelOnMobile ? '' : 'hidden sm:block'}`} aria-hidden="true" />
      {header && (
        <div className={`border-b border-line/60 bg-[rgb(var(--im-bar))] px-3 pb-2 ${bezelOnMobile ? 'pt-9' : 'pt-3 sm:pt-9'}`}>{header}</div>
      )}
      <div className="flex-1 overflow-hidden">{children}</div>
      {footer}
    </div>
  );
}

/** Contact header: round avatar with initial, name and a sub-line. */
export function ContactHeader({ name, sub, right }: { name: string; sub?: ReactNode; right?: ReactNode }) {
  return (
    <div className="flex items-center gap-3">
      <Avatar name={name} size="sm" />
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-semibold leading-tight">{name}</p>
        {sub && <p className="truncate text-xs text-muted">{sub}</p>}
      </div>
      {right}
    </div>
  );
}

/**
 * One Messages-style bubble. `me` = the helper (right, blue); otherwise the friend (left, gray).
 * `tail` draws the curved tail; only the LAST bubble of a run from the same sender gets it.
 */
export function Bubble({ me, children, tail = true, className = '' }: { me?: boolean; children: ReactNode; tail?: boolean; className?: string }) {
  return (
    <div className={`flex ${me ? 'justify-end pr-1.5' : 'justify-start pl-1.5'}`}>
      <div className={`im im-bubble animate-pop-in ${me ? 'im-sent' : 'im-recv'} ${tail ? 'im-tail' : ''} ${className}`}>{children}</div>
    </div>
  );
}

/** The three bouncing dots shown while the friend is "typing". */
export function TypingDots({ label }: { label: string }) {
  return (
    <div className="flex justify-start pl-1.5" role="status" aria-label={label}>
      <div className="im-bubble im-recv im-tail flex items-center gap-1 px-3.5 py-3">
        {[0, 1, 2].map((i) => (
          <span key={i} className="h-2 w-2 animate-blink rounded-full bg-[rgb(var(--im-meta))]" style={{ animationDelay: `${i * 0.18}s` }} />
        ))}
      </div>
    </div>
  );
}

/**
 * Messages-style conversation header: a back chevron on the left, the friend's round avatar centered
 * with their name in a small gray pill under it, and round controls on the right.
 */
export function MessagesHeader({ name, sub, left, right }: { name: string; sub?: ReactNode; left?: ReactNode; right?: ReactNode }) {
  return (
    <div className="grid grid-cols-[4.5rem_1fr_4.5rem] items-center">
      <div className="justify-self-start">{left}</div>
      <div className="flex min-w-0 flex-col items-center gap-0.5">
        <Avatar name={name} size="sm" />
        <span className="im max-w-full truncate rounded-full bg-[rgb(var(--im-recv))] px-2 py-0.5 text-[11px] font-semibold leading-tight text-[rgb(var(--im-recv-ink))]">
          {name} <span aria-hidden="true">›</span>
        </span>
        {sub && <span className="im-meta leading-tight">{sub}</span>}
      </div>
      <div className="flex items-center gap-1.5 justify-self-end">{right}</div>
    </div>
  );
}
