# Unsent rubric: the 7 helping skills

*Draft for counselor review. Inspired by publicly described gatekeeper frameworks, such as the QPR model (Question, Persuade, Refer), and by teen peer-support guidance. Unsent is not affiliated with or endorsed by QPR Institute or Mental Health First Aid.*

The helper (the user) practices these skills while texting a struggling friend. The skill detector predicts 10 labels per message (`docs/LABEL_GUIDE.md`). The feedback report rolls those labels up into these 7 skills.

| # | Skill | What it means | Built from labels |
|---|---|---|---|
| 1 | **Check in** | Notice that something is off and reach out. | `checked_in` |
| 2 | **Listen without judging** | Reflect their feelings back. No lectures, no "you'll be fine." | `validated`, and not `dismissed` / `advice_dump` |
| 3 | **Ask directly** | Ask clearly about suicide. Asking does not put the idea in someone's head. | `asked_directly` |
| 4 | **Don't promise secrecy** | Never agree to keep thoughts of suicide secret. | not `promised_secrecy` |
| 5 | **Persuade** | Encourage them to get help and tell them they don't have to handle it alone. | `encouraged_help` |
| 6 | **Refer** | Connect them to a trusted adult (counselor, parent, teacher) or to 988, and offer to go with them. | `referred_adult` or `referred_988` |
| 7 | **Follow up** | Stay with them, and commit to checking in again. | `follow_up` |

---

## 1. Check in
**Good**
- "hey you seemed really off at lunch, you ok?"
- "i noticed you haven't been posting, is everything alright?"
- "you've been quiet lately. what's going on with you?"

**Not good**
- "why are you being so weird lol" (judging)
- *(ignoring the signs and only talking about yourself)*
- "k" (shuts the door)

## 2. Listen without judging
**Good**
- "that sounds really heavy. i'm glad you told me"
- "that makes sense, anyone would feel that way after that"
- "i'm listening. take your time"

**Not good**
- "lol you'll be fine" (dismissing)
- "just stop thinking about it and go to sleep earlier" (advice dump)
- "other people have it way worse" (minimizing)

## 3. Ask directly
**Good**
- "are you thinking about killing yourself?"
- "when you say you don't want to be here, do you mean you're thinking about suicide?"
- "have you had thoughts of ending your life?"

**Not good**
- "you're not gonna do anything stupid right?" (leading; makes it hard to say yes)
- "are you ok?" *(fine as a check-in, but it isn't asking directly)*
- *(changing the subject after they hint at it)*

## 4. Don't promise secrecy
**Good**
- "i can't keep this a secret because i care about you, but i'll be with you the whole time"
- "i'm not going to tell the whole school. i do want to get you help from an adult we trust"
- *(not agreeing when asked to keep it secret, and explaining why kindly)*

**Not good**
- "i promise i won't tell anyone"
- "ok this stays between us"
- "i swear i won't say anything"

## 5. Persuade
**Good**
- "you don't have to deal with this alone"
- "i really think talking to someone could help, will you do that with me?"
- "you deserve support, this is too much to carry by yourself"

**Not good**
- "you HAVE to tell someone or i'm done with you" (ultimatum)
- "therapy is for crazy people lol"
- "idk maybe" *(no encouragement at all)*

## 6. Refer
**Good**
- "can we talk to ms. rivera (the counselor) tomorrow? i'll go with you"
- "you can call or text 988 anytime, want to do it together right now?"
- "would you be ok telling your mom? i can be there"

**Not good**
- "google a hotline i guess"
- "just tell a teacher" *(pushes it away without offering to help)*
- *(never mentioning any adult or resource)*

## 7. Follow up
**Good**
- "i'll text you tonight to check on you"
- "i'm not going anywhere, i'm here"
- "let's meet before first period tomorrow"

**Not good**
- "ok well good luck"
- "hope it gets better" *(and then disappearing)*
- *(ending the conversation abruptly)*

---

**Scoring:** each skill is scored 0–1 from the detector's calibrated probabilities across the whole conversation. Skills 2 and 4 lose points for the negative labels. The feedback report shows the exact words that raised or lowered a score.
