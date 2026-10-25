/**
 * The landing hero's night sky (dark mode only): ~50 tiny stars drifting very slowly on one canvas.
 * Deterministic positions, capped at 30 fps, DPR-aware, paused when the tab is hidden or the hero is
 * off-screen. Twinkle is a slow (~12 s) brightness change, never a flash. Reduced motion draws one
 * still frame. Decorative only.
 */
import { useEffect, useRef } from 'react';
import { prefersReducedMotion } from '../lib/typingDelay';

interface Star {
  x: number;
  y: number;
  r: number;
  a: number;
  vx: number;
  phase: number;
}

/** Small seeded PRNG so the sky is the same on every visit. */
function seeded(seed: number) {
  let s = seed >>> 0;
  return () => {
    s = (s + 0x6d2b79f5) >>> 0;
    let t = Math.imul(s ^ (s >>> 15), 1 | s);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function makeStars(count: number): Star[] {
  const rand = seeded(7);
  return Array.from({ length: count }, () => ({
    x: rand(),
    y: rand(),
    r: 0.4 + rand() * 0.9,
    a: 0.25 + rand() * 0.5,
    vx: (0.4 + rand() * 0.8) * 1e-6, // fraction of the width per ms: one crossing takes many minutes
    phase: rand() * Math.PI * 2,
  }));
}

export function StarField({ className = '' }: { className?: string }) {
  const ref = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = ref.current;
    let ctx: CanvasRenderingContext2D | null = null;
    try {
      ctx = canvas?.getContext('2d') ?? null;
    } catch {
      ctx = null;
    }
    if (!canvas || !ctx) return undefined;
    const stars = makeStars(52);
    const still = prefersReducedMotion();
    let width = 0;
    let height = 0;
    let frame = 0;
    let last = 0;
    let onScreen = true;

    const resize = () => {
      const dpr = Math.min(2, window.devicePixelRatio || 1);
      width = canvas.clientWidth;
      height = canvas.clientHeight;
      canvas.width = Math.round(width * dpr);
      canvas.height = Math.round(height * dpr);
      ctx!.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    const draw = (t: number) => {
      ctx!.clearRect(0, 0, width, height);
      for (const s of stars) {
        const x = (((s.x + s.vx * t) % 1) + 1) % 1;
        const alpha = s.a * (0.7 + 0.3 * Math.sin(t * 0.0005 + s.phase));
        ctx!.globalAlpha = alpha;
        ctx!.fillStyle = '#F6F4FA';
        ctx!.beginPath();
        ctx!.arc(x * width, s.y * height, s.r, 0, Math.PI * 2);
        ctx!.fill();
      }
    };
    const loop = (t: number) => {
      frame = requestAnimationFrame(loop);
      if (t - last < 33) return; // ~30 fps is plenty for drift this slow
      last = t;
      draw(t);
    };
    const start = () => {
      if (!still && !frame && onScreen && !document.hidden) frame = requestAnimationFrame(loop);
    };
    const stop = () => {
      cancelAnimationFrame(frame);
      frame = 0;
    };

    resize();
    draw(0);
    const ro = typeof ResizeObserver !== 'undefined' ? new ResizeObserver(() => { resize(); draw(last); }) : null;
    ro?.observe(canvas);
    const io =
      typeof IntersectionObserver !== 'undefined'
        ? new IntersectionObserver(([entry]) => {
            onScreen = entry.isIntersecting;
            if (onScreen) start();
            else stop();
          })
        : null;
    io?.observe(canvas);
    const onVisibility = () => {
      if (document.hidden) stop();
      else start();
    };
    document.addEventListener('visibilitychange', onVisibility);
    start();
    return () => {
      stop();
      ro?.disconnect();
      io?.disconnect();
      document.removeEventListener('visibilitychange', onVisibility);
    };
  }, []);

  return <canvas ref={ref} className={`pointer-events-none ${className}`} aria-hidden="true" />;
}
