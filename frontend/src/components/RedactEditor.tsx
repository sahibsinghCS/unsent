/**
 * Cover names and numbers on one screenshot. Drag (mouse, pen or finger) to draw a solid black box;
 * drag a box's bottom edge to make it taller or shorter.
 * Keyboard: "Add box" places a box; arrow keys move the selected box (Shift + arrows resize it),
 * Delete removes it. "Cover the top bar" covers the contact name and number at the top of a phone
 * screenshot in one tap. Boxes are kept in the image's own pixels and flattened later (lib/redact).
 */
import { useEffect, useId, useRef, useState, type KeyboardEvent, type PointerEvent } from 'react';
import { usePrefs } from '../i18n';
import { bottomEdgeHit, boxFromPoints, nudge, targetSize, topBarBox, type Box } from '../lib/redact';

export function RedactEditor({ image, boxes, onChange, index }: { image: HTMLImageElement; boxes: Box[]; onChange: (boxes: Box[]) => void; index: number }) {
  const { t } = usePrefs();
  const canvas = useRef<HTMLCanvasElement>(null);
  const help = useId();
  const [selected, setSelected] = useState<number | null>(null);
  const [temp, setTemp] = useState<Box | null>(null);
  const start = useRef<{ x: number; y: number } | null>(null);
  const resizing = useRef<number>(-1); // index of the box whose bottom edge is being dragged
  const W = image.naturalWidth || image.width;
  const H = image.naturalHeight || image.height;
  const step = Math.max(4, Math.round(Math.max(W, H) * 0.02));

  // Draw the screenshot, the boxes (solid black) and the selected box's outline.
  useEffect(() => {
    const el = canvas.current;
    const ctx = el?.getContext('2d');
    if (!el || !ctx) return;
    const { width, height, scale } = targetSize(W, H, 900);
    el.width = width;
    el.height = height;
    ctx.drawImage(image, 0, 0, width, height);
    ctx.fillStyle = '#000';
    for (const b of temp ? [...boxes, temp] : boxes) ctx.fillRect(b.x * scale, b.y * scale, b.w * scale, b.h * scale);
    if (selected !== null && boxes[selected]) {
      const b = boxes[selected];
      ctx.strokeStyle = '#0A6EF0';
      ctx.lineWidth = 3;
      ctx.strokeRect(b.x * scale - 2, b.y * scale - 2, b.w * scale + 4, b.h * scale + 4);
    }
  }, [image, boxes, temp, selected, W, H]);

  const point = (e: PointerEvent<HTMLCanvasElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    return { x: ((e.clientX - rect.left) / rect.width) * W, y: ((e.clientY - rect.top) / rect.height) * H };
  };
  const add = (box: Box) => {
    onChange([...boxes, box]);
    setSelected(boxes.length);
  };

  function onPointerDown(e: PointerEvent<HTMLCanvasElement>) {
    try {
      e.currentTarget.setPointerCapture(e.pointerId);
    } catch {
      /* synthetic or already-released pointer: dragging still works without capture */
    }
    const p = point(e);
    // Grab a box's bottom edge (a generous target, finger-friendly) to resize it instead of drawing.
    const rect = e.currentTarget.getBoundingClientRect();
    const hit = bottomEdgeHit(boxes, p, (14 / rect.height) * H);
    if (hit >= 0) {
      resizing.current = hit;
      setSelected(hit);
      return;
    }
    start.current = p;
  }
  function onPointerMove(e: PointerEvent<HTMLCanvasElement>) {
    const p = point(e);
    if (resizing.current >= 0) {
      const i = resizing.current;
      onChange(boxes.map((b, j) => (j === i ? { ...b, h: Math.max(step, Math.min(H - b.y, p.y - b.y)) } : b)));
    } else if (start.current) setTemp(boxFromPoints(start.current, p, W, H));
  }
  function onPointerUp() {
    if (resizing.current < 0 && temp && temp.w > step / 2 && temp.h > step / 2) add(temp);
    resizing.current = -1;
    start.current = null;
    setTemp(null);
  }
  function onKeyDown(e: KeyboardEvent<HTMLCanvasElement>) {
    const moves: Record<string, [number, number]> = { ArrowLeft: [-step, 0], ArrowRight: [step, 0], ArrowUp: [0, -step], ArrowDown: [0, step] };
    if (selected === null || !boxes[selected]) return;
    if (moves[e.key]) {
      e.preventDefault();
      const [dx, dy] = moves[e.key];
      onChange(boxes.map((b, i) => (i === selected ? nudge(b, dx, dy, W, H, e.shiftKey) : b)));
    } else if (e.key === 'Delete' || e.key === 'Backspace') {
      e.preventDefault();
      onChange(boxes.filter((_, i) => i !== selected));
      setSelected(null);
    }
  }

  return (
    <div className="card p-4 sm:p-5" data-testid="redact-editor">
      <div className="mb-3 flex flex-wrap items-center gap-2">
        <span className="meta-label mr-auto">{t('real_friend.image_n', { n: index + 1 })}</span>
        <button type="button" className="btn-primary px-3.5 py-1.5 text-[13px]" onClick={() => add(topBarBox(W, H))} data-testid="cover-top">
          {t('real_friend.cover_top')}
        </button>
        <button
          type="button"
          className="btn-ghost px-3.5 py-1.5 text-[13px]"
          onClick={() => {
            add({ x: Math.round(W * 0.3), y: Math.round(H * 0.45), w: Math.round(W * 0.4), h: Math.round(H * 0.06) });
            canvas.current?.focus();
          }}
          data-testid="add-box"
        >
          {t('real_friend.add_box')}
        </button>
        <button type="button" className="btn-ghost px-3.5 py-1.5 text-[13px]" onClick={() => { onChange(boxes.slice(0, -1)); setSelected(null); }} disabled={!boxes.length}>
          {t('real_friend.undo')}
        </button>
        <button type="button" className="btn-ghost px-3.5 py-1.5 text-[13px]" onClick={() => { onChange([]); setSelected(null); }} disabled={!boxes.length}>
          {t('real_friend.clear')}
        </button>
      </div>
      <canvas
        ref={canvas}
        tabIndex={0}
        aria-label={t('real_friend.canvas_label', { n: index + 1 })}
        aria-describedby={help}
        className="mx-auto block max-h-[70vh] w-auto max-w-full cursor-crosshair touch-none select-none rounded-xl border border-line"
        onPointerDown={onPointerDown}
        onPointerMove={onPointerMove}
        onPointerUp={onPointerUp}
        onPointerCancel={onPointerUp}
        onKeyDown={onKeyDown}
        data-testid="redact-canvas"
      />
      <p id={help} className="mt-3 text-xs leading-relaxed text-muted">
        {t('real_friend.editor_help')}
      </p>
      <p className="mt-1 text-xs font-semibold" aria-live="polite" data-testid="box-count">
        {boxes.length ? t('real_friend.boxes', { n: boxes.length }) : t('real_friend.no_boxes')}
      </p>
    </div>
  );
}
