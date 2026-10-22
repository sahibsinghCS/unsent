import en from '../i18n/en.json';
import es from '../i18n/es.json';
import { translate } from '../i18n';

function keys(node: unknown, prefix = ''): string[] {
  if (Array.isArray(node)) return [`${prefix}[${node.length}]`];
  if (node && typeof node === 'object')
    return Object.entries(node).flatMap(([k, v]) => (k === '_meta' ? [] : keys(v, prefix ? `${prefix}.${k}` : k)));
  return [prefix];
}

describe('i18n', () => {
  it('Spanish has exactly the same keys (and list lengths) as English', () => {
    expect(keys(es).sort()).toEqual(keys(en).sort());
  });
  it('Spanish is marked for native review', () => {
    expect(es._meta.needs_native_review).toBe(true);
  });
  it('fills placeholders', () => {
    expect(translate('en', 'chat.typing', { name: 'Maya' })).toBe('Maya is typing');
    expect(translate('es', 'chat.typing', { name: 'Maya' })).toBe('Maya está escribiendo');
  });
  it('returns the key for unknown strings instead of crashing', () => {
    expect(translate('en', 'nope.missing')).toBe('nope.missing');
  });
  it('keeps 988 and 911 in the footer in both languages', () => {
    for (const lang of ['en', 'es'] as const) {
      expect(translate(lang, 'app.footer')).toMatch(/988/);
      expect(translate(lang, 'app.footer')).toMatch(/911/);
    }
  });
});
