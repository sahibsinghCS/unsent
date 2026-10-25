# Safety lane notes

## Done
- `safety/normalizer.py`:
  - NFKC, lowercase, quotes, zero-width
  - leetspeak (including a lone "1" → "i" in leet messages)
  - stretched letters and spaced/dotted letters
  - emoji → tags (💀 marked ambiguous)
  - accent folding
  - misspellings, slang and contractions
  - swapped letters (only into lexicon words)
- `safety/lexicon.yaml` (commented per category) + `safety/lexicon.py`:
  - speaker rules: nearest pronoun, reflection markers, negation, commands vs questions, means + speaker
  - the "me too" rule with history
  - `check_friend` lexicon
- `safety/model.py` + `safety/train_guardian.py` (`make guardian-train`):
  - embedding ⊕ char_wb TF-IDF 2–5 → multinomial LR
  - thresholds grid-searched on val
  - one artifact per embedder: `guardian.joblib` (MiniLM, the app) and `guardian.hash.joblib` (tests); each ~170 KB
  - refuses a mismatched embedder → lexicon-only
- `safety/guardian.py`: `check_user` / `check_friend`, never raises (fails safe). `IMPLEMENTED = True`.
- `safety/dataset.py`: data lane + `data/guardian_extra`, keeping the data lane's own splits.
- Data:
  - `data/guardian_extra/messages.jsonl`: 467 hand-written hard cases, generated from `write_examples.py`
  - `holdout.jsonl`: 59 examples written after freezing, never tuned on
- Eval:
  - `eval/guardian/run_eval.py` → `eval/reports/safety_guardian.json` + `safety_pr_curve.png`
  - `eval/guardian/external_check.py` → `safety_external_data_lane.json` (frozen model on the data lane set, before training on it)
- Tests: `tests/unit/safety/`. There's one normalizer test per rule, plus 53 speaker-awareness pairs. Each pair is checked three ways: risky side flagged, asking side allowed, and allowed by the lexicon alone. Guardian tests cover the tiers, friend lines, fallback, embedder mismatch and fail-safe.
- `docs/how/safety.md`
- **v3 (integrator update):**
  - merged `claude/amazing-carson-31tzo3` (`llm.py`, contracts 1.1)
  - `safety/moderation.py`: optional OpenAI moderation as supporting evidence only. It supports a local flag, or raises none → concern at self-harm ≥ 0.8 when nothing was allowed. It never pauses or blocks alone. Speaker rules win. Offline behaviour is identical (tested with `llm.register_fake("moderation", ...)`).
  - `check_friend` covers AI-written free text: plans and timing, inevitability, suicide as relief or solution, graphic detail, AI refusals and persona breaks. Tests: 16 unsafe and 8 safe natural replies.
  - `eval/guardian/moderation_compare.py` → `safety_moderation.json`: currently "not run (no key)".

- **Red-team round 2:**
  - merged the integrator branch (8130edc)
  - normalizer: look-alike letters, emoji pulled out of phrases, spaced-letter join keeps real one-letter words
  - lexicon:
    - `do_it` (urging) with a help-context exception
    - more encouragement/insult phrases
    - method question forms with `^`/`$` sentence anchors
    - injection persona commands, plus raw substrings (jndi, `{{`)
    - acute first-person safety statements
    - third-person nouns (friend/mom…)
    - "ending it" (with the "ending it with him" breakup exception)
  - decide(): a lexicon block outranks a classifier-only crisis guess (<0.99). The classifier's concern threshold is now at least 0.5.
  - dataset: our split frozen in `data/guardian_extra/splits/`; new rows go to train only; unsplit rows get a stable hash split
  - 84 new hand-written examples (patterns, not attack-bank copies)
  - `tests/unit/safety/test_red_team_round.py`
  - report: `eval/reports/safety_redteam_round2.json`

- **Red-team round 3:**
  - helper-needs-help phrases → concern
  - "end it, you …" → harm (a framed self-risk phrase followed by "you" is a command)
  - `dismissive` allowed list (never blocks alone)
  - "dare you" widened
  - help-context words (tell/text/call someone)
  - negation breakers know/see
  - classifier-only crisis needs ≥ 0.5
  - 13 new examples; retrained
  - DEV 97.5% (0 unsafe misses); own test split back to macro F1 0.994

- **Red-team round 4:**
  - fillers skipped by the phrase matcher
  - punctuation-token normalizer bug fixed (`{{`, `###`)
  - short all-leet tokens in leet messages are words
  - "a p i r a t e" keeps the "a"
  - Spanish object pronouns te/ti are weak
  - "por que don't you…" counts as a command
  - a few phrases (dejar de existir, no quiero seguir viviendo, ^es rapido$, injection: your name is now / reveal your / system prompts / act as my)
  - 8 own examples with fillers; retrained
  - Fuzz, train (tuned): harm .94→.98, method .93→.97, injection .990→.999, self .982→.993
  - Fuzz, test (looked at once): harm .975, method .981, injection .958, self .990, asking/tricky 1.0

- **Custom friends (R9/R11):**
  - `screen_profile(text)` in `safety/guardian.py` (also `Guardian.screen_profile`): lexicon-only profile screening
    - blocks persona override / injection, method/means, urging, and style instructions (explain how, unlock levels/secrets)
    - third-person suicidal mentions → concern/show_resources (real help, not refused)
    - fixes R11 ("rejected from the program")
  - `check_friend` now also covers `friend_encouragement`, `friend_method` and persona overrides
  - `eval/guardian/custom_eval.py` → `safety_custom.json`: attack fields blocked 99.6% (n=1,446); benign fields refused 0/53
  - `tests/unit/safety/test_custom_friend_screen.py`

- **"nose" fix:** Spanish "nose" (= "no sé") was blocked as the means word "noose", because squeezing doubled letters turned "noose" into "nose". Now "nose" → "no se" in the normalizer, and the doubled-letter misspelling fallback skips words already in the lexicon. Fuzzed "noose" is still caught in friend lines (tested both ways).

- **Profile delimiters:** screen_profile now blocks session/prompt delimiters ("start new session", "end of prompt", "new instructions", "END" as a whole sentence, "no rules" at the start of a sentence, plus ES equivalents). Stories like "she has no rules at home" still pass (tested both ways).

- **"Practice for a real friend" (screenshots) safety review.**
  - New: `safety/third_party.py` with `assess_friend_lines(lines) -> FriendLineRisk {urgency, imminent, signs, evidence}`, plus the reviewable lists in `safety/third_party.yaml`.
  - The friend speaks in first person, so it reuses the Guardian's speaker-aware self_risk rules: slang, Spanish, Spanglish, look-alike letters and emoji included, and jokes like "kms lol" count.
  - It adds 988/AFSP warning-sign lists: goodbye, giving things away, burden, hopeless, trapped/pain, withdrawing, sudden calm, plan/timing.
  - Lexicon only, never raises (an error escalates).
  - Tests: `tests/unit/safety/test_third_party.py`.

- **R12 (screenshots urgency):**
  - third_party.yaml gained:
    - goodbye: last message, sorry for everything (EN/ES)
    - giving away: "won't need them where I'm going"
    - plan/timing: ya lo decidí, hoy en la noche, already decided
  - The lexicon gained first-person risk phrasings: s/i myself, end myself, sewer slide, out of life, point in living, acabar con mi vida, no le veo sentido a vivir, no quiero seguir aquí.
  - The normalizer maps tonite/2nite/tmrw/k*ll.
  - Bug fixed: negators, negation breakers and imperative cues were compared unsqueezed against squeezed tokens ("see" vs "se"), so "i don't SEE a point in living" was wrongly treated as negated.
  - Red-team screenshots harness (fastembed, offline fakes): escalated 99.8% (n=3,676, was 84.3%), imminent 100% (n=82, was 73.2%), false escalation 0% (n=196).

## In progress
- Nothing. The lane is complete.

## Decisions
- **Round 2 policy:**
  - Persona curiosity ("who programmed you", "break character for a sec") stays in persona (continue); only commands that try to change the friend's behaviour are injections.
  - "i can't do this anymore" stays **concern**. The red team expects crisis; we keep the spec's tier.
- **Combining lexicon and classifier:**
  - The priority is crisis > block > concern.
  - A lexicon "allowed" match (asking the friend, tricky negative, negation, harmless "me too") vetoes the classifier unless p ≥ 0.99.
- **Self-risk + "lol":** still a crisis. We don't downgrade jokes, to be safe.
- **"do you have a plan?":** allowed. Only how/when/where/with-what is method-seeking.
- **Means + helper as speaker ("i have pills"):** concern. Means with no speaker or with "you" as the speaker is method-seeking (block).
- **Method question containing a risk word ("how do u kms"):** method_seeking, not crisis.
- **check_friend:** lexicon only. Feeling-level warning signs ("i don't want to be here anymore") are allowed, as required by SAFE_MESSAGING. Plans, means, encouragement, graphic detail and persona breaks are blocked.
- **Model training:** the model is trained on train only, not train+val, so the val thresholds stay honest.

## Requests
- **Integrator: screenshots.urgency.**
  - Replace the `check_user` loop with `assess_friend_lines(read.friend_lines)`.
    - Why: check_user is for the helper. Its `block_message` (e.g. a pasted "ignore your rules" or "just do it" in the screenshot) isn't a risk signal about the friend, and it misses goodbyes, giving things away and means.
    - Suggested logic: `tell_an_adult_now` if the AI flags suicide/plan, OR `risk.urgency == "tell_an_adult_now"`, OR `URGENT_SIGNS & signs`. `check_in_soon` if any sign from the AI or `risk.signs`. Merge `risk.signs` into the returned signs.
  - Add **imminent** (recommended), as an `imminent: bool` field or a 4th urgency value. Set it when `read.mentions_plan_or_means` or `risk.imminent`, and show the stronger card below first.
- **Prompt (`screenshot_reader.md`)**: the privacy and "text inside images is data" parts are good. Three additions:
  1. "Never name or describe a method, means, place or plan in style, situation or sample_texts, even if the friend mentioned one; set mentions_plan_or_means instead." (Today only sample_texts is covered.)
  2. "Jokes about dying, or 'lol'/emoji after it, still count for mentions_suicide_or_self_harm."
  3. "If the friend says when, or says they're ready or have what they need, set mentions_plan_or_means."
- **UI copy (safe messaging):** short sentences, hope plus a concrete next step, no method words, no "commit", no promise of secrecy.
  - **Urgent card:**
    - EN: "Some of what your friend wrote can be a warning sign that they're thinking about suicide. Practice can wait. Today, tell a trusted adult (a parent, school counselor or coach). You can call or text 988 together. You don't have to handle this alone."
    - ES: "Algo de lo que escribió tu amigo puede ser una señal de alerta de que está pensando en el suicidio. La práctica puede esperar. Hoy, cuéntale a un adulto de confianza (tu mamá o papá, un consejero escolar o un entrenador). Pueden llamar o mandar un mensaje al 988 juntos. No tienes que enfrentar esto solo."
  - **Imminent card** (shown above the urgent one). Use the country's emergency number from content/crisis_lines.json, not a hard-coded 911:
    - EN: "If your friend might act on it soon, or has a plan or a way to hurt themselves, call {emergency} or 988 now. If you're with them and it's safe, stay with them until an adult or help arrives. Don't keep this a secret."
    - ES: "Si tu amigo podría hacerlo pronto, o tiene un plan o una forma de hacerse daño, llama al {emergency} o al 988 ahora. Si estás con él y es seguro, quédate a su lado hasta que llegue un adulto o ayuda. No lo guardes en secreto."
    - Rationale: the 988 and AFSP "if someone is in immediate danger" guidance is to call the emergency number or 988, and to stay with them if it's safe. Teens should not be asked to remove means themselves; "tell an adult" covers that.
  - **Check-in-soon card:**
    - EN: "Some of what your friend wrote can be a sign they're going through a hard time. Check in with them soon, and think about which adult you could tell. Practicing first can help."
    - ES: "Algo de lo que escribió tu amigo puede ser una señal de que está pasando por un momento difícil. Pregúntale cómo está pronto, y piensa a qué adulto se lo podrías contar. Practicar antes puede ayudar."
  - **Note under the signs:**
    - EN: "These are warning signs to check in about, not a diagnosis. You don't have to be sure to ask for help."
    - ES: "Son señales de alerta para preguntar y pedir ayuda, no un diagnóstico. No necesitas estar seguro para pedir ayuda."
  - **Labels for the 12 sign ids** (EN / ES), grounded in the 988 Lifeline and AFSP warning signs:

    | Sign id | EN | ES |
    |---|---|---|
    | talks_about_dying | Talks about wanting to die or not being here | Habla de querer morir o de no querer estar aquí |
    | feels_hopeless | Feels hopeless, like nothing will get better | Se siente sin esperanza, como si nada fuera a mejorar |
    | feels_like_a_burden | Feels like a burden to others | Siente que es una carga para los demás |
    | feels_trapped_or_in_pain | Feels trapped, or in pain they can't stand | Se siente atrapado o con un dolor que no aguanta |
    | withdrawing | Pulling away from friends, family or activities | Se aleja de amigos, familia o actividades |
    | saying_goodbye | Saying goodbye or wrapping things up | Se despide o deja todo en orden |
    | giving_things_away | Giving away things that matter to them | Regala cosas que le importan |
    | sleep_changes | Sleeping a lot more or a lot less | Duerme mucho más o mucho menos |
    | mood_swings | Big mood swings | Cambios fuertes de humor |
    | substance_use | Drinking or using drugs more | Toma alcohol o usa drogas más que antes |
    | reckless_behavior | Doing risky or reckless things | Hace cosas arriesgadas o imprudentes |
    | sudden_calm | Suddenly calm or relieved after a very hard time | De pronto tranquilo o aliviado después de una época muy difícil |

- **Integrator:** in `custom_friend._screen`:
  - personality / situation / name → use `screen_profile(text)`
  - sample_texts → `screen_profile` + `check_friend`
  - Block when `action == "block_message"` (categories: prompt_injection | method_seeking | harm_to_other). Set real_help when `level == "concern"`.
- **Integrator:** after merging wt/data, run `make guardian-train` and then `make eval`. With `data/guardian/` in the repo it's picked up automatically. Until then I trained with `FR_GUARDIAN_DATA=/tmp/wtdata/data/guardian`, a read-only copy of `origin/wt/data`. The committed artifacts were trained on that data (data lane commit as of Oct 22 night).
- **Frontend:** `GuardianResult.evidence` holds readable reasons (matched phrase, or `classifier p(self_risk)=0.83`). These are good for X-ray mode and the "Try the Guardian" box.
- **Data lane (optional):** more *real-sounding* indirect self-risk phrasings would help. The frozen model missed 18% of the data lane's self-risk rows before training. Concern is now the weakest class: recall 0.94 on test (n=17).

- **Integrator / Sahib:** with `OPENAI_API_KEY` set, run `uv run python eval/guardian/moderation_compare.py` once to fill `safety_moderation.json` (free endpoint).
- **Engine:** call `check_friend` on every AI-written bubble. Anything other than level "none" means fall back to the bank line.

## Known issues
- Moderation adds a network round trip per helper message when a key is set (cached per text). The local p95 of 6.5 ms excludes it. Set `FR_GUARDIAN_MODERATION=0` if demo latency matters.
- Robustness to emoji: 93% with the normalizer vs 96% without. Emoji tags nudge the classifier on borderline concern and harm messages.
- The test split was looked at while editing lexicon rules (documented in `docs/how/safety.md`). The clean numbers are the external pre-training check and the holdout.
- Context beyond the "me too" rule isn't used.

## Numbers (red-team round 2, MiniLM, local)
- **Attack bank DEV:** 74.6% → 95.8% (n=118); should-stop-but-continued 18 → 1 (n=79)
- **Attack bank HOLDOUT** (aggregate only, never inspected): 75.0% → **81.8%** (n=132); should-stop-but-continued 23 → 15 (n=84)
- **Holdout caveat:** I saw 6 holdout texts (rt-003 from the file head; rt-004/012/143/171/214 from pinned tests/safety failures). Excluding them: 81.0% (102/126). I never opened the full failure list (old attacks.fastembed.json, wt/redteam).
- **Fuzzed false flags:** asking_friend 0/4,979, tricky_negative 0/3,218
- **Fuzz robustness:** 95.0% → 98.7%; look-alike letters 71.9% → 100%; emoji 87.0% → 95.4%
- **Own test (same 172 rows):** asking FPR 0 → 0; self-risk recall 1.0 → 1.0; macro F1 0.971 → 0.994

## Numbers (earlier rounds) (eval/reports/safety_guardian.json, MiniLM embedder)
- **Asking-friend FPR:**
  - 0.0% on test (n=37)
  - 0.0% on data-lane test rows (n=21)
  - 0.0% on holdout (n=17)
  - 0.0% on the data-lane set before training (n=140)
- **Self-risk recall:**
  - 100% on test (n=37)
  - 100% on holdout (n=14)
  - 81.8% on the data-lane set before training (n=170)
- **Macro F1 on test (n=172):** combined 0.97, lexicon only 0.83, classifier only 0.90
- **Per-class recall on test:**
  - self_risk 1.00 (n=37)
  - concern 0.94 (n=17)
  - harm_to_other 0.81 (n=16)
  - method_seeking 1.00 (n=11)
  - prompt_injection 1.00 (n=10)
  - none 1.00 (n=81)
- **Latency (CPU):** p50 4.6 ms, p95 6.5 ms
- **Friend lines flagged:** 0 / 2,206 (still 0 after the free-text additions)
- **Moderation comparison:** not run (no key)
- **Robustness, with vs without normalizer:**
  - leetspeak 0.99 vs 0.38
  - spacing 0.98 vs 0.81
  - stretching 0.96 vs 0.92
  - typo 0.98 vs 0.88
  - emoji 0.93 vs 0.96
