import { loadRealMode, offlineRealMode } from '../lib/realmode';

afterEach(() => vi.unstubAllGlobals());

describe('Real mode offline fallback (bundled content)', () => {
  it('has the fixed steps and the US line + 911 without any network', () => {
    const data = offlineRealMode('en', 'US');
    expect(data.steps.length).toBeGreaterThanOrEqual(5);
    expect(data.crisis.lines.map((l) => l.call)).toContain('988');
    expect(data.crisis.emergency).toBe('911');
    expect(data.crisis.lines.some((l) => l.country === '*')).toBe(true); // international directory too
  });

  it('switches language and country', () => {
    const es = offlineRealMode('es', 'GB');
    expect(es.lang).toBe('es');
    expect(es.crisis.emergency).toBe('999');
    expect(es.crisis.lines[0].name).toBe('Samaritans');
  });

  it('"other" falls back to the international directory and a generic emergency number', () => {
    const other = offlineRealMode('en', 'other');
    expect(other.crisis.lines.every((l) => l.country === '*')).toBe(true);
    expect(other.crisis.emergency).toMatch(/emergency/);
  });

  it('never mentions methods (safe-messaging spot check)', () => {
    const text = JSON.stringify([offlineRealMode('en', 'US'), offlineRealMode('es', 'US')]).toLowerCase();
    for (const word of ['pills?', 'overdose', 'guns?', 'rope', 'bridge']) expect(text).not.toMatch(new RegExp(`\\b${word}\\b`));
  });
});

describe('loadRealMode', () => {
  it('uses the API when it answers', async () => {
    const live = { ...offlineRealMode('en', 'US'), title: 'From the server' };
    vi.stubGlobal('fetch', vi.fn(() => Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(live) })));
    const result = await loadRealMode('en', 'US');
    expect(result.offline).toBe(false);
    expect(result.data.title).toBe('From the server');
  });

  it('falls back to the bundled copy when the API is down', async () => {
    vi.stubGlobal('fetch', vi.fn(() => Promise.reject(new TypeError('Failed to fetch'))));
    const result = await loadRealMode('en', 'US');
    expect(result.offline).toBe(true);
    expect(result.data.crisis.lines.map((l) => l.call)).toContain('988');
  });

  it('falls back when the API returns an error or an empty payload', async () => {
    vi.stubGlobal('fetch', vi.fn(() => Promise.resolve({ ok: false, status: 500, json: () => Promise.resolve({}) })));
    expect((await loadRealMode('es', 'US')).offline).toBe(true);
    vi.stubGlobal('fetch', vi.fn(() => Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve({ steps: [] }) })));
    expect((await loadRealMode('en', 'US')).offline).toBe(true);
  });
});
