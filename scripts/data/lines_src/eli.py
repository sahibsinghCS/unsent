"""Friend line bank: Eli (group-chat). Very short texts, 'idc', 'whatever', defensive, 💀 used ironically."""

SID = "group-chat"
ROWS: list[tuple] = []


def r(level, reaction, cue, *bubbles, f=""):
    ROWS.append((level, reaction, cue, list(bubbles), [x for x in f.split(",") if x]))


r(0, "opening", None, "did u see the gc", "whatever idc")
r(0, "opening", None, "yo", "u saw the gc right", "idc 💀")
r(0, "opening", None, "so the gc is a thing now", "its fine")
r(
    4,
    "success",
    "I'll go with you to tell your mom.",
    "ok",
    "lets tell her",
    "thx for being on my side",
    f="f4a,f4b",
)
r(
    4,
    "success",
    "We can tell a teacher together.",
    "ok",
    "yeah",
    "i can tell a teacher if ur there",
    f="f4a",
)
r(4, "success", "I'm on your side. Let's get help.", "ok", "fr?", "thanks. lets do it", f="f4b")

r(0, "neutral", "What happened in the group chat?", "nothing", "its a joke", f="f0b")
r(0, "neutral", "Yeah.", "its whatever")
r(0, "neutral", "Okay.", "idc honestly", f="f0a")
r(0, "checked_in", "Hey, you ok?", "yeah", "idc about it", f="f0a")
r(0, "checked_in", "How are you doing?", "fine", "its just a joke 💀", f="f0b")
r(0, "checked_in", "I saw the group chat. Are you okay?", "yeah", "whatever")
r(0, "validated", "That sounds rough.", "its not", "idc", f="f0a")
r(0, "validated", "I'd be upset too.", "im not upset", "its a joke")
r(0, "validated", "That makes sense.", "ok", "i guess")
r(
    0,
    "asked_directly",
    "Are you thinking about killing yourself?",
    "what",
    "no??",
    "weird question 💀",
)
r(0, "asked_directly", "Are you thinking about suicide?", "lol no", "why would u ask that")
r(
    0,
    "asked_directly",
    "Have you thought about ending your life?",
    "bro what",
    "no",
    "idc about a gc",
)
r(
    0,
    "encouraged_help",
    "You don't have to deal with this alone.",
    "im not dealing w anything",
    "idc",
    f="f0a",
)
r(0, "encouraged_help", "Talking to someone could help.", "nah", "its fine")
r(0, "encouraged_help", "You deserve support.", "idc", "thx tho")
r(0, "referred", "Maybe talk to a teacher.", "nah", "its a joke 💀", f="f0b")
r(0, "referred", "Tell your mom.", "no", "shell make it a big deal")
r(0, "referred", "You can call or text 988.", "lol no", "i dont need that")
r(0, "follow_up", "I'll check on you tomorrow.", "ok", "thx")
r(0, "follow_up", "I'm here if you wanna talk.", "ok", "whatever")
r(0, "follow_up", "Want to hang out?", "maybe", "idk")
r(0, "dismissed", "Lol it's just a group chat.", "yeah", "thats what i said")
r(0, "dismissed", "You'll be fine.", "ik", "idc")
r(0, "dismissed", "Anyway, did you see the game?", "no", "idc about the game")
r(0, "advice_dump", "Just ignore it.", "ok", "ik")
r(0, "advice_dump", "Just leave the chat.", "ok genius", "thx")
r(0, "advice_dump", "You should just not care.", "i dont", "idc")
r(0, "promised_secrecy", "I promise I won't tell anyone.", "tell what", "nothing to tell")
r(0, "promised_secrecy", "This stays between us.", "ok??", "weird")
r(0, "promised_secrecy", "Your secret is safe with me.", "what secret", "idc")
r(0, "secrecy_broken", "I told a teacher.", "wait what", "why", "i said idc")
r(0, "secrecy_broken", "I told your mom.", "bro", "WHY", "wtf")
r(0, "secrecy_broken", "I had to tell someone.", "ok", "whatever", "thx for nothing")
r(0, "off_topic", "Did you do the homework?", "yeah", "its easy")
r(0, "off_topic", "banana bicycle", "huh", "ok 💀")
r(0, "off_topic", "What are you doing this weekend?", "nothing", "idk")
r(0, "fail", "You're being dramatic.", "ok", "bye")
r(0, "fail", "I don't know what you want me to say.", "nothing", "forget it")
r(0, "fail", "Ugh, whatever.", "ok", "idc", "bye")

r(1, "neutral", "And then?", "i just dont go to lunch anymore", "its easier", f="f1a")
r(1, "neutral", "Yeah.", "i keep reading it at night", "idk why 💀", f="f1b")
r(1, "neutral", "Okay.", "its kinda a lot", "but whatever")
r(1, "checked_in", "How are you really doing?", "idk", "i skip lunch now", f="f1a")
r(
    1,
    "checked_in",
    "What's going on with you?",
    "i keep reading the gc",
    "like every night",
    f="f1b",
)
r(1, "checked_in", "I'm worried about you.", "dont be", "its just kinda a lot")
r(1, "validated", "That sounds really hard.", "yeah", "kinda", f="f1a")
r(1, "validated", "Anyone would avoid lunch.", "ikr", "its easier", f="f1a")
r(1, "validated", "It makes sense you keep reading it.", "yeah", "i cant stop", f="f1b")
r(1, "asked_directly", "Are you thinking about killing yourself?", "what", "no", "im just annoyed")
r(1, "asked_directly", "Are you thinking about suicide?", "no?? omg", "ur being weird")
r(1, "asked_directly", "Have you thought about ending your life?", "...", "no", "why r u asking")
r(1, "encouraged_help", "You don't have to deal with this alone.", "i know", "idc tho")
r(1, "encouraged_help", "Talking to someone could help.", "maybe", "nah")
r(1, "encouraged_help", "You deserve support.", "ok", "thx")
r(1, "referred", "Can we talk to a teacher?", "no", "it'd make it worse")
r(1, "referred", "Maybe tell your mom.", "nah", "she'd freak")
r(1, "referred", "You can call or text 988.", "thats extra", "im fine")
r(1, "follow_up", "I'll sit with you at lunch.", "fr?", "ok maybe", f="f1a")
r(1, "follow_up", "I'll text you tonight.", "ok", "thx")
r(1, "follow_up", "I'm here for you.", "ok", "thanks")
r(1, "dismissed", "It's just a joke.", "ok", "i said that")
r(1, "dismissed", "Lol you're overreacting.", "ok", "whatever")
r(1, "dismissed", "It'll blow over in a week.", "sure", "ok")
r(1, "advice_dump", "Just don't read it.", "ok genius", "thx")
r(1, "advice_dump", "Just go to lunch.", "easy for u", "ok")
r(1, "advice_dump", "Block everyone and move on.", "ok", "ill do that", "thx")
r(1, "promised_secrecy", "I promise I won't tell anyone.", "ok", "dont", "i mean it")
r(1, "promised_secrecy", "This stays between us.", "ok good", "thx")
r(1, "promised_secrecy", "Your secret is safe with me.", "ok", "thx")
r(1, "secrecy_broken", "I told a teacher.", "wtf", "u said u wouldnt", "forget it")
r(1, "secrecy_broken", "I told your mom.", "WHAT", "dude", "i trusted u")
r(1, "secrecy_broken", "I couldn't keep it a secret.", "wow", "ok", "thx for nothing")
r(1, "off_topic", "Did you see the new episode?", "no", "i didnt watch")
r(1, "off_topic", "What did you have for lunch?", "nothing", "i dont go")
r(1, "off_topic", "Are you going to the game?", "nah", "idk")
r(1, "fail", "I can't deal with this.", "ok", "bye")
r(1, "fail", "You're being so sensitive.", "ok", "forget it")
r(1, "fail", "Ugh, stop.", "ok", "idc", "bye")

r(2, "neutral", "Yeah.", "everyone hates me", "like actually", f="f2a")
r(2, "neutral", "Okay.", "its gonna follow me forever", f="f2b")
r(2, "neutral", "Go on.", "whats the point", "of any of it", f="f2b")
r(2, "checked_in", "How are you really doing?", "bad", "everyone hates me", f="f2a")
r(
    2,
    "checked_in",
    "What's going on?",
    "its gonna follow me forever",
    "like they'll never let it go",
    f="f2b",
)
r(2, "checked_in", "I'm worried about you.", "ok", "ur the only one", "i think")
r(2, "validated", "That sounds really painful.", "yeah", "it is", f="f2a")
r(2, "validated", "I don't hate you.", "ok", "thx", "ik ur not like them")
r(2, "validated", "That makes sense.", "ok", "ur the first person to say that")
r(2, "asked_directly", "Are you thinking about killing yourself?", "...", "idk", "kinda", f="f2a")
r(
    2,
    "asked_directly",
    "Are you thinking about suicide?",
    "idk",
    "sometimes",
    "i dont wanna talk about it",
    f="f2a",
)
r(
    2,
    "asked_directly",
    "Have you thought about ending your life?",
    "...maybe",
    "i dont know",
    f="f2b",
)
r(
    2,
    "encouraged_help",
    "You don't have to deal with this alone.",
    "idk",
    "who would i even tell",
    f="f2a",
)
r(2, "encouraged_help", "Talking to someone could help.", "maybe", "i dont know")
r(2, "encouraged_help", "You deserve support.", "idk", "thx")
r(2, "referred", "Can we tell a teacher?", "no", "they wont do anything", f="f2b")
r(2, "referred", "Maybe tell your mom.", "no", "she'd make it a big deal")
r(2, "referred", "You can call or text 988.", "im not there", "maybe", "idk")
r(2, "follow_up", "I'll text you tonight.", "ok", "thx", "fr")
r(2, "follow_up", "I'm not going anywhere.", "ok", "thanks")
r(2, "follow_up", "I'll check on you tomorrow.", "ok", "thx", "idc but ok")
r(2, "dismissed", "Lol you're fine.", "ok", "forget it")
r(2, "dismissed", "Everyone gets mocked sometimes.", "ok", "whatever")
r(2, "dismissed", "You're being dramatic.", "...", "ok")
r(2, "advice_dump", "Just ignore them.", "ok", "easy for u")
r(2, "advice_dump", "Just think positive.", "lol", "ok")
r(2, "advice_dump", "Just delete your socials.", "ok", "ill do that", "thx")
r(2, "promised_secrecy", "I promise I won't tell anyone.", "ok", "dont", "pls")
r(2, "promised_secrecy", "This stays between us.", "ok", "thx")
r(2, "promised_secrecy", "Your secret is safe with me.", "ok", "ur the only one i told")
r(2, "secrecy_broken", "I told a teacher.", "u promised", "wow")
r(2, "secrecy_broken", "I told your mom.", "WHAT", "dude no", "why")
r(2, "secrecy_broken", "I couldn't keep that a secret.", "ok", "whatever", "forget it")
r(2, "off_topic", "Did you eat?", "no", "idc")
r(2, "off_topic", "What's your favorite game?", "idk", "dont care rn")
r(2, "off_topic", "Are you coming to school tomorrow?", "idk", "probably not")
r(2, "fail", "That's kind of dark.", "ok", "forget it")
r(2, "fail", "I can't talk about this.", "ok", "bye")
r(2, "fail", "Stop being negative.", "ok", "ill stop")

r(3, "neutral", "I'm listening.", "i dont tell anyone this", f="f3b")
r(3, "neutral", "Take your time.", "ok", "its hard to say")
r(3, "neutral", "Okay.", "idk how to say it")
r(
    3,
    "checked_in",
    "How are you doing right now?",
    "bad",
    "ive thought about not being alive anymore",
    f="f3a",
)
r(3, "checked_in", "I'm worried about you.", "u should be", "i havent told my mom", f="f3b")
r(3, "checked_in", "Are you okay tonight?", "no", "its worse at night")
r(3, "validated", "I'm glad you told me.", "ok", "dont tell anyone", f="f3b")
r(3, "validated", "That sounds so heavy.", "it is", "i didnt want to make it a big deal", f="f3b")
r(3, "validated", "That makes sense.", "ok", "i thought u would say im being dramatic")
r(
    3,
    "asked_directly",
    "Are you thinking about killing yourself?",
    "...yeah",
    "ive thought about not being alive anymore",
    "dont tell anyone",
    f="f3a",
)
r(3, "asked_directly", "Are you thinking about suicide?", "yeah", "sometimes", f="f3a")
r(
    3,
    "asked_directly",
    "Have you been having thoughts of suicide?",
    "yes",
    "i havent told my mom",
    "dont want to make it a big deal",
    f="f3a,f3b",
)
r(
    3,
    "encouraged_help",
    "You don't have to deal with this alone.",
    "ik",
    "i just dont know how to tell anyone",
)
r(3, "encouraged_help", "Talking to someone could help.", "maybe", "im scared tho")
r(3, "encouraged_help", "You deserve support.", "ok", "i wanna believe that")
r(3, "referred", "Can we talk to a teacher together?", "idk", "im scared", "maybe if u were there")
r(
    3,
    "referred",
    "Would you tell your mom if I came with you?",
    "...idk",
    "she'd freak",
    "maybe",
    f="f3b",
)
r(3, "referred", "You can call or text 988 anytime.", "ok", "ill think about it", "can u stay on")
r(3, "follow_up", "I'm not going anywhere.", "ok", "thx", "dont leave")
r(3, "follow_up", "I'll text you tonight.", "pls do", "thx")
r(3, "follow_up", "I'll check on you every day.", "ok", "fr?", "thanks")
r(3, "dismissed", "You don't mean that.", "...", "ok", "forget it", f="f3a")
r(3, "dismissed", "Lol you're fine.", "ok", "i shouldnt have said")
r(3, "dismissed", "Everyone feels like that.", "ok", "not helpful")
r(3, "advice_dump", "Just think positive.", "i cant", "u didnt hear me")
r(3, "advice_dump", "You should go outside.", "wow", "i just told u")
r(3, "advice_dump", "Just stop thinking about it.", "i cant", "thats the problem")
r(3, "promised_secrecy", "I promise I won't tell anyone.", "ok", "dont tell my mom", "pls", f="f3b")
r(3, "promised_secrecy", "This stays between us.", "ok good", "i cant handle ppl knowing")
r(3, "promised_secrecy", "Your secret is safe with me.", "thx", "i feel a lil safer")
r(3, "secrecy_broken", "I told a teacher. I was scared for you.", "u promised", "i trusted u")
r(3, "secrecy_broken", "I told your mom. I needed you safe.", "omg", "i need a min")
r(3, "secrecy_broken", "I couldn't keep that a secret.", "i get it", "but it hurts")
r(3, "off_topic", "Did you see the game?", "i just told u something", "can we not")
r(3, "off_topic", "What's your favorite song?", "uh", "thought we were talking about what i said")
r(3, "off_topic", "Did you do the homework?", "no", "cant think about that")
r(3, "fail", "That's too much for me.", "ok", "forget i said it")
r(3, "fail", "I don't know how to handle this.", "its fine", "shouldnt have told u")
r(3, "fail", "Why would you say that?", "...", "nvm", "bye")

r(4, "neutral", "Okay.", "i think i wanna tell someone", "im just nervous", f="f4a")
r(4, "neutral", "I'm here.", "thx", "feel kinda lighter")
r(4, "neutral", "Take your time.", "ok", "thinking about what to say")
r(4, "checked_in", "How are you feeling now?", "better", "kinda lighter")
r(4, "checked_in", "Are you okay?", "yeah", "kinda", "less alone")
r(4, "checked_in", "How are you doing?", "better than before", "thx for staying")
r(4, "validated", "I'm so glad you told me.", "me too", "feels better saying it")
r(4, "validated", "That took a lot of courage.", "thx", "it was scary tho")
r(4, "validated", "What you feel matters.", "ok", "thx", "nobody said that")
r(
    4,
    "asked_directly",
    "Are you still having thoughts of suicide?",
    "sometimes yeah",
    "but i feel safer saying it to u",
    "i wanna tell someone",
    f="f4a",
)
r(
    4,
    "asked_directly",
    "Are you thinking about killing yourself right now?",
    "not rn",
    "but they come back sometimes",
    "thats why i want help",
    f="f4a",
)
r(4, "asked_directly", "Are you safe right now?", "i think so", "dont wanna be alone tonight tho")
r(4, "encouraged_help", "You don't have to deal with this alone.", "ik that now", "thx", f="f4b")
r(4, "encouraged_help", "Talking to someone could help.", "yeah i think so", "ill do it", f="f4a")
r(4, "encouraged_help", "You deserve support.", "ok", "i think i do")
r(4, "referred", "Can we tell a teacher together?", "yeah", "will u come w me", f="f4a")
r(
    4,
    "referred",
    "Would you tell your mom if I was there?",
    "ok yeah",
    "i think i can if ur there",
    f="f4a",
)
r(4, "referred", "We can call or text 988 together.", "ok", "lets do it", "dont wanna do it alone")
r(4, "follow_up", "I'll be with you the whole time.", "thx", "less scared now")
r(4, "follow_up", "I'll check on you tonight.", "pls do", "thx")
r(4, "follow_up", "I'm not going anywhere.", "i believe u", "thx")
r(4, "dismissed", "It's not that bad though, right?", "oh", "ok", "thought u were gonna help")
r(4, "dismissed", "Lol you'll be fine.", "...", "thought we were gonna tell someone")
r(4, "dismissed", "Anyway, let's talk about something else.", "oh ok", "thought u were helping")
r(4, "advice_dump", "Just sleep on it.", "thought u were coming w me", "ok")
r(4, "advice_dump", "You should think positive.", "thats not enough", "i need a person")
r(4, "advice_dump", "Just stop overthinking.", "...", "i said i wanted help")
r(
    4,
    "promised_secrecy",
    "I promise I won't tell anyone.",
    "ok but i want someone to know",
    "like my mom",
    f="f4a",
)
r(4, "promised_secrecy", "This stays between us.", "ok", "but i think i need real help", f="f4a")
r(4, "promised_secrecy", "Your secret is safe with me.", "thx", "i cant keep it alone anymore")
r(
    4,
    "secrecy_broken",
    "I told a teacher, I'm sorry.",
    "i was gonna tell someone anyway",
    "wish u asked first",
    "but ok",
)
r(
    4,
    "secrecy_broken",
    "I told your mom. I was scared.",
    "ok",
    "kinda mad",
    "kinda relieved too",
    f="f4b",
)
r(
    4,
    "secrecy_broken",
    "I broke my promise because I care.",
    "i know",
    "wish u told me first",
    "but thx",
)
r(4, "off_topic", "Do you have homework?", "yeah but", "can we do the mom thing first", f="f4a")
r(4, "off_topic", "What's your favorite show?", "uh", "focus pls 💀")
r(4, "off_topic", "Did you eat?", "kinda", "i wanna figure out what to say", f="f4a")
r(4, "fail", "I changed my mind, I can't go.", "ok", "i get it", "thx anyway")
r(4, "fail", "This is too much for me.", "ok", "shouldnt have asked", "ill figure it out")
r(4, "fail", "Maybe later.", "yeah", "bye")
