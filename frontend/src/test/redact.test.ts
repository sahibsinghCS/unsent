import { boxFromPoints, dataUrlBytes, encodeUnder, MAX_BYTES, nudge, paintRedacted, prepareScreenshot, targetSize, topBarBox } from '../lib/redact';

/** A tiny fake 2D context with a real pixel grid: drawImage fills every pixel white, fillRect paints. */
function pixelCtx(width: number, height: number) {
  const px: string[][] = Array.from({ length: height }, () => Array(width).fill('empty'));
  const ctx = {
    fillStyle: '#000' as string | CanvasGradient | CanvasPattern,
    drawImage: (_img: unknown, x: number, y: number, w: number, h: number) => {
      for (let j = y; j < y + h; j++) for (let i = x; i < x + w; i++) if (px[j]?.[i] !== undefined) px[j][i] = 'image';
    },
    fillRect: (x: number, y: number, w: number, h: number) => {
      for (let j = Math.max(0, y); j < Math.min(height, y + h); j++) for (let i = Math.max(0, x); i < Math.min(width, x + w); i++) px[j][i] = String(ctx.fillStyle);
    },
  };
  return { ctx, px };
}

describe('screenshot redaction', () => {
  it('flattens boxes into the pixels after drawing the image, scaled to the output size', () => {
    // A 400×200 screenshot downscaled by 0.1 to 40×20; a box at (100,50)-(200,100) → (10,5)-(20,10).
    const { ctx, px } = pixelCtx(40, 20);
    paintRedacted(ctx as never, {} as CanvasImageSource, 40, 20, [{ x: 100, y: 50, w: 100, h: 50 }], 0.1);
    for (let j = 5; j < 10; j++) for (let i = 10; i < 20; i++) expect(px[j][i]).toBe('#000');
    // A 1 px safety margin, and the rest of the image untouched.
    expect(px[4][9]).toBe('#000');
    expect(px[15][30]).toBe('image');
    expect(px[0][0]).toBe('image');
  });

  it('downscales to at most 1280 px on the long side and never upscales', () => {
    expect(targetSize(1170, 2532)).toMatchObject({ width: 591, height: 1280 });
    expect(targetSize(2000, 1000)).toMatchObject({ width: 1280, height: 640 });
    expect(targetSize(600, 800)).toMatchObject({ width: 600, height: 800, scale: 1 });
  });

  it('steps JPEG quality down until the file is under 1.5 MB, and gives up if it never fits', () => {
    const url = (bytes: number) => 'data:image/jpeg;base64,' + 'A'.repeat(Math.ceil((bytes * 4) / 3));
    const asked: number[] = [];
    const out = encodeUnder((q) => {
      asked.push(q);
      return url(q > 0.6 ? 2_000_000 : 1_000_000);
    });
    expect(asked).toEqual([0.82, 0.72, 0.62, 0.5]);
    expect(dataUrlBytes(out)).toBeLessThanOrEqual(MAX_BYTES);
    expect(() => encodeUnder(() => url(3_000_000))).toThrow('too_big');
  });

  it('exports a JPEG at quality 0.82 from a fresh canvas and wipes the canvas afterwards', () => {
    const { ctx, px } = pixelCtx(591, 1280);
    const canvas = { width: 0, height: 0, getContext: () => ctx, toDataURL: vi.fn(() => 'data:image/jpeg;base64,AAAA') };
    const image = { naturalWidth: 1170, naturalHeight: 2532, width: 1170, height: 2532 } as unknown as HTMLImageElement;
    const out = prepareScreenshot(image, [topBarBox(1170, 2532)], () => canvas as unknown as HTMLCanvasElement);
    expect(out.startsWith('data:image/jpeg')).toBe(true);
    expect(canvas.toDataURL).toHaveBeenCalledWith('image/jpeg', 0.82);
    expect(px[10][300]).toBe('#000'); // inside the top bar
    expect(px[600][300]).toBe('image');
    expect(canvas.width).toBe(0);
  });

  it('builds boxes from a drag in any direction and keeps moved boxes inside the image', () => {
    expect(boxFromPoints({ x: 50, y: 40 }, { x: 10, y: 10 }, 100, 100)).toEqual({ x: 10, y: 10, w: 40, h: 30 });
    expect(boxFromPoints({ x: -5, y: 0 }, { x: 120, y: 10 }, 100, 100)).toEqual({ x: 0, y: 0, w: 100, h: 10 });
    expect(nudge({ x: 90, y: 0, w: 10, h: 10 }, 20, 0, 100, 100)).toMatchObject({ x: 90 });
    expect(nudge({ x: 0, y: 0, w: 10, h: 10 }, 5, 5, 100, 100, true)).toMatchObject({ w: 15, h: 15 });
  });
});
