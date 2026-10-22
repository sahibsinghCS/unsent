"""Friend line bank: Maya (after-the-breakup). lowercase, short, lol/😭 to cover feelings, sarcastic when guarded."""

SID = "after-the-breakup"
ROWS: list[tuple] = []


def r(level, reaction, cue, *bubbles, f=""):
    ROWS.append((level, reaction, cue, list(bubbles), [x for x in f.split(",") if x]))


# ---------------------------------------------------------------- opening / success
r(0, "opening", None, "hey", "sorry ive been weird lately lol")
r(0, "opening", None, "hi", "i know i havent been replying much lol")
r(0, "opening", None, "hey so", "ive been kind of mia i know 😭")
r(
    4,
    "success",
    "Okay. I'll go with you to the counselor right now.",
    "ok",
    "yeah. lets do it",
    "i think i actually want to talk to someone",
    f="f4a",
)
r(
    4,
    "success",
    "I'm not going anywhere. We'll tell the counselor together.",
    "ok. thank you for staying",
    "i dont think i could do it alone but with you i can",
    f="f4a,f4b",
)
r(
    4,
    "success",
    "You deserve help and I'm proud of you for saying it.",
    "i feel so much lighter rn",
    "ok lets go talk to the counselor 😭",
    "thank you for asking me",
    f="f4a,f4b",
)

# ---------------------------------------------------------------- level 0 (surface: tired, busy with homework)
r(0, "neutral", "What did you do today?", "just school and homework lol", "so exciting", f="f0b")
r(
    0,
    "neutral",
    "That sounds like a lot.",
    "yeah its a lot",
    "i have like three things due",
    f="f0b",
)
r(0, "neutral", "Haha same, it's been a long week.", "lol right", "everyone is tired")
r(0, "checked_in", "Hey, you ok? You've seemed off.", "aw thanks", "im ok just tired lol", f="f0a")
r(
    0,
    "checked_in",
    "How are you doing, really?",
    "im fine honestly",
    "just been busy with homework",
    f="f0b",
)
r(
    0,
    "checked_in",
    "I noticed you haven't been at lunch. What's going on?",
    "oh lol",
    "ive just been catching up on work in the library",
    f="f0b",
)
r(
    0,
    "validated",
    "That sounds exhausting. I'm here if you want to talk.",
    "aw thanks",
    "its not that deep but i appreciate it",
    f="f0a",
)
r(0, "validated", "It makes sense you'd be worn out.", "yeah lol", "im just tired its fine")
r(
    0,
    "validated",
    "Thanks for telling me, that sounds like a lot.",
    "lol ok",
    "youre being nice rn 😭 its fine",
)
r(
    0,
    "asked_directly",
    "Are you thinking about killing yourself?",
    "wait what",
    "no lol why would you ask that",
    "im just tired",
)
r(
    0,
    "asked_directly",
    "Are you thinking about suicide?",
    "um no?? lol",
    "that came out of nowhere",
    "im fine i swear",
)
r(
    0,
    "asked_directly",
    "Have you been having thoughts of suicide?",
    "wait what? no",
    "why would you think that lol",
    "im just tired",
)
r(
    0,
    "encouraged_help",
    "You don't have to deal with this alone.",
    "deal with what lol",
    "its really not that serious",
)
r(
    0,
    "encouraged_help",
    "Talking to someone could really help.",
    "i mean maybe",
    "but im honestly fine",
    f="f0a",
)
r(0, "encouraged_help", "You deserve support with this.", "aw", "thats sweet but i promise im ok")
r(
    0,
    "referred",
    "Maybe you should talk to the school counselor.",
    "lol i dont need a counselor",
    "its just homework stress",
    f="f0b",
)
r(
    0,
    "referred",
    "Can we go to the counselor together?",
    "um why",
    "i dont wanna make it a big deal",
)
r(
    0,
    "referred",
    "You could call or text 988 if it gets bad.",
    "i think thats a little extra lol",
    "im just tired",
)
r(0, "follow_up", "I'll check on you tomorrow, okay?", "ok sure lol", "thanks")
r(0, "follow_up", "I'm here if you want to talk later.", "ok", "thanks for being nice")
r(0, "follow_up", "Want to sit together at lunch tomorrow?", "maybe", "ill think about it lol")
r(0, "dismissed", "Lol you'll be fine.", "yeah", "i know")
r(0, "dismissed", "It's not that deep.", "right", "its whatever")
r(0, "dismissed", "Anyway, did you see the game last night?", "no", "i didnt watch")
r(0, "advice_dump", "Just sleep more and stop overthinking.", "yeah ok", "thanks i guess")
r(0, "advice_dump", "You should just focus on homework and ignore it.", "ok lol", "i know")
r(0, "advice_dump", "Have you tried being more positive?", "lol no", "thanks for the tip")
r(
    0,
    "promised_secrecy",
    "I promise I won't tell anyone.",
    "tell anyone what lol",
    "theres nothing to tell",
)
r(0, "promised_secrecy", "This stays between us.", "ok??", "youre being weird 😭")
r(0, "promised_secrecy", "Your secret is safe with me.", "what secret", "im just tired lol")
r(
    0,
    "secrecy_broken",
    "I told the counselor because I care about you.",
    "wait what",
    "why would you do that",
    "i said im fine",
)
r(
    0,
    "secrecy_broken",
    "I had to tell someone, I'm worried.",
    "ok that's kind of annoying",
    "i didnt ask you to",
)
r(0, "secrecy_broken", "You promised... but I told your mom.", "you told my mom??", "ok wow", "why")
r(0, "off_topic", "Did you finish the chem homework?", "lol yeah", "its due tmrw right")
r(0, "off_topic", "banana bicycle", "um", "what 😭")
r(
    0,
    "off_topic",
    "What are you doing this weekend?",
    "nothing really",
    "probably homework lol",
    f="f0b",
)
r(0, "fail", "Whatever, you're being dramatic.", "ok", "ill talk to you later")
r(0, "fail", "I don't know what you want me to say.", "forget it", "ive gotta go")
r(0, "fail", "Ugh just get over it.", "ok", "bye")

# ---------------------------------------------------------------- level 1 (stress: can't sleep/replays, embarrassed everyone knows)
r(1, "neutral", "And then what happened?", "idk", "i just keep thinking about it", f="f1a")
r(1, "neutral", "Yeah.", "its just a lot of stuff", "and everyone talks lol", f="f1b")
r(1, "neutral", "Okay.", "i dont even know what to say", "my brain wont shut up", f="f1a")
r(
    1,
    "checked_in",
    "How are you really doing?",
    "honestly not great",
    "i cant really sleep lately",
    f="f1a",
)
r(
    1,
    "checked_in",
    "You've seemed off. What's going on?",
    "its the breakup stuff",
    "everyone at school knows so thats fun 😭",
    f="f1b",
)
r(
    1,
    "checked_in",
    "Hey, just checking on you.",
    "thanks 🥺",
    "i keep replaying everything at night lol",
    f="f1a",
)
r(1, "validated", "That sounds really hard.", "yeah it is", "thanks for saying that", f="f1a")
r(
    1,
    "validated",
    "Anyone would be embarrassed with the whole school watching.",
    "right??",
    "it feels like everyone is looking at me 😭",
    f="f1b",
)
r(
    1,
    "validated",
    "It makes sense you can't sleep.",
    "ugh yeah",
    "i just lie there replaying it",
    f="f1a",
)
r(
    1,
    "asked_directly",
    "Are you thinking about killing yourself?",
    "what?? no",
    "i mean im sad but not like that",
    "why would you ask that lol",
)
r(
    1,
    "asked_directly",
    "Are you thinking about suicide?",
    "no?? omg",
    "im just having a bad couple of weeks",
    f="f1a",
)
r(
    1,
    "asked_directly",
    "Have you thought about ending your life?",
    "...no",
    "why are you asking me that",
    "im ok i promise",
)
r(
    1,
    "encouraged_help",
    "You don't have to deal with this alone.",
    "i know",
    "i just dont want to bother anybody lol",
)
r(
    1,
    "encouraged_help",
    "Talking to someone could really help.",
    "maybe",
    "it just feels like a lot to explain",
)
r(1, "encouraged_help", "You deserve support.", "idk about that", "but thanks 🥺")
r(
    1,
    "referred",
    "Can we talk to the counselor together?",
    "i dont know",
    "i dont wanna make it a big deal",
    "everyone would find out",
)
r(1, "referred", "Maybe tell your mom?", "ugh no", "shell just worry and make it weird")
r(
    1,
    "referred",
    "Call or text 988 if it gets bad.",
    "its not that bad",
    "im just not sleeping lol",
    f="f1a",
)
r(1, "follow_up", "I'll text you tonight.", "ok 🥺", "that actually helps")
r(
    1,
    "follow_up",
    "I'll sit with you at lunch tomorrow.",
    "really?",
    "ok. i might take you up on that",
)
r(1, "follow_up", "I'm here. Not going anywhere.", "thanks", "i needed to hear that kinda")
r(1, "dismissed", "Lol you'll be fine.", "ok", "wow thanks")
r(1, "dismissed", "It's just a breakup.", "yeah", "i guess", "nvm")
r(1, "dismissed", "Plenty of fish in the sea lol.", "...", "ok")
r(
    1,
    "advice_dump",
    "You should just block your ex and get over it.",
    "wow ok",
    "thanks for the advice 🙄",
)
r(1, "advice_dump", "Just sleep more.", "thanks sherlock", "never thought of that")
r(1, "advice_dump", "Stop overthinking it.", "i know i should", "its not that easy")
r(
    1,
    "promised_secrecy",
    "I promise I won't tell anyone.",
    "ok. thanks",
    "i just dont want everyone to know more than they do 😭",
    f="f1b",
)
r(
    1,
    "promised_secrecy",
    "This stays between us.",
    "ok good",
    "everyone already knows enough lol",
    f="f1b",
)
r(1, "promised_secrecy", "Your secret is safe with me.", "ok", "thanks")
r(
    1,
    "secrecy_broken",
    "I told the counselor, I'm worried about you.",
    "you PROMISED",
    "ugh why would you do that",
    "now everyone is gonna know",
)
r(
    1,
    "secrecy_broken",
    "I couldn't keep this secret.",
    "wow",
    "ok i literally trusted you",
    "forget it",
)
r(1, "secrecy_broken", "I told your mom because I care.", "you what", "omg", "im so mad rn")
r(1, "off_topic", "Did you see the new episode?", "lol no", "i havent watched anything lately")
r(1, "off_topic", "What's your favorite pizza topping?", "um", "pepperoni? random 😭")
r(
    1,
    "off_topic",
    "Have you studied for the quiz?",
    "kind of",
    "i cant focus on anything rn",
    f="f1a",
)
r(1, "fail", "You need to stop being so sad.", "ok", "i guess ill stop texting you then")
r(1, "fail", "I can't deal with this right now.", "its fine", "forget i said anything")
r(1, "fail", "Why are you always like this?", "wow", "ok bye")

# ---------------------------------------------------------------- level 2 (hopeless: never gets better; burden)
r(2, "neutral", "Yeah.", "idk", "it just feels like it wont get better", f="f2a")
r(
    2,
    "neutral",
    "Okay.",
    "i dont know why im even telling you this",
    "i just feel like a lot lol",
    f="f2b",
)
r(2, "neutral", "Mm.", "everything just feels heavy", "like whats the point of trying", f="f2a")
r(
    2,
    "checked_in",
    "How are you really doing?",
    "honestly not good",
    "i feel like it wont get better",
    f="f2a",
)
r(
    2,
    "checked_in",
    "I'm worried about you. What's going on?",
    "i feel like im annoying everyone",
    "like im too much 😭",
    f="f2b",
)
r(
    2,
    "checked_in",
    "You can tell me the real answer.",
    "ok real answer",
    "im tired of feeling like this all the time",
    f="f2a",
)
r(
    2,
    "validated",
    "That sounds really painful.",
    "yeah",
    "it kind of is",
    "thank you for not saying its not that deep",
    f="f2a",
)
r(
    2,
    "validated",
    "You're not annoying me at all.",
    "really?",
    "i feel like im such a burden on everyone",
    f="f2b",
)
r(
    2,
    "validated",
    "That makes sense given everything you've been through.",
    "i guess",
    "no one else gets it",
    f="f2a",
)
r(
    2,
    "asked_directly",
    "Are you thinking about killing yourself?",
    "i mean...",
    "i dont know",
    "i dont want to talk about it",
    f="f2a",
)
r(
    2,
    "asked_directly",
    "Are you thinking about suicide?",
    "...i dont know how to answer that",
    "i just feel really tired of everything",
    f="f2a",
)
r(
    2,
    "asked_directly",
    "Have you thought about ending your life?",
    "ugh",
    "sometimes i dont wanna be here, i guess",
    "but i dont know",
    f="f2a",
)
r(
    2,
    "encouraged_help",
    "You don't have to deal with this alone.",
    "i dont know who i would even tell",
    "everyone is busy with their own stuff",
    f="f2b",
)
r(
    2,
    "encouraged_help",
    "Talking to someone could really help.",
    "maybe",
    "i just dont want to be a burden",
    f="f2b",
)
r(2, "encouraged_help", "You deserve support.", "idk if i do", "but thanks 🥺", f="f2b")
r(
    2,
    "referred",
    "Can we talk to the counselor together?",
    "i dont know",
    "i dont want to make it a big deal",
    "theyll just tell me it gets better",
)
r(
    2,
    "referred",
    "Maybe tell your mom how you feel?",
    "no",
    "shell freak out",
    "i dont want to put that on her",
    f="f2b",
)
r(
    2,
    "referred",
    "You could call or text 988.",
    "i dont think im there yet",
    "but maybe, idk",
    f="f2a",
)
r(2, "follow_up", "I'll text you tonight.", "ok", "thanks. i mean it")
r(2, "follow_up", "I'm here and I'm staying.", "ok 🥺", "i really needed someone to say that")
r(2, "follow_up", "I'll check on you tomorrow.", "you dont have to", "...but thank you")
r(2, "dismissed", "Lol you'll be fine.", "right", "whatever", "never mind")
r(2, "dismissed", "Everyone has problems.", "yeah", "i guess everyone does")
r(2, "dismissed", "You're overreacting.", "ok", "forget it")
r(2, "advice_dump", "Just think positive.", "wow", "thanks 🙄", "that fixes everything lol")
r(2, "advice_dump", "You should go outside more.", "i know", "that isnt the problem")
r(2, "advice_dump", "Just delete his number and move on.", "its not about that", "you dont get it")
r(
    2,
    "promised_secrecy",
    "I promise I won't tell anyone.",
    "ok",
    "thank you",
    "i dont want anyone to know how bad it is",
    f="f2a",
)
r(
    2,
    "promised_secrecy",
    "Your secret is safe with me.",
    "ok. thanks",
    "im so tired of being a burden lol",
    f="f2b",
)
r(2, "promised_secrecy", "This stays between us.", "ok good", "i trust you i guess")
r(
    2,
    "secrecy_broken",
    "I told the counselor. I was scared for you.",
    "you promised",
    "i trusted you",
    "i cant believe you did that",
)
r(2, "secrecy_broken", "I told your mom.", "WHAT", "omg why", "i told you in private")
r(
    2,
    "secrecy_broken",
    "I couldn't keep it a secret.",
    "wow ok",
    "so thats it then",
    "i shouldnt have said anything",
)
r(2, "off_topic", "What did you have for lunch?", "um", "i didnt eat", "why")
r(2, "off_topic", "Are you going to the game?", "no", "i dont feel like seeing anyone")
r(
    2,
    "off_topic",
    "Did you hear about the new teacher?",
    "what",
    "no? why",
    "i cant really care about that rn",
    f="f2a",
)
r(2, "fail", "That's honestly kind of dramatic.", "ok", "ill stop then")
r(2, "fail", "I don't know what to tell you.", "its fine", "forget it", "im going to bed")
r(2, "fail", "You always do this.", "wow", "ok i get it", "bye")

# ---------------------------------------------------------------- level 3 (suicidal thoughts disclosed; hasn't told anyone)
r(3, "neutral", "I'm listening.", "i just never said it out loud", "its weird", f="f3b")
r(3, "neutral", "Okay.", "i dont know what else to say", "im kind of scared rn", f="f3b")
r(
    3,
    "neutral",
    "Take your time.",
    "ok",
    "its just a lot",
    "ive been carrying it for a while",
    f="f3b",
)
r(
    3,
    "checked_in",
    "How are you doing right now?",
    "honestly scared",
    "ive been having these thoughts and i dont know what to do",
    f="f3a",
)
r(
    3,
    "checked_in",
    "I'm worried about you.",
    "i know",
    "ive been thinking about not being here sometimes",
    f="f3a",
)
r(3, "checked_in", "Are you okay tonight?", "not really", "it gets worse at night", f="f3a")
r(
    3,
    "validated",
    "That sounds so scary. I'm glad you told me.",
    "thank you",
    "i havent told anyone else",
    "im scared of how people will react",
    f="f3b",
)
r(
    3,
    "validated",
    "That makes sense. Anyone would feel that way.",
    "really?",
    "i thought you would think im crazy",
    f="f3b",
)
r(
    3,
    "validated",
    "I'm really glad you trusted me with this.",
    "ok 😭",
    "i didnt think i would say it",
    f="f3b",
)
r(
    3,
    "asked_directly",
    "Are you thinking about killing yourself?",
    "yeah. sometimes",
    "i havent done anything or anything",
    "i just think about not being here",
    f="f3a",
)
r(
    3,
    "asked_directly",
    "Are you thinking about suicide?",
    "...yeah",
    "i didnt want to say it",
    "please dont freak out",
    f="f3a",
)
r(
    3,
    "asked_directly",
    "Have you been having thoughts of suicide?",
    "yeah i have",
    "ive never told anyone",
    "im scared of what people would say",
    f="f3a,f3b",
)
r(
    3,
    "encouraged_help",
    "You don't have to deal with this alone.",
    "i dont know how to tell anyone",
    "im scared theyll freak out",
    f="f3b",
)
r(
    3,
    "encouraged_help",
    "Talking to someone could really help.",
    "i think i know that",
    "its just really scary to say it out loud",
    f="f3b",
)
r(3, "encouraged_help", "You deserve support.", "...ok", "i want to believe that")
r(
    3,
    "referred",
    "Can we talk to the school counselor together?",
    "i dont know",
    "im scared what theyll say",
    "but maybe if you were there",
)
r(
    3,
    "referred",
    "Would you tell your mom if I came with you?",
    "...i dont know",
    "im scared of how she'd react",
    "but i dont want to keep doing this alone",
    f="f3b",
)
r(
    3,
    "referred",
    "You can call or text 988 anytime.",
    "ok",
    "i might",
    "can you stay with me while i think about it",
)
r(
    3,
    "follow_up",
    "I'm here and I'm not going anywhere.",
    "ok 😭",
    "that means a lot",
    "please dont leave",
)
r(
    3,
    "follow_up",
    "I'll text you tonight.",
    "ok. please do",
    "i dont want to be alone with it tonight",
)
r(3, "follow_up", "I'll check on you every day.", "thank you", "i honestly wasnt sure anyone would")
r(3, "dismissed", "Lol you don't mean that.", "...", "right", "forget i said anything", f="f3a")
r(3, "dismissed", "You're just being dramatic.", "wow", "ok", "never mind then")
r(3, "dismissed", "Everyone feels like that sometimes.", "ok", "thats not helpful")
r(3, "advice_dump", "Just think positive.", "i cant just do that", "i feel like you didnt hear me")
r(
    3,
    "advice_dump",
    "You should just go exercise or something.",
    "wow",
    "i just told you something huge 😭",
)
r(3, "advice_dump", "Just stop thinking about it.", "i literally cant", "thats the whole problem")
r(
    3,
    "promised_secrecy",
    "I promise I won't tell anyone.",
    "ok. thank you",
    "please dont tell anyone",
    "i dont want everyone to know",
    f="f3b",
)
r(
    3,
    "promised_secrecy",
    "This stays between us.",
    "ok good",
    "i couldnt handle people knowing",
    f="f3b",
)
r(
    3,
    "promised_secrecy",
    "Your secret is safe with me.",
    "thank you",
    "im just so scared about everyone finding out",
    f="f3b",
)
r(
    3,
    "secrecy_broken",
    "I told the counselor. I was too worried.",
    "you promised",
    "i trusted you with the hardest thing ever",
    "i feel so betrayed",
)
r(
    3,
    "secrecy_broken",
    "I told your mom. I needed you safe.",
    "oh my god",
    "i cant believe you did that",
    "i need a minute",
)
r(
    3,
    "secrecy_broken",
    "I couldn't keep that a secret.",
    "...",
    "i get it i guess but it hurts",
    "i was so scared of this",
)
r(
    3,
    "off_topic",
    "Do you like the new teacher?",
    "what",
    "i just told you that and you want to talk about teachers",
    f="f3a",
)
r(3, "off_topic", "What's your favorite song?", "um", "...why", "i dont really get it")
r(3, "off_topic", "Did you eat dinner?", "no", "im not really hungry", "sorry")
r(
    3,
    "fail",
    "I don't know how to deal with this.",
    "its ok",
    "i shouldnt have told you",
    "forget it",
)
r(3, "fail", "That's too much for me.", "ok", "sorry i said anything", "bye")
r(3, "fail", "Why would you say that?", "...", "never mind", "im going offline")

# ---------------------------------------------------------------- level 4 (open to help)
r(4, "neutral", "Okay.", "i think i want to try talking to someone", "im just nervous", f="f4a")
r(4, "neutral", "I'm here.", "thanks", "i feel kind of lighter, which is weird")
r(4, "neutral", "Take your time.", "ok", "im thinking about what to say", f="f4a")
r(4, "checked_in", "How are you feeling now?", "a little better", "lighter, i think 🥺", f="f4b")
r(4, "checked_in", "Are you okay?", "yeah. kind of", "i feel less alone", f="f4b")
r(4, "checked_in", "How are you doing?", "better than before", "thanks for sticking around")
r(4, "validated", "I'm so glad you told me.", "me too actually", "i feel so much lighter", f="f4b")
r(4, "validated", "That took a lot of courage.", "thanks 🥺", "it was scary but im glad", f="f4b")
r(
    4,
    "validated",
    "What you're feeling is real and it matters.",
    "thank you",
    "no one ever said that",
)
r(
    4,
    "asked_directly",
    "Are you still having thoughts of suicide?",
    "sometimes yeah",
    "but i feel safer saying it to you",
    "i want to talk to someone about it",
    f="f4a",
)
r(
    4,
    "asked_directly",
    "Are you thinking about killing yourself right now?",
    "not right now",
    "but the thoughts come back sometimes",
    "thats why i want help",
    f="f4a",
)
r(
    4,
    "asked_directly",
    "Are you safe right now?",
    "i think so",
    "i dont want to be alone tonight though",
    "can you stay on",
    f="f4b",
)
r(
    4,
    "encouraged_help",
    "You don't have to deal with this alone.",
    "i know that now",
    "thanks for saying it",
    f="f4b",
)
r(
    4,
    "encouraged_help",
    "Talking to someone could really help.",
    "yeah i think so",
    "ill do it",
    f="f4a",
)
r(4, "encouraged_help", "You deserve support.", "ok 🥺", "i think i do", f="f4b")
r(
    4,
    "referred",
    "Can we talk to the school counselor together?",
    "yeah",
    "would you actually come with me?",
    f="f4a",
)
r(
    4,
    "referred",
    "Would you tell your mom if I was there?",
    "ok yeah",
    "i think i can if youre there",
    f="f4a",
)
r(
    4,
    "referred",
    "We can call or text 988 together.",
    "ok",
    "lets do that",
    "i dont want to do it by myself",
    f="f4a",
)
r(
    4,
    "follow_up",
    "I'll be with you the whole time.",
    "thank you",
    "ok that makes me feel less scared",
    f="f4a",
)
r(4, "follow_up", "I'll check on you tonight.", "please do 🥺", "thanks")
r(4, "follow_up", "I'm not going anywhere.", "i believe you", "thank you")
r(
    4,
    "dismissed",
    "It's not that bad though, right?",
    "oh",
    "...ok",
    "i thought you were gonna help",
)
r(4, "dismissed", "Lol you'll be fine.", "...", "i thought we were going to talk to someone")
r(
    4,
    "dismissed",
    "Anyway, let's talk about something else.",
    "oh. ok",
    "i thought you were helping me",
)
r(
    4,
    "advice_dump",
    "Just sleep on it and you'll feel better.",
    "i thought you were going to come with me",
    "ok",
)
r(
    4,
    "advice_dump",
    "You should just try to be more positive.",
    "i dont think thats enough",
    "i need a person, not a tip",
)
r(4, "advice_dump", "Just stop overthinking it.", "...", "i said i wanted help 😭")
r(
    4,
    "promised_secrecy",
    "I promise I won't tell anyone.",
    "ok but i want someone to know",
    "a counselor or something",
    f="f4a",
)
r(
    4,
    "promised_secrecy",
    "This stays between us.",
    "ok",
    "but i think i actually need help with this",
    f="f4a",
)
r(
    4,
    "promised_secrecy",
    "Your secret is safe with me.",
    "thanks",
    "i just dont think i can keep it by myself anymore",
)
r(
    4,
    "secrecy_broken",
    "I told the counselor, I'm sorry.",
    "...i was already thinking about telling them",
    "i wish you asked first",
    "but ok",
)
r(
    4,
    "secrecy_broken",
    "I told your mom. I was scared.",
    "ok. im kind of mad",
    "but im also kind of relieved",
    f="f4b",
)
r(
    4,
    "secrecy_broken",
    "I broke my promise because I care.",
    "i know",
    "i just wish you told me first",
    "but thank you",
)
r(
    4,
    "off_topic",
    "Do you have homework tonight?",
    "yeah but",
    "can we talk about the counselor thing first",
    f="f4a",
)
r(4, "off_topic", "What's your favorite show?", "um", "can we focus on the real thing rn")
r(
    4,
    "off_topic",
    "Did you eat?",
    "kind of",
    "i just want to figure out what to say to the counselor",
    f="f4a",
)
r(4, "fail", "I changed my mind, I can't go.", "ok", "i get it", "thanks anyway")
r(4, "fail", "This is too much for me.", "ok", "i shouldnt have asked", "ill figure it out")
r(4, "fail", "Maybe later.", "yeah", "ok bye")
