// The phone mockup and iMessage-style message pieces, shared by Landing, Chat and What-if.
import type { ReactNode } from 'react';

/** A phone-shaped frame. `header` is the contact bar; children scroll inside the screen. */
export function PhoneFrame({ header, children, footer, className = '' }: { header?: ReactNode; children: ReactNode; footer?: ReactNode; className?: string }) {
  return (
    <div className={`relative flex flex-col overflow-hidden rounded-[2.25rem] border-[6px] border-[#1d2427] bg-surface shadow-phone dark:border-[#05090a] ${className}`}>
      <div className="pointer-events-none absolute left-1/2 top-1.5 z-10 h-5 w-24 -translate-x-1/2 rounded-full bg-[#1d2427] dark:bg-[#05090a]" aria-hidden="true" />
      {header && <div className="border-b border-line bg-surface/95 px-4 pb-2.5 pt-8">{header}</div>}
      <div className="flex-1 overflow-hidden">{children}</div>
      {footer}
    </div>
  );
}

/** Contact header: round avatar with initial, name and a sub-line. */
export function ContactHeader({ name, sub, right }: { name: string; sub?: ReactNode; right?: ReactNode }) {
  return (
    <div className="flex items-center gap-3">
      <div className="grid h-9 w-9 shrink-0 place-items-center rounded-full bg-gradient-to-br from-warm to-brand text-sm font-bold text-white" aria-hidden="true">
        {name.slice(0, 1).toUpperCase()}
      </div>
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
          me ? 'bg-me text-white' : 'bg-them text-ink'
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
