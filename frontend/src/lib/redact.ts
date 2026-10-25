/**
 * Preparing a screenshot in the browser before anything is uploaded:
 *  1. the black boxes the user drew are painted INTO the pixels (flattened), so the covered names and
 *     numbers are gone from the image itself, not just hidden by an overlay;
 *  2. it is downscaled to at most 1280 px on the long side;
 *  3. it is re-encoded as JPEG (≈0.82 quality), which drops EXIF data such as location;
 *  4. quality steps down until the file is under 1.5 MB (the server's limit).
 * The original file is never uploaded. Boxes are stored in the image's own pixel coordinates.
 */

export interface Box {
  x: number;
  y: number;
  w: number;
  h: number;
}

export const MAX_SIDE = 1280;
export const MAX_BYTES = 1_500_000;
const QUALITIES = [0.82, 0.72, 0.62, 0.5, 0.4, 0.3];

/** The output size: at most MAX_SIDE on the long side, never upscaled. */
export function targetSize(width: number, height: number, maxSide = MAX_SIDE) {
  const scale = Math.min(1, maxSide / Math.max(width, height));
  return { width: Math.max(1, Math.round(width * scale)), height: Math.max(1, Math.round(height * scale)), scale };
}

/** Phone screenshots put the contact's name and number in the top bar: cover the top 12%. */
export function topBarBox(width: number, height: number): Box {
  return { x: 0, y: 0, w: width, h: Math.round(height * 0.12) };
}

/** A box from two drag corners, in any direction, clamped to the image. */
export function boxFromPoints(a: { x: number; y: number }, b: { x: number; y: number }, width: number, height: number): Box {
  const x1 = Math.max(0, Math.min(a.x, b.x));
  const y1 = Math.max(0, Math.min(a.y, b.y));
  const x2 = Math.min(width, Math.max(a.x, b.x));
  const y2 = Math.min(height, Math.max(a.y, b.y));
  return { x: x1, y: y1, w: x2 - x1, h: y2 - y1 };
}

/** Move (or resize) a box by a step, keeping it inside the image. */
export function nudge(box: Box, dx: number, dy: number, width: number, height: number, resize = false): Box {
  if (resize) {
    const w = Math.max(8, Math.min(width - box.x, box.w + dx));
    const h = Math.max(8, Math.min(height - box.y, box.h + dy));
    return { ...box, w, h };
  }
  return { ...box, x: Math.max(0, Math.min(width - box.w, box.x + dx)), y: Math.max(0, Math.min(height - box.h, box.y + dy)) };
}

/**
 * Draw the image and then the boxes, scaled, onto a 2D context. Box edges are rounded outward and
 * grown by 1 px so anti-aliasing can never leave a readable sliver at the border.
 */
export function paintRedacted(ctx: Pick<CanvasRenderingContext2D, 'drawImage' | 'fillRect' | 'fillStyle'>, image: CanvasImageSource, width: number, height: number, boxes: Box[], scale: number) {
  ctx.drawImage(image, 0, 0, width, height);
  ctx.fillStyle = '#000';
  for (const b of boxes) {
    const x = Math.floor(b.x * scale) - 1;
    const y = Math.floor(b.y * scale) - 1;
    ctx.fillRect(x, y, Math.ceil((b.x + b.w) * scale) + 1 - x, Math.ceil((b.y + b.h) * scale) + 1 - y);
  }
}

/** Decoded size in bytes of a base64 data URL. */
export function dataUrlBytes(url: string): number {
  const payload = url.slice(url.indexOf(',') + 1);
  const padding = payload.endsWith('==') ? 2 : payload.endsWith('=') ? 1 : 0;
  return Math.floor((payload.length * 3) / 4) - padding;
}

/** Encode, stepping quality down until it fits under maxBytes. Throws if even the lowest is too big. */
export function encodeUnder(encode: (quality: number) => string, maxBytes = MAX_BYTES): string {
  for (const q of QUALITIES) {
    const url = encode(q);
    if (dataUrlBytes(url) <= maxBytes) return url;
  }
  throw new Error('too_big');
}

/** Flatten + downscale + re-encode one screenshot. Returns a JPEG data URL (the only thing uploaded). */
export function prepareScreenshot(
  image: CanvasImageSource & { naturalWidth?: number; naturalHeight?: number; width: number; height: number },
  boxes: Box[],
  makeCanvas: () => HTMLCanvasElement = () => document.createElement('canvas'),
): string {
  const srcW = image.naturalWidth || image.width;
  const srcH = image.naturalHeight || image.height;
  const { width, height, scale } = targetSize(srcW, srcH);
  const canvas = makeCanvas();
  canvas.width = width;
  canvas.height = height;
  const ctx = canvas.getContext('2d');
  if (!ctx) throw new Error('no_canvas');
  paintRedacted(ctx, image, width, height, boxes, scale);
  try {
    return encodeUnder((q) => canvas.toDataURL('image/jpeg', q));
  } finally {
    // Drop the pixels right away; only the returned data URL lives on (until analysis is done).
    canvas.width = 0;
    canvas.height = 0;
  }
}

/** Read a picked file into an image element via a data URL (the CSP allows data: images, not blob:). */
export function loadImage(file: File): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    if (!/^image\/(png|jpeg|webp)$/.test(file.type)) {
      reject(new Error('bad_type'));
      return;
    }
    const reader = new FileReader();
    reader.onerror = () => reject(new Error('unreadable'));
    reader.onload = () => {
      const img = new Image();
      img.onload = () => resolve(img);
      img.onerror = () => reject(new Error('unreadable'));
      img.src = String(reader.result);
    };
    reader.readAsDataURL(file);
  });
}
