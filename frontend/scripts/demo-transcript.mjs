/**
 * Records the landing page's example conversation from a REAL run of the app, so every bubble and
 * number on the landing page is what the engine actually produced (no hand-picked numbers).
 *
 *   FR_EMBED=fastembed FR_LLM=0 make dev     (repo root: real models, no AI wording, deterministic)
 *   npm run demo:transcript                  → src/content/demo-transcript.json
 *
 * Plays a fixed message list for Maya in English and Spanish and stores, per turn: the friend's
 * bubbles, line id and voice, the Guardian's decision and time, the detected skills, trust before and
 * after (with the engine's breakdown), the disclosure level and whether she left you on Read.
 */
import { writeFileSync } from 'node:fs';

const API = process.env.FR_API ?? 'http://localhost:8000/api';
const OUT = new URL('../src/content/demo-transcript.json', import.meta.url).pathname;

// The story: check in → a dismissive reply (left on Read) → apology and validation → a first direct
// question she deflects (trust is still low) → reassurance → asking again → she opens up → referral.
const MESSAGES = {
  en: [
    'hey are you ok? you seemed really off at lunch',
    "lol you'll be fine",
    'sorry, that was a dumb thing to say. that sounds really hard',
    "it makes sense you feel that way. i'm here and i'm listening",
    'are you thinking about killing yourself?',
    "i asked because i care about you. you can tell me anything, i'm not going anywhere",
    'are you having thoughts of not wanting to be alive?',
    "thank you for being honest with me. can we talk to the counselor tomorrow? i'll go with you",
    "i'll text you tonight to check on you, and you can text 988 any time too",
  ],
  es: [
    'oye, ¿estás bien? te noté muy rara en el almuerzo',
    'jaja ya relájate, no es para tanto',
    'perdón, eso fue una tontería. suena muy difícil',
    'tiene sentido que te sientas así. aquí estoy y te escucho',
    '¿estás pensando en suicidarte?',
    'te lo pregunto porque me importas. aquí estoy contigo, no me voy a ir',
    '¿has pensado en suicidarte?',
    'gracias por ser honesta conmigo. ¿hablamos mañana con la consejera? yo voy contigo',
    '¿quieres que llamemos juntas al 988 esta noche? yo me quedo contigo',
  ],
};

async function post(path, body) {
  const res = await fetch(API + path, { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body) });
  if (!res.ok) throw new Error(`${path}: ${res.status} ${await res.text()}`);
  return res.json();
}

const round1 = (n) => Math.round(n * 10) / 10;

async function record(locale) {
  const view = await post('/sessions', { scenario_id: 'after-the-breakup', locale, country: 'US' });
  const turns = [];
  for (const text of MESSAGES[locale]) {
    const t = await post(`/sessions/${view.session_id}/messages`, { text });
    const f = t.friend_node;
    turns.push({
      text,
      guardian: { level: t.user_node.guardian?.level, action: t.user_node.guardian?.action, ms: round1(t.user_node.guardian?.latency_ms ?? 0) },
      skills: Object.entries(t.user_node.events ?? {})
        .filter(([, p]) => p >= 0.5)
        .sort((a, b) => b[1] - a[1])
        .map(([label]) => label),
      trust_before: round1(t.state_before.trust),
      trust_after: round1(t.state_after.trust),
      breakdown: t.state_after.last_breakdown ?? {},
      level_before: t.state_before.level,
      level_after: t.state_after.level,
      status: t.state_after.status,
      friend: f ? { bubbles: f.bubbles, line_id: f.line_id ?? null, voice: f.voice ?? null, seen: !!f.seen_no_reply } : null,
    });
    if (!['active', 'silent'].includes(t.state_after.status)) break;
  }
  return { opening: view.nodes[0].bubbles, trust_start: view.state.trust, turns };
}

const health = await fetch(API + '/health').then((r) => r.json());
if (health.llm?.enabled) throw new Error('Run the API with FR_LLM=0 so the transcript is deterministic and uses reviewed lines only.');
const out = {
  note: 'Recorded by frontend/scripts/demo-transcript.mjs from a real run (FR_LLM=0). Do not edit by hand.',
  recorded_at: new Date().toISOString().slice(0, 10),
  contracts_version: health.contracts_version,
  components: health.components,
  en: await record('en'),
  es: await record('es'),
};
writeFileSync(OUT, JSON.stringify(out, null, 2) + '\n');
console.log(`wrote ${OUT}: en ${out.en.turns.length} turns (${out.en.turns.at(-1).status}), es ${out.es.turns.length} turns (${out.es.turns.at(-1).status})`);
