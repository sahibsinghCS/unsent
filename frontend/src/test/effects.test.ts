/**
 * Guard against the "blank page after clicking a link" bug: a React effect may only return a cleanup
 * function or undefined. `useEffect(() => window.scrollTo(0, 0))` returned scrollTo's value, which
 * browser extensions can make non-undefined → React calls it as a cleanup → TypeError → blank page.
 * This scans the source so the pattern can't come back (the project has no ESLint).
 */
import { readdirSync, readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';

const SRC = join(__dirname, '..');

function files(dir: string): string[] {
  return readdirSync(dir).flatMap((name) => {
    const path = join(dir, name);
    if (statSync(path).isDirectory()) return name === 'test' ? [] : files(path);
    return /\.tsx?$/.test(name) ? [path] : [];
  });
}

const offenders = (pattern: RegExp) =>
  files(SRC).flatMap((file) =>
    readFileSync(file, 'utf8')
      .split('\n')
      .map((line, i) => ({ line, at: `${file.replace(SRC, 'src')}:${i + 1}` }))
      .filter(({ line }) => pattern.test(line))
      .map(({ at, line }) => `${at}  ${line.trim()}`),
  );

describe('effects never return a non-function', () => {
  it('no expression-bodied effects like useEffect(() => doSomething())', () => {
    // `() => () => {...}` (returning a cleanup) and `() => {` (block body) are fine.
    expect(offenders(/use(Layout)?Effect\(\s*\(\)\s*=>(?!\s*[{(])/)).toEqual([]);
  });
  it('no effects that pass a callback directly, like useEffect(load, [load])', () => {
    expect(offenders(/use(Layout)?Effect\(\s*[A-Za-z_$][\w$]*\s*,/)).toEqual([]);
  });
  it('the scanner itself catches the original bug', () => {
    expect(/use(Layout)?Effect\(\s*\(\)\s*=>(?!\s*[{(])/.test('useEffect(() => window.scrollTo(0, 0), [pathname]);')).toBe(true);
    expect(/use(Layout)?Effect\(\s*[A-Za-z_$][\w$]*\s*,/.test('useEffect(load, [load]);')).toBe(true);
  });
});
