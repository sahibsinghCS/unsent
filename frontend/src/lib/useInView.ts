// Plays a scroll moment once: `seen` turns true the first time ~30% of the element is in view.
// With reduced motion (or no IntersectionObserver, e.g. tests) it is true immediately, so the final
// state always shows.
import { useEffect, useRef, useState } from 'react';
import { prefersReducedMotion } from './typingDelay';

export function useInView<T extends Element>(threshold = 0.3) {
  const ref = useRef<T>(null);
  const [seen, setSeen] = useState(false);
  useEffect(() => {
    const el = ref.current;
    if (!el || seen) return undefined;
    if (prefersReducedMotion() || typeof IntersectionObserver === 'undefined') {
      setSeen(true);
      return undefined;
    }
    const io = new IntersectionObserver(
      (entries) => {
        if (entries.some((e) => e.isIntersecting)) {
          setSeen(true);
          io.disconnect();
        }
      },
      { threshold },
    );
    io.observe(el);
    return () => io.disconnect();
  }, [seen, threshold]);
  return [ref, seen] as const;
}
