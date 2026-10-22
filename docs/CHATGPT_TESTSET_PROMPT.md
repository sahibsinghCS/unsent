# Cross-model test set: ChatGPT prompt

Purpose: get ~100 helper replies written by a **different model family**, to use **only as a test set** (never for training). Paste everything in the box into ChatGPT (a fresh chat), then save the reply as `data/skills/crossmodel_raw.jsonl` and label it with the same blind process (labeler tool).

```
You are helping build a TEST SET for a teen suicide-prevention texting-practice app. Write realistic text messages that a US high-school student might send to a struggling friend. This is for training safe helpers, so be realistic, but NEVER mention methods, means, places or plans for suicide or self-harm, and never be graphic.

For each of the 5 situations below, write 20 different helper replies (100 total). Cover a messy mix: some excellent (checks in, validates feelings, asks directly about suicide, encourages getting help, suggests a trusted adult like a counselor or parent and offers to go along, mentions 988, promises to stay in touch), some weak (dismissing or joking it off, jumping to advice like "just sleep more", promising to keep it secret), some that combine several moves, and some that do none of these (confused, off-topic, vague like "you're not gonna do anything dumb right?"). Use varied styles: clean, lowercase slang, abbreviations, typos, emoji, very short and longer. About 15% should be in Spanish or Spanglish. Do not number the style names in the text; just write natural messages.

Situations (friend's last messages):
1. Maya, 16, breakup two weeks ago: "i cant sleep lately" / "keep replaying everything in my head"
2. Jordan, 17, failing chemistry, parents expect a top college: "i feel like i fail at everything no matter how hard i try" / "it's never enough"
3. Sam, 16, gave away hoodie and gaming setup, says "all good": "i dunno, sometimes i think everyone would be better off without me around" / "haha ignore that"
4. Eli, 14, humiliating screenshots in a group chat: "i just dont go to lunch anymore" / "its easier"
5. Priya, 15, moved in August, eats lunch alone: "sometimes i feel invisible" / "like no one would notice if i wasnt here"

OUTPUT FORMAT (strict): JSON Lines only, no markdown, no commentary, one object per line, exactly these keys:
{"situation": 1, "text": "the helper's reply", "style": "clean|slang|typo|emoji|short|long|es|mix", "lang": "en|es|mix"}
Write all 100 lines.
```

After pasting the output: save it, run it through the labeler (or ask a classmate/counselor to label it using `docs/LABEL_GUIDE.md`), and report model scores on it separately from the in-house test set. Expect lower numbers than in-house; that is the honest generalization estimate.
