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
    <div className={`relative flex flex-col overflow-hidden ${bezel} bg-surface ring-1 ring-white/10 ${className}`}>
      <div className={`pointer-events-none absolute left-1/2 top-2 z-10 h-6 w-28 -translate-x-1/2 rounded-full bg-[#17121f] dark:bg-[#05030b] ${bezelOnMobile ? '' : 'hidden sm:block'}`} aria-hidden="true" />
      {header && <div className={`border-b border-line/70 bg-surface/90 px-4 pb-2.5 backdrop-blur ${bezelOnMobile ? 'pt-9' : 'pt-3 sm:pt-9'}`}>{header}</div>}
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

/** One text bubble. `me` = the helper (right, brand color); otherwise the friend (left, gray). */
export function Bubble({ me, children, tail = true, className = '' }: { me?: boolean; children: ReactNode; tail?: boolean; className?: string }) {
  return (
    <div className={`flex ${me ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[80%] whitespace-pre-wrap break-words px-3.5 py-2 text-[15px] leading-snug animate-pop-in ${
          me ? 'bg-me text-white shadow-[0_6px_16px_-10px_rgb(var(--bubble-me))]' : 'bg-them text-ink'
        } rounded-bubble ${tail ? (me ? 'rounded-br-md' : 'rounded-bl-md') : ''} ${className}`}
      >
        {children}
      </div>
    </div>
  );
}

/** The three bouncing dots shown while the friend is "typing". */
export function TypingDots({ label }: { label: string }) {
  return (
    <div className="flex justify-start" role="status" aria-label={label}>
      <div className="flex items-center gap-1 rounded-bubble rounded-bl-md bg-them px-4 py-3">
        {[0, 1, 2].map((i) => (
          <span key={i} className="h-2 w-2 animate-blink rounded-full bg-muted" style={{ animationDelay: `${i * 0.18}s` }} />
        ))}
      </div>
    </div>
  );
}
