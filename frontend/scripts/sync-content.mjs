// Copies the fixed crisis content (repo-root content/) into src/content/ so it is bundled into the
// build. Real mode uses these copies when the API is unreachable. The copies are committed, so the
// frontend still builds on its own (e.g. in a Docker stage without the content/ folder).
import { copyFileSync, existsSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const src = join(here, '..', '..', 'content');
const dest = join(here, '..', 'src', 'content');
const files = ['realmode.en.json', 'realmode.es.json', 'crisis_lines.json'];

mkdirSync(dest, { recursive: true });
for (const file of files) {
  if (existsSync(join(src, file))) copyFileSync(join(src, file), join(dest, file));
  else console.warn(`sync-content: ${file} not found, keeping the committed copy`);
}
