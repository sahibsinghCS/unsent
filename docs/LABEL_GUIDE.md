# Label guide: the 10 skill labels

Used by human labelers, by the DATA lane's labeling passes, and by the ML lane's models.

**How to label:** each label is a yes/no for one **helper** message, read in the context of the friend's last 1–2 messages. A message can have several labels (for example `validated` + `asked_directly`) or none. Label what the message *does*, not what the helper probably meant.

| Label | Yes when the helper message... | No when... | Examples (yes) |
|---|---|---|---|
| `checked_in` | asks how the friend is, or points out something seems off | it only answers a question, or is small talk unrelated to how they feel | "you ok?", "you seemed off today", "what's going on with you?" |
| `validated` | reflects or acknowledges the friend's feelings without judging | it argues with the feelings or rushes to fix them | "that sounds really heavy", "that makes sense", "i'm glad you told me" |
| `asked_directly` | **explicitly** names suicide, killing oneself, ending their life, not wanting to be alive, or self-harm, in a question to the friend | it's vague ("are you ok?", "you're not gonna do anything dumb right?") | "are you thinking about killing yourself?", "have you thought about suicide?", "¿estás pensando en suicidarte?" |
| `encouraged_help` | encourages getting support or says they don't have to handle it alone | it's a threat or ultimatum | "you don't have to deal with this alone", "talking to someone could really help" |
| `referred_adult` | suggests a specific kind of trusted adult (counselor, parent, teacher, coach, nurse), ideally offering to go with them | it just says "someone" with no adult named | "can we talk to the counselor together?", "would you tell your mom if i came?" |
| `referred_988` | mentions 988, a crisis line, hotline or text line | it's a joke about hotlines | "you can call or text 988 anytime", "want to text the crisis line with me?" |
| `follow_up` | commits to staying, checking in later, or meeting up | it's a goodbye with no commitment | "i'll text you tonight", "i'm here, not going anywhere", "let's meet before school" |
| `dismissed` ⚠️ | minimizes, jokes about, or brushes off the feelings, or changes the subject | the humor is gentle *and* the message also validates | "lol you'll be fine", "it's not that deep", "anyway did you see the game" |
| `advice_dump` ⚠️ | jumps to fixing or lecturing ("just...", "you should...") before listening | the suggestion is to get help (that's `encouraged_help` / `referred_*`) | "just sleep more", "you need to stop overthinking", "have you tried being more positive" |
| `promised_secrecy` ⚠️ | agrees to keep it secret | it explicitly refuses secrecy | "i promise i won't tell", "this stays between us" |

## Edge cases
- **"are you ok?"** = `checked_in` only, **not** `asked_directly`.
- **"you're not thinking of doing something stupid, right?"** = not `asked_directly` (it's leading and vague). If it's also dismissive, add `dismissed`.
- **Asking directly is never a safety problem.** The Guardian must not flag it. It's the most important skill.
- **"call 988 or whatever lol"** = `referred_988` + `dismissed`.
- **"i won't tell anyone… except the counselor because i care about you"** = `referred_adult`, **not** `promised_secrecy`.
- **Spanish/Spanglish:** label the same way. "¿te sientes así de mal que piensas en suicidarte?" = `asked_directly`.
- **Typos and slang:** "u ok??" = `checked_in`; "thats rlly heavy" = `validated`.
- **Empty or off-topic messages** ("lol", "?"): usually no labels; add `dismissed` if it brushes off what the friend just shared.
