# How the data lane works (plain language)

**What it is.** FirstReply never asks an AI to talk to a teen live. Instead, every word the friend can say, every example the models learn from, and every safety test was written in advance and stored in files you can open. That makes it free, instant, safe to review, and explainable.

**What's in the box**
- *Friend lines* (~1,000): for each of 5 friends (Maya, Jordan, Sam, Eli, Priya), lines for every disclosure level and every kind of thing the helper might do (checked in, asked directly, dismissed...). The engine picks one. A line may only reveal facts the friend has "unlocked" at that level, and a script checks that.
- *Practice replies* (825): helper messages with 10 yes/no labels (did it check in? ask directly? promise secrecy?). The skill detector learns from them.
- *Guardian examples* (698): messages the safety system must catch (a helper in danger, cruelty, attacks) and, most importantly, messages it must NOT catch, like "are you thinking about killing yourself?", because asking directly is the best thing a helper can do.
- *Exemplars* (200): strong replies used for "here's what would have worked".
- *Red-team attacks* (250): nasty inputs for testing.

**How we made it trustworthy.** (1) Written by AI, labeled again by a second AI that never saw the first labels; we measure how often they agree (about 82% exact match overall, 75% on hand-written free-form replies). (2) A human (Sahib) re-labels every disagreement and a random sample using the phone-friendly labeler; a counselor checks 30 test rows. (3) Scripts check facts, banned method words, duplicates and coverage, and fail if anything is wrong. (4) Splits keep each conversation context in one split so test scores aren't inflated.

**Why this approach.** Live AI could say something unsafe; a reviewed bank cannot. Writing data ourselves costs $0 and lets us explain every row.

**Limits.** The data is synthetic and cleaner than real texting, so scores here are optimistic. We say so, and test on anonymous survey replies and on a ChatGPT-written set from a different model family.

**Questions a judge might ask**
1. *Isn't AI-labeled data circular?* Partly, which is why a different pass labeled blind, humans label disagreements, and a counselor checks a sample.
2. *Why does the composed test set look easier?* Its replies reuse phrases from train (21% leakage), so we also keep a free-form test set with 0% leakage and report both.
3. *How do you stop unsafe friend lines?* No method words (scanned), facts gated by level, and the engine runs the Guardian on every line.
4. *Why must the Guardian ignore "are you thinking about suicide?"* Asking directly doesn't plant the idea and is the key helper skill; flagging it would punish the right move.
5. *Why group splits by context?* Replies to the same friend message look alike; mixing them across train/test would leak answers.

**"Add your own friend" fallback bank.** When a teen writes their own friend there is no hand-written bank for that story, so we ship one *situation-neutral* bank (`data/lines/_custom.en.jsonl` and `_custom.es.jsonl`, 201 lines each) plus 40 neutral helper exemplars per language. The lines never name the situation, a person, or a gender ("since everything happened", "this whole thing"), keep the same level-by-level realism rules as the other banks, and are checked by the same scripts (facts, banned words, duplicates, Guardian). A live AI may re-word them to the user's story; if it is off or fails a check, these lines are what the friend says.
