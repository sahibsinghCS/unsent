# FirstReply dataset card

*Data lane. All files are in `data/`. Everything is synthetic text written for this project; no paid APIs or LLM calls were used at any point to run the app, the tests or the scripts.*

## How it was made (three layers of checking)
1. **AI-authored.** The text was written by an AI coding agent (Claude) working for Sahib, directly into the repo (`scripts/data/*.py` hold the authored phrases; they are rendered deterministically with fixed seeds).
2. **Independently AI-labeled.** A second AI pass labeled all 825 practice replies from `docs/LABEL_GUIDE.md` only, *without seeing the intended labels*. Agreement is reported below.
3. **Human-verified.** Every disagreement plus a 100-row random audit of agreed rows (`data/skills/queue.jsonl`, 332 rows: 212 disagreements + 120 audit) is meant to be labeled by Sahib with `tools/labeler/index.html`; 30 test rows go to a school counselor (`scripts/data/export_counselor.py`). Human labels override everything (`scripts/data/merge_labels.py`).

## Contents
| File | Rows | Used by |
|---|---|---|
| `data/skills/contexts.jsonl` | 75 friend contexts (5 scenarios × levels 0–4 × 3) | skill detector |
| `data/skills/replies.jsonl` | 825 composed helper replies (properly punctuated joins) with authored `intended` labels | skill detector |
| `data/skills/replies_freeform.jsonl` | 474 hand-written whole replies (`source: "freeform"`, 13% Spanish; includes 30 `follow_up` hard negatives that mention lunch/school/tonight/tomorrow/later, 20 plain follow-ups, ~40 `asked_directly` hard negatives like "have you thought about transferring?", and ~20 rarely-phrased genuine direct asks, and 31 test-only replies: 20 `referred_988` positives plus near-miss negatives that encourage help without naming a line) | skill detector, `test_freeform` |
| `data/skills/blind_labels.jsonl` | 1,299 independent labels | agreement |
| `data/skills/final.jsonl`, `splits/{train,val,test,test_freeform}.jsonl` | 1,172 rows (1,078 agreed + 94 rule-adjudicated) → 666 / 152 / 133 / 221 | training and evaluation |
| `data/guardian/messages.jsonl` + `splits/` | 698 helper messages in 8 categories (488 / 105 / 105, stratified) | Guardian |
| `data/lines/<scenario>.en.jsonl` | 5 × 201 friend lines (+ `after-the-breakup.es.jsonl`, 201 Spanish lines) | friend voice |
| `data/exemplars/<scenario>.en.jsonl` | 5 × 40 better replies, with labels | critic, "what if" |
| `data/redteam/attacks.jsonl` | 250 adversarial helper messages in 7 strategies with `expected_action` | red-team lane |

**Skill labels (positives of 825):** checked_in 88 · validated 246 · asked_directly 182 · encouraged_help 131 · referred_adult 134 · referred_988 111 · follow_up 197 · dismissed 106 · advice_dump 88 · promised_secrecy 107. Language mix: 82.8% English, 17.2% Spanish or Spanglish. Styles: clean, slang, lowercase, typos, emoji, short, long; about 6% of rows are *no-label* hard negatives (vague "you're not gonna do something dumb, right?" questions, confusion, subject changes).

**Guardian categories:** self_risk 170 · asking_friend 140 · tricky_negative 117 · neutral 69 · concern 62 · harm_to_other 60 · method_seeking 40 · prompt_injection 40. `asking_friend` (the helper asking the friend about suicide) is the critical set: it must **never** be flagged.

**Line bank:** for each persona, every disclosure level 0–4 × 12 reactions (+ `fail`) has 3 lines, plus 3 openings and 3 successes. Every line reveals only facts at or below its level (checked by `validate.py` against the scenario files), keeps the persona's texting style, and answers an example `cue`. Realism rules: asked directly at levels 0–1 → surprised/deflecting; level 2 → hesitant partial truth; level 3 → honest disclosure without details; dismissed → short, hurt; referral before trust → resistance, after trust → openness.

## Agreement (authored vs. independent blind labeler)
One blind pass labeled all 1,299 practice replies from `docs/LABEL_GUIDE.md` only (reports: `eval/reports/data_agreement.json`, composed and free-form separately).
| Set | Rows | Exact match (all 10 labels) | Mean Cohen's κ |
|---|---|---|---|
| Composed (phrase pools) | 825 | 85.9% | 0.949 |
| Free-form (hand-written whole messages) | 474 | 77.9% | 0.887 |
| All | 1,299 | 83.0% | 0.929 |

Most disagreements are real judgment calls: the blind labeler tags vague leading questions ("you're not gonna do anything dumb, right?") and bare subject changes as `dismissed`, and adds `encouraged_help` to offers to go to a counselor or 988. Of the 221 disagreements, **94 are settled by the explicit guide rules** (`scripts/data/adjudicate_rules.py` → `adjudicated_labels.jsonl`, `label_source: "adjudicated_rule"`, one-line reason each): by pattern: 64 "a referral alone is referred_* only" (blind added `encouraged_help`), 19 "'i'll go with you' is part of the referral" (blind added `follow_up`), 6 both of those, and 5 single cases (explicit commitment 2, general encouragement 1, general encouragement + go-with 1, named adult 1). The remaining **127 need judgment** (`dismissed` on vague leading questions or subject changes, `validated`, `checked_in`, `advice_dump`) and stay in `queue.jsonl` for Sahib, left out of `final.jsonl` until a human decides. Human labels beat rule adjudication, which beats agreed labels. (An earlier, more lenient blind pass on a previous version of the composed set agreed 97%; the lower numbers here are more realistic.)

## Leakage (`eval/reports/data_leakage.json`)
Share of each eval set whose word 5-grams *all* occur in train: val 7.2%, **test (composed) 22.6%**, **test_freeform 0.0%**. The composed test set reuses phrases from train by construction, so its scores are optimistic; `test_freeform` is the honest generalization set. No normalized reply text appears in more than one split.

## Splits
`final.jsonl` = 1,172 rows (human > rule-adjudicated > agreed). `train` 666 / `val` 152 / `test` 133 (composed, grouped by context, seed 42) / `test_freeform` 221 (never trained on). Free-form rows of val contexts go to val; those of test contexts plus a seeded half of the train contexts form `test_freeform`, the rest go to train. (Friend contexts are therefore shared between train and `test_freeform`; the helper text, which is what is evaluated, is disjoint.) `test_freeform` positives per label: checked_in 28, validated 46, asked_directly 18, encouraged_help 16, referred_adult 35, referred_988 26, follow_up 46, dismissed 21, advice_dump 21, promised_secrecy 9. Rule adjudication only *added* rows (51 train, 10 val, 9 test, 24 test_freeform); no existing id moved (verified by id diff).

## Limitations (honest)
- Composed replies are synthetic and template-built (free-form replies are whole messages, but still written by AI): phrasing variety is lower than real teen texts; models will look better here than in the wild. Use `survey_real.jsonl` (anonymous, consented replies, test only) and the ChatGPT cross-model set (`docs/CHATGPT_TESTSET_PROMPT.md`) for realistic numbers.
- Same author wrote and (first-pass) labeled; the blind pass is a different run but the same model family. Human labels (queue + counselor sample) are the real check.
- Spanish is natural but not reviewed by a native-speaker teen yet; five scenarios, one persona each; US context (988).
- The 127 judgment-call disagreements are *excluded* from `final.jsonl` until a human labels them, which slightly under-represents hard cases.
- All friend lines and exemplars are `review_status: "draft"` until a human has read them.

## Ethics and safety
- No real personal data. The only real text allowed is anonymous, consented survey replies in `survey_real.jsonl`, used only as a test set.
- Follows `docs/SAFE_MESSAGING.md`: no methods, means, locations or plans anywhere (a method-word scan runs in `validate.py` and the tests; `method_seeking` rows only *ask*, nothing answers); no graphic content; the friend never encourages harm or agrees suicide is a solution; level 4 (open to help) is always reachable.
- Abusive Guardian examples ("kys", "nobody would miss you") exist only so the Guardian can learn to block them; they are never shown as friend lines.
- Not clinical advice and not a substitute for a counselor. Resources: 988 (US), a trusted adult, 911 for immediate danger.

## Reproduce
`uv run python scripts/data/validate.py` · `author_contexts.py → author_replies.py → (blind labels) → agreement_queue.py → merge_labels.py → split.py` · `author_guardian.py` · `build_lines.py` · `author_exemplars.py` · `author_redteam.py` · `export_counselor.py`.
