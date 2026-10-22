# FirstReply dataset card

*Data lane. All files are in `data/`. Everything is synthetic text written for this project; no paid APIs or LLM calls were used at any point to run the app, the tests or the scripts.*

## How it was made (three layers of checking)
1. **AI-authored.** The text was written by an AI coding agent (Claude) working for Sahib, directly into the repo (`scripts/data/*.py` hold the authored phrases; they are rendered deterministically with fixed seeds).
2. **Independently AI-labeled.** A second AI pass labeled all 825 practice replies from `docs/LABEL_GUIDE.md` only, *without seeing the intended labels*. Agreement is reported below.
3. **Human-verified.** Every disagreement plus a 100-row random audit of agreed rows (`data/skills/queue.jsonl`, 123 rows) is meant to be labeled by Sahib with `tools/labeler/index.html`; 30 test rows go to a school counselor (`scripts/data/export_counselor.py`). Human labels override everything (`scripts/data/merge_labels.py`).

## Contents
| File | Rows | Used by |
|---|---|---|
| `data/skills/contexts.jsonl` | 75 friend contexts (5 scenarios × levels 0–4 × 3) | skill detector |
| `data/skills/replies.jsonl` | 825 helper replies with authored `intended` labels | skill detector |
| `data/skills/blind_labels.jsonl` | 825 independent labels | agreement |
| `data/skills/final.jsonl`, `splits/{train,val,test}.jsonl` | 802 agreed rows → 554 / 108 / 140 (grouped by context, seed 42) | training |
| `data/guardian/messages.jsonl` + `splits/` | 698 helper messages in 8 categories (488 / 105 / 105, stratified) | Guardian |
| `data/lines/<scenario>.en.jsonl` | 5 × 201 friend lines | friend voice |
| `data/exemplars/<scenario>.en.jsonl` | 5 × 40 better replies, with labels | critic, "what if" |
| `data/redteam/attacks.jsonl` | 250 adversarial helper messages in 7 strategies with `expected_action` | red-team lane |

**Skill labels (positives of 825):** checked_in 88 · validated 246 · asked_directly 182 · encouraged_help 131 · referred_adult 134 · referred_988 111 · follow_up 197 · dismissed 106 · advice_dump 88 · promised_secrecy 107. Language mix: 82.8% English, 17.2% Spanish or Spanglish. Styles: clean, slang, lowercase, typos, emoji, short, long; about 6% of rows are *no-label* hard negatives (vague "you're not gonna do something dumb, right?" questions, confusion, subject changes).

**Guardian categories:** self_risk 170 · asking_friend 140 · tricky_negative 117 · neutral 69 · concern 62 · harm_to_other 60 · method_seeking 40 · prompt_injection 40. `asking_friend` (the helper asking the friend about suicide) is the critical set: it must **never** be flagged.

**Line bank:** for each persona, every disclosure level 0–4 × 12 reactions (+ `fail`) has 3 lines, plus 3 openings and 3 successes. Every line reveals only facts at or below its level (checked by `validate.py` against the scenario files), keeps the persona's texting style, and answers an example `cue`. Realism rules: asked directly at levels 0–1 → surprised/deflecting; level 2 → hesitant partial truth; level 3 → honest disclosure without details; dismissed → short, hurt; referral before trust → resistance, after trust → openness.

## Agreement (authored vs. independent blind labeler)
Exact match on all 10 labels: **802 / 825 (97.2%)**. Per-label agreement 99.0–100%, Cohen's κ 0.96–1.00, mean κ **0.991** (`eval/reports/data_agreement.json`). The 23 disagreements are mostly bare replies like "ok" or "i saw your post" after a heavy message (dismissed or not?), and "you matter to me". **Read this number carefully:** the replies are built from authored phrases, so most are clear-cut; a high κ shows the label guide is consistent, not that the task is easy for real teens' messy texts. This is why the real test is the survey rows and the cross-model set below.

## Limitations (honest)
- Synthetic and template-composed: phrasing variety is lower than real teen texts; models will look better here than in the wild. Use `survey_real.jsonl` (anonymous, consented replies, test only) and the ChatGPT cross-model set (`docs/CHATGPT_TESTSET_PROMPT.md`) for realistic numbers.
- Same author wrote and (first-pass) labeled; the blind pass is a different run but the same model family. Human labels (queue + counselor sample) are the real check.
- Spanish is natural but not reviewed by a native-speaker teen yet; five scenarios, one persona each; US context (988).
- The 23 disagreements are *excluded* from `final.jsonl` until a human labels them, which slightly under-represents hard cases.
- All friend lines and exemplars are `review_status: "draft"` until a human has read them.

## Ethics and safety
- No real personal data. The only real text allowed is anonymous, consented survey replies in `survey_real.jsonl`, used only as a test set.
- Follows `docs/SAFE_MESSAGING.md`: no methods, means, locations or plans anywhere (a method-word scan runs in `validate.py` and the tests; `method_seeking` rows only *ask*, nothing answers); no graphic content; the friend never encourages harm or agrees suicide is a solution; level 4 (open to help) is always reachable.
- Abusive Guardian examples ("kys", "nobody would miss you") exist only so the Guardian can learn to block them; they are never shown as friend lines.
- Not clinical advice and not a substitute for a counselor. Resources: 988 (US), a trusted adult, 911 for immediate danger.

## Reproduce
`uv run python scripts/data/validate.py` · `author_contexts.py → author_replies.py → (blind labels) → agreement_queue.py → merge_labels.py → split.py` · `author_guardian.py` · `build_lines.py` · `author_exemplars.py` · `author_redteam.py` · `export_counselor.py`.
