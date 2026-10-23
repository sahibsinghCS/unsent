# "What if" rollouts

*Owner: whatif lane. Plain language, so Sahib can explain every part to a judge.*

## What it does
After a practice chat, you can click **"What if?"** on the message where you lost your friend (by default
the engine's *turning point*, the message where trust dropped the most). FirstReply then shows **three
better replies** you could have sent instead, and for each one it **plays the conversation forward**:
"if you'd said this, here's where it would have gone." Each card shows the reply, which skill it teaches,
a short simulated chat, a trust curve, and one card is marked **Best path**. A combined chart puts all
three next to what you actually did.

## How it works: we simulate the future with our own engine
Think of a chess engine that looks a few moves ahead before it suggests a move. "What if" does a small
version of that search, using the same pieces the real chat uses:

1. **Find better replies (candidates).** We only use the **reviewed exemplar bank**
   (`data/exemplars/<scenario>.<language>.jsonl`): example replies written for this exact friend and
   language. We look first at exemplars written for the friend's current disclosure level (±1).
   - We work out what the message was missing with the **critic's own rules** (for example "brushed off
     the feeling, so it needs listening", or "they sounded hopeless and you hadn't asked directly yet"),
     plus the skills the whole conversation never reached.
   - A candidate is kept only if **our trained skill detector** scores it at least **0.2 higher** than
     your message on the skill it teaches, it trips no negative label (dismissing, advice-dumping,
     promising secrecy), and the **Guardian** lets it through.
   - If the feedback report already showed a "Try instead" rewrite for that message, that rewrite is
     **candidate #1**, so the two screens never disagree.
   - We pick **3 different** ones with *maximal marginal relevance* (MMR): each pick must be relevant
     but different from the ones already picked (a different skill, and never a near-copy, measured with
     sentence embeddings).
2. **Play each one forward (rollout).** The candidate replaces your message and goes through the **real
   state engine** (trust, levels, gates, "Seen", endings) and the friend answers with the **reviewed line
   bank voice**, exactly the way the live chat does when the AI voice is off. Then we simulate **up to 3
   more helper messages**. For each of those, we try every unused exemplar, ask the engine "what would
   happen next?" (one-step look-ahead), and send the one that helps most: trust change + 10 × level gained
   (± 25 if the chat would end). A text is never sent twice. If the friend leaves you on Seen, or the
   chat ends, the simulation does exactly what the engine says.
3. **Score each path** with the value formula below and mark the best one.

### The value formula
`value = final trust + 10 × levels gained + 25 if the friend accepts help − 25 if they shut down − 10 for
every helper message after the first`.

- Trust is 0–100, and a level is the friend opening up one step (0 = surface … 4 = open to help), so a
  level is worth about one good message of trust.
- The −10 per extra message means *getting there sooner wins*: without it, a longer path would usually win
  just by piling up more trust. (We first tried −1; then a path that reached help in 2 messages lost to
  one that needed 4.)
- Ties go to the earlier card.

### What the numbers on a card mean
- **Critic score x.xx**: our skill detector's calibrated probability (0–1) that this reply shows the
  skill it teaches (the same per-message rubric score the feedback report uses). "0.92" means "our model
  is very sure this reply asks directly." It is *not* the trust or the value.
- **The trust curve** starts at the trust *before* the replaced message, then one point per simulated
  helper message.

### Faithfulness (the tricky part)
The engine has "diminishing returns": validating twice in a row counts less the second time. It remembers
the previous message's skills by the exact State object in memory, so copying or rebuilding a state would
silently forget them and change the result. Our rollouts never depend on that memory: they find the
skills of the message that produced the starting state (the same lookup the live engine makes) and pass
them to the engine explicitly every turn. A test replays real conversations from every message and checks
that the simulated states, "Seen" and friend lines are **identical** to the live chat; another test shows
the naive copy gives a different (wrong) trust.

### Speed
The detector and the Guardian re-embed the same ~40 exemplar texts at every look-ahead step. While a
simulation runs we wrap the shared embedder in a small cache (`whatif/cache.py`) so each text is embedded
once, on its own (so its vector never depends on which batch it came in). That took p95 from 2.6 s to
about 0.6 s with the real models, with identical results.

## Why this approach (and what we considered instead)
- **Bank voice, not the AI voice:** the simulation is deterministic (same chat → same three paths, every
  time), free (no OpenAI calls at all in this feature), and every friend line was written and reviewed
  ahead of time and passes the verifier and the Guardian. An AI-written future could say anything and
  would change every click.
- **Our engine, not an AI guess:** the future is computed by the same rules the real chat uses, so "what
  would have happened" is exactly what FirstReply would really do with that reply.
- **Exemplars, not AI-written suggestions:** human-written, scenario-specific, safe-messaging checked,
  and in the session's language.
- **Considered:** a deeper search (all combinations of 3 follow-ups is 40³ = 64,000 paths per card; too
  slow and it would just find the same top replies), and the old stub (3 fixed generic templates with the
  same second message, where every card's score was the "asked directly" probability, so a good
  validating reply showed "0.00").

## How we measured it (real numbers, with n and the split)
`python -m backend.app.whatif.evaluate` (run with `FR_EMBED=fastembed`, the real trained detector, and
the AI voice off) → `eval/reports/whatif_rollouts.json`. Split **"scripted"**: 18 scripted helper
conversations × 5 friends = **90 weak points**. Each script has one weak message (3 dismissive and
3 advice-dump texts), placed first, after a check-in, or after listening, followed by weak replies
("ok", "that sucks"…). These scripts are ours, not training data.

| Metric | Value | n |
|---|---|---|
| weak points with 3 paths of 3 different strategies | 100% | 90 |
| best path beats what was actually said (value) | 100% | 90 |
| best path beats what was actually said (final trust) | 100% | 90 |
| mean trust gain (best path − actual, 0–100 scale) | +76.2 | 90 |
| best path ≥ a hand-written "textbook" continuation (validate → ask → refer → follow up) | 100% | 90 |
| mean value over that textbook continuation | +57.5 | 90 |
| best paths where the friend accepts help within the horizon | 100% | 90 |
| latency p50 / p95 (warm process, this box) | 0.49 s / 0.64 s | 90 |
| two runs identical | 100% | 90 |
| candidate messages the Guardian would block | 0 | 885 messages |
| friend bubbles failing `check_friend` | 0 | 2,183 bubbles |
| bubbles in the wrong language | 0 | 3,068 bubbles |

**Spanish** (split "scripted_es": the same 18 scripts translated, Maya only, n = 18): 3 diverse paths
100%, best beats what was said 100%, mean trust gain +71.2, best ≥ the Spanish textbook continuation
100% (mean value +65.9), success 100%, p50 / p95 0.55 s / 0.68 s, deterministic 100%, 0 / 190 unsafe
candidates, 0 / 502 unsafe friend bubbles, 0 / 692 bubbles in the wrong language.

**Read these honestly:** the scripted continuations are deliberately weak, so "beats what was said" is an
easy bar. The textbook comparison is the harder one; the search wins mostly because exemplars often
combine skills in one message ("that sounds crushing. are you having thoughts of suicide?"), and the
engine rewards each skill.

## Limitations
- **A simulation is not a real person.** It shows what *our engine* would do, not what a real friend
  would do. The UI says "simulated."
- **3-turn horizon:** the replaced message plus up to 3 more helper messages. Longer futures aren't shown.
- **Candidates come only from the reviewed exemplar bank** (about 40 per friend), so a reply is only as
  good as the best exemplar for that moment. If no exemplar beats your message on the skill it teaches,
  fewer than 3 cards (or none) appear; we never invent one.
- **Greedy look-ahead:** each later message is the best *next step*, not the best 3-step plan.
- **Spanish** works only where the friend has Spanish exemplars (today: Maya). A chat never mixes
  languages, so a Spanish chat without Spanish exemplars would get no cards rather than English ones.
- The evaluation uses scripted weak points, not real users' chats.

## Questions a judge might ask (with answers)
1. **"Is the 'what if' just made up by an AI?"** No. This feature makes zero AI calls. The replies come
   from a human-written exemplar bank, and the future is computed by our own deterministic engine with
   pre-written, reviewed friend lines. Click it twice and you get exactly the same answer.
2. **"How do you choose the three replies?"** We use the critic's rules to find what the message was
   missing, keep only exemplars our trained detector scores at least 0.2 higher on that skill and that the
   Guardian allows, put the feedback report's own rewrite first, and pick three different skills with MMR
   so you don't see three versions of the same idea.
3. **"How do you know the simulation matches the real app?"** We replay real conversations through the
   simulator from every message and check the states, "Seen" and friend lines are identical to the live
   chat. That test caught a real trap: the engine's diminishing-returns memory is lost if you copy a state.
4. **"What does 'Best path' mean?"** The highest value: final trust + 10 per level the friend opened up
   + 25 if they accept help − 25 if they shut down − 10 per extra message. It rewards getting your friend
   to help sooner, not just more trust.
5. **"Isn't 100% suspicious?"** Partly, and we say so: what it beats is weak on purpose. The more
   meaningful check is against a hand-written textbook continuation, which the search also beat in all 90
   cases, because good exemplars combine skills in one message. The real limit is that it's a model of a
   friend, not a person, and it only looks 3 messages ahead.
