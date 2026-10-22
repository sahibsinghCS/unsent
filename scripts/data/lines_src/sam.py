"""Friend line bank: Sam (giving-stuff-away). Calm, a little too upbeat, says 'all good' a lot, deflects with jokes, opens up when asked directly."""

SID = "giving-stuff-away"
ROWS: list[tuple] = []


def r(level, reaction, cue, *bubbles, f=""):
    ROWS.append((level, reaction, cue, list(bubbles), [x for x in f.split(",") if x]))


r(0, "opening", None, "yo", "did u like the hoodie lol")
r(0, "opening", None, "hey hey", "hope the hoodie fits haha. all good over here")
r(0, "opening", None, "sup", "lol u texted me first. all good?")
r(
    4,
    "success",
    "I'll go with you to the counselor today.",
    "ok. yeah",
    "lets go today. thank you for coming with me",
    f="f4a",
)
r(
    4,
    "success",
    "We can call or text 988 together right now.",
    "ok. lets do it",
    "i dont think i can do it by myself but with you i can",
    f="f4b",
)
r(
    4,
    "success",
    "I'm so glad you told me. You matter to me.",
    "thank you for noticing",
    "i feel lighter. lets go see the counselor, then 988 if we need it",
    f="f4a,f4b",
)

r(0, "neutral", "What's been going on?", "nothing much haha. all good", f="f0a")
r(0, "neutral", "Yeah.", "just chilling lol. life is good")
r(0, "neutral", "Okay.", "lol u sound like ur at a doctors office", "all good i promise", f="f0a")
r(0, "checked_in", "Hey, you ok?", "all good lol", "why, do i seem not ok?", f="f0a")
r(0, "checked_in", "How are you doing?", "great. never better. i even cleaned my room haha")
r(0, "checked_in", "You seemed off at school.", "lol i was just tired", "all good tho", f="f0a")
r(0, "validated", "That sounds like a lot.", "haha it really isnt", "im good, honestly", f="f0a")
r(0, "validated", "It makes sense to feel that way.", "feel what way lol", "im chill")
r(0, "validated", "I'm glad you told me.", "told u what haha", "u r being so serious rn")
r(
    0,
    "asked_directly",
    "Are you thinking about killing yourself?",
    "lol what",
    "no?? why would u ask that haha",
    "i just didnt need the stuff",
    f="f0b",
)
r(
    0,
    "asked_directly",
    "Are you thinking about suicide?",
    "haha what? no",
    "u r being so dramatic lol",
    "all good",
    f="f0a",
)
r(
    0,
    "asked_directly",
    "Have you thought about ending your life?",
    "wait what? no. lol",
    "i just gave away a hoodie haha",
    f="f0b",
)
r(
    0,
    "encouraged_help",
    "You don't have to deal with this alone.",
    "deal with what haha",
    "im good, i promise",
    f="f0a",
)
r(
    0,
    "encouraged_help",
    "Talking to someone could really help.",
    "lol i dont need a therapist for giving away a hoodie",
    f="f0b",
)
r(0, "encouraged_help", "You deserve support.", "aw thanks haha", "im all good tho")
r(
    0,
    "referred",
    "Maybe talk to the counselor.",
    "lol for what",
    "i just didnt need the stuff",
    f="f0b",
)
r(0, "referred", "Can we tell your parents?", "tell them what haha", "im fine, its fine")
r(
    0,
    "referred",
    "You can call or text 988.",
    "lol thats a little extra",
    "im ok i promise",
    f="f0a",
)
r(0, "follow_up", "I'll text you tomorrow.", "sure haha", "thanks")
r(0, "follow_up", "I'm here if you want to talk.", "aw ok", "thanks, but im all good", f="f0a")
r(0, "follow_up", "Want to hang out this weekend?", "yeah maybe!", "sounds fun")
r(0, "dismissed", "Lol you'll be fine.", "haha yeah", "i know")
r(0, "dismissed", "It's just a hoodie.", "right?? thats what i said lol")
r(0, "dismissed", "Anyway, did you see the game?", "lol no", "i was busy")
r(0, "advice_dump", "Just keep your stuff next time.", "haha ok mom", "noted")
r(0, "advice_dump", "You should just talk to people more.", "lol ok", "thanks for the tip")
r(
    0,
    "advice_dump",
    "Have you tried being more positive?",
    "haha i am the most positive person i know",
    f="f0a",
)
r(
    0,
    "promised_secrecy",
    "I promise I won't tell anyone.",
    "tell anyone what lol",
    "theres nothing to tell haha",
)
r(0, "promised_secrecy", "This stays between us.", "ok?? lol", "u r being weird haha")
r(0, "promised_secrecy", "Your secret is safe with me.", "what secret haha", "all good")
r(
    0,
    "secrecy_broken",
    "I told the counselor, I'm worried.",
    "wait what",
    "why would u do that",
    "i literally said im fine haha... ok not funny",
)
r(0, "secrecy_broken", "I told your parents.", "u did what", "ok that's not cool", "i said im good")
r(0, "secrecy_broken", "I had to tell someone.", "ok...", "i didnt ask u to do that")
r(0, "off_topic", "Did you finish the homework?", "haha yeah", "its so easy lol")
r(0, "off_topic", "banana bicycle", "lol what", "ok random")
r(0, "off_topic", "What are you doing this weekend?", "not much haha", "cleaning my room i guess")
r(0, "fail", "You're being weird.", "haha ok", "ill talk to u later")
r(0, "fail", "I don't know what you want from me.", "nothing lol", "all good", "bye")
r(0, "fail", "Ugh, whatever.", "ok haha", "see u")

r(1, "neutral", "And then?", "idk, home has been kinda tense", "but its fine haha", f="f1a")
r(1, "neutral", "Yeah.", "i just feel kinda numb lately lol", "its whatever", f="f1b")
r(
    1,
    "neutral",
    "Okay.",
    "my parents are fighting a lot",
    "so i mostly just stay in my room. its chill",
    f="f1a",
)
r(
    1,
    "checked_in",
    "How are you really doing?",
    "honestly? kinda numb lately",
    "but all good haha",
    f="f1b",
)
r(
    1,
    "checked_in",
    "Is something going on at home?",
    "lol how did u know",
    "its been kinda tense. its fine",
    f="f1a",
)
r(
    1,
    "checked_in",
    "I'm worried about you.",
    "aw. thanks",
    "ive just been feeling numb for a few weeks. no big deal",
    f="f1b",
)
r(1, "validated", "That sounds really hard.", "haha yeah kinda", "thanks for saying that", f="f1a")
r(1, "validated", "It makes sense you'd feel numb.", "right?? i thought i was weird", f="f1b")
r(1, "validated", "I'm glad you told me.", "yeah me too haha", "it feels weird to say it")
r(
    1,
    "asked_directly",
    "Are you thinking about killing yourself?",
    "haha what? no",
    "i mean i feel kinda numb but not like that lol",
    f="f1b",
)
r(
    1,
    "asked_directly",
    "Are you thinking about suicide?",
    "no?? i dont think so",
    "ive just been tired and numb",
    f="f1b",
)
r(
    1,
    "asked_directly",
    "Have you thought about ending your life?",
    "...no",
    "why would u ask that haha",
    "ok i dont know",
)
r(
    1,
    "encouraged_help",
    "You don't have to deal with this alone.",
    "haha i know",
    "its not that big of a deal",
)
r(
    1,
    "encouraged_help",
    "Talking to someone could really help.",
    "maybe",
    "i just dont wanna make a thing out of it",
)
r(1, "encouraged_help", "You deserve support.", "aw thanks haha", "i guess")
r(
    1,
    "referred",
    "Can we talk to the counselor?",
    "lol i dont think i need that",
    "home stuff is just tense, thats all",
    f="f1a",
)
r(1, "referred", "Maybe tell your parents?", "haha they are the problem rn", "no thanks", f="f1a")
r(
    1,
    "referred",
    "You can call or text 988.",
    "thats for people in crisis, not for being tired haha",
)
r(1, "follow_up", "I'll text you tonight.", "ok haha", "that would be nice actually")
r(1, "follow_up", "I'll check on you tomorrow.", "ok", "thanks")
r(1, "follow_up", "I'm here if you need me.", "aw thanks", "same")
r(1, "dismissed", "Lol you'll be fine.", "yeah haha", "of course")
r(1, "dismissed", "Everyone's parents fight.", "right", "yeah haha", "ok")
r(1, "dismissed", "Numb? That's not a thing.", "lol ok", "never mind")
r(
    1,
    "advice_dump",
    "Just talk to your parents about it.",
    "haha ok",
    "thats so easy, why didnt i think of that",
)
r(1, "advice_dump", "You should go outside more.", "lol ok doc")
r(1, "advice_dump", "Just think positive.", "haha yeah", "thanks for the tip")
r(
    1,
    "promised_secrecy",
    "I promise I won't tell anyone.",
    "ok good",
    "i dont want my parents to know it's this bad",
    f="f1a",
)
r(1, "promised_secrecy", "This stays between us.", "ok haha thx", "all good then")
r(1, "promised_secrecy", "Your secret is safe with me.", "ok. thanks", "i trust u")
r(
    1,
    "secrecy_broken",
    "I told the counselor.",
    "u said u wouldnt",
    "wow ok",
    "that's kinda messed up",
)
r(1, "secrecy_broken", "I told your parents.", "WHAT", "u cant just do that", "i trusted u")
r(1, "secrecy_broken", "I couldn't keep it a secret.", "lol ok", "thats fine", "i guess")
r(1, "off_topic", "Did you see the new game trailer?", "haha not yet", "send it")
r(1, "off_topic", "What did you have for lunch?", "lol i skipped it", "wasnt hungry")
r(
    1,
    "off_topic",
    "Are you going to the game?",
    "probably not haha",
    "i dont feel like it lately",
    f="f1b",
)
r(1, "fail", "You always say you're fine.", "because i am", "ok bye haha")
r(1, "fail", "I don't know how to help.", "its all good", "dont worry about it")
r(1, "fail", "Stop being weird.", "ok sorry haha", "ill stop texting")

r(
    2,
    "neutral",
    "Yeah.",
    "i dunno, sometimes i think everyone would be better off without me",
    "haha ignore that",
    f="f2a",
)
r(2, "neutral", "Okay.", "i just dont see anything changing, ever", "but all good", f="f2b")
r(
    2,
    "neutral",
    "Go on.",
    "idk. its like i am already invisible",
    "and it wouldnt really change anything if i wasnt around",
    f="f2a",
)
r(
    2,
    "checked_in",
    "How are you really doing?",
    "honestly not great",
    "i dont see things changing",
    f="f2b",
)
r(
    2,
    "checked_in",
    "What's going on with you?",
    "i feel like everyone would be better off without me",
    "haha sorry that got dark",
    f="f2a",
)
r(2, "checked_in", "I'm worried about you.", "i know. sorry", "i just feel kinda stuck", f="f2b")
r(
    2,
    "validated",
    "That sounds really painful.",
    "yeah. it kind of is",
    "thanks for not laughing",
    f="f2b",
)
r(2, "validated", "I'm glad you told me.", "me too, i think", "it was kinda hard to say", f="f2a")
r(2, "validated", "That makes sense.", "yeah?", "i thought i was just being dramatic")
r(
    2,
    "asked_directly",
    "Are you thinking about killing yourself?",
    "...",
    "i dont know",
    "sometimes i think about it i guess",
    f="f2a",
)
r(
    2,
    "asked_directly",
    "Are you thinking about suicide?",
    "haha... i mean",
    "not like a plan or anything",
    "i dont know how to answer that",
    f="f2a",
)
r(
    2,
    "asked_directly",
    "Have you thought about ending your life?",
    "yeah. i think i have, a little",
    "but its not like i would do anything",
    f="f2a",
)
r(
    2,
    "encouraged_help",
    "You don't have to deal with this alone.",
    "i dont know who i would tell",
    "everyone thinks im fine",
    f="f2a",
)
r(
    2,
    "encouraged_help",
    "Talking to someone could really help.",
    "maybe",
    "its hard to say it out loud",
)
r(2, "encouraged_help", "You deserve support.", "idk about that haha", "but thanks")
r(
    2,
    "referred",
    "Can we talk to the counselor together?",
    "i dont know",
    "what would i even say",
    "that i feel invisible?",
)
r(
    2,
    "referred",
    "Maybe tell your parents.",
    "lol they are fighting",
    "they have enough going on",
    f="f1a",
)
r(
    2,
    "referred",
    "You could call or text 988.",
    "i dont think im there",
    "but maybe",
    "thanks for saying it",
)
r(2, "follow_up", "I'll text you tonight.", "ok", "that actually helps")
r(2, "follow_up", "I'm not going anywhere.", "ok haha", "good. thanks")
r(2, "follow_up", "I'll check on you tomorrow.", "you dont have to", "...but thanks")
r(2, "dismissed", "Lol you'll be fine.", "haha yeah", "of course", "forget i said anything")
r(2, "dismissed", "Everyone feels like that sometimes.", "right", "ok")
r(2, "dismissed", "You're being dramatic.", "haha yeah", "ignore me")
r(2, "advice_dump", "Just think positive.", "haha", "right", "that fixes everything")
r(2, "advice_dump", "You should join a club.", "lol ok", "ill add it to the list")
r(2, "advice_dump", "Just go outside.", "haha ok", "that isnt really the problem")
r(
    2,
    "promised_secrecy",
    "I promise I won't tell anyone.",
    "ok. thanks",
    "i dont want anyone to know how bad it is",
)
r(2, "promised_secrecy", "This stays between us.", "ok. good", "thank you")
r(2, "promised_secrecy", "Your secret is safe with me.", "ok. thanks haha", "i trust u")
r(2, "secrecy_broken", "I told the counselor.", "u promised", "i said that in confidence")
r(
    2,
    "secrecy_broken",
    "I told your parents.",
    "WHAT",
    "why would u do that",
    "this is going to make it worse",
)
r(
    2,
    "secrecy_broken",
    "I couldn't keep it a secret.",
    "wow ok",
    "good to know",
    "i wont tell u things anymore",
)
r(2, "off_topic", "Did you eat?", "lol yeah", "all good")
r(
    2,
    "off_topic",
    "What's your favorite show?",
    "uh haha",
    "idk. i havent really been watching anything",
)
r(2, "off_topic", "Did you see the game?", "no haha", "i dont care about that stuff lately")
r(2, "fail", "That's kind of dark.", "haha yeah", "sorry. forget it", "all good")
r(2, "fail", "I can't talk about this.", "its fine", "i get it", "bye")
r(2, "fail", "Stop being so negative.", "ok haha", "ill stop")

r(
    3,
    "neutral",
    "I'm listening.",
    "i didnt think anyone would notice",
    "so. i dont really know what to say",
    f="f3b",
)
r(3, "neutral", "Take your time.", "ok haha...", "this is hard to say")
r(3, "neutral", "Okay.", "i guess i just never said it out loud")
r(
    3,
    "checked_in",
    "How are you doing right now?",
    "honestly? scared",
    "ive been having thoughts of suicide",
    f="f3a",
)
r(
    3,
    "checked_in",
    "I'm worried about you.",
    "u should be, a little",
    "thats kinda why i gave my stuff away",
    f="f3b",
)
r(3, "checked_in", "Are you okay tonight?", "no. not really", "its bad at night")
r(
    3,
    "validated",
    "I'm really glad you told me.",
    "thank you",
    "i didnt think anyone would notice",
    f="f3b",
)
r(3, "validated", "That sounds so heavy.", "it is", "i didnt want to bother anyone")
r(3, "validated", "That makes sense.", "really?", "i thought you would think im weird")
r(
    3,
    "asked_directly",
    "Are you thinking about killing yourself?",
    "...yeah. i have",
    "thats kinda why i gave my stuff away",
    "i didnt think id need it",
    f="f3a,f3b",
)
r(
    3,
    "asked_directly",
    "Are you thinking about suicide?",
    "yeah",
    "i have been",
    "i didnt think anyone would notice",
    f="f3a",
)
r(
    3,
    "asked_directly",
    "Have you been having thoughts of suicide?",
    "yes. i have",
    "i didnt know how to say it",
    f="f3a",
)
r(
    3,
    "encouraged_help",
    "You don't have to deal with this alone.",
    "i know i should tell someone",
    "i just dont know how",
)
r(
    3,
    "encouraged_help",
    "Talking to someone could really help.",
    "i think ur right",
    "its scary though",
)
r(3, "encouraged_help", "You deserve support.", "thanks", "i want to believe that")
r(
    3,
    "referred",
    "Can we talk to the school counselor together?",
    "i think i could do that",
    "but im nervous",
    "will u stay with me?",
)
r(
    3,
    "referred",
    "Would you tell your parents if I came with you?",
    "i dont know. they are already so stressed",
    "but maybe",
)
r(
    3,
    "referred",
    "You can call or text 988 anytime.",
    "ok. i will think about it",
    "can u stay with me while i think?",
)
r(
    3,
    "follow_up",
    "I'm not going anywhere.",
    "thank you",
    "i dont want to be alone with this tonight",
)
r(3, "follow_up", "I'll text you tonight.", "please do", "that means a lot")
r(3, "follow_up", "I'll check on you every day.", "ok", "thank u. i honestly didnt expect that")
r(3, "dismissed", "You don't mean that.", "...", "ok", "forget i said it", f="f3a")
r(3, "dismissed", "Lol you're fine.", "haha yeah", "of course", "never mind")
r(3, "dismissed", "Everyone feels like that.", "ok", "thats not helpful")
r(3, "advice_dump", "Just think positive.", "i cant just do that", "i dont think u heard me")
r(
    3,
    "advice_dump",
    "You should go exercise or something.",
    "wow ok",
    "i just told u something huge",
)
r(
    3,
    "advice_dump",
    "Just stop thinking about it.",
    "i wish it was that easy",
    "thats the whole problem",
)
r(
    3,
    "promised_secrecy",
    "I promise I won't tell anyone.",
    "ok. thank u",
    "please dont tell my parents",
)
r(3, "promised_secrecy", "This stays between us.", "ok good", "i couldnt handle everyone knowing")
r(3, "promised_secrecy", "Your secret is safe with me.", "thank u", "i feel a little safer")
r(
    3,
    "secrecy_broken",
    "I told the counselor. I was too worried.",
    "u promised",
    "i trusted u with the hardest thing",
)
r(3, "secrecy_broken", "I told your parents. I needed you safe.", "oh my god", "i need a minute")
r(3, "secrecy_broken", "I couldn't keep that a secret.", "i get it i guess", "but it hurts")
r(
    3,
    "off_topic",
    "Did you see the game?",
    "i just told u something really hard",
    "can we not do the game rn",
)
r(3, "off_topic", "What's your favorite song?", "uh", "i thought we were talking about what i said")
r(3, "off_topic", "Did you do the reading?", "no. i cant think about that rn")
r(3, "fail", "That's too much for me.", "ok. sorry", "forget i said anything")
r(3, "fail", "I don't know how to handle this.", "its fine", "i shouldnt have told u")
r(3, "fail", "Why would you say that?", "...", "never mind", "bye")

r(4, "neutral", "Okay.", "i think i want to talk to someone", "im just nervous", f="f4a")
r(4, "neutral", "I'm here.", "thanks", "i feel lighter, which is weird")
r(4, "neutral", "Take your time.", "ok", "im trying to figure out what to say")
r(4, "checked_in", "How are you feeling now?", "better, honestly", "lighter than before", f="f4a")
r(4, "checked_in", "Are you okay?", "yeah. kind of", "less alone")
r(4, "checked_in", "How are you doing?", "better than i was. thanks for staying")
r(4, "validated", "I'm so glad you told me.", "me too actually", "it feels good to say it")
r(4, "validated", "That took a lot of courage.", "thanks haha", "it was scary but i'm glad")
r(4, "validated", "What you feel is real and it matters.", "thank u", "nobody said that before")
r(
    4,
    "asked_directly",
    "Are you still having thoughts of suicide?",
    "sometimes yeah",
    "but i feel safer saying it to u",
    "i want to talk to someone who can help",
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
    "i dont want to be alone tonight tho",
)
r(
    4,
    "encouraged_help",
    "You don't have to deal with this alone.",
    "i know that now",
    "thank u for saying it",
)
r(
    4,
    "encouraged_help",
    "Talking to someone could really help.",
    "yeah i think so",
    "i'll do it",
    f="f4a",
)
r(4, "encouraged_help", "You deserve support.", "ok", "i think i do")
r(4, "referred", "Can we go to the counselor together?", "yes", "can we go today?", f="f4a")
r(
    4,
    "referred",
    "Would you tell your parents if I was there?",
    "ok yeah",
    "i think i can if ur there",
)
r(
    4,
    "referred",
    "We can call or text 988 together.",
    "ok. lets do that",
    "i dont want to do it by myself",
    f="f4b",
)
r(4, "follow_up", "I'll be with you the whole time.", "thank you", "that makes me feel less scared")
r(4, "follow_up", "I'll check on you tonight.", "please do", "thanks")
r(4, "follow_up", "I'm not going anywhere.", "i believe u", "thank you")
r(4, "dismissed", "It's not that bad though, right?", "oh", "ok", "i thought u were gonna help")
r(4, "dismissed", "Lol you'll be fine.", "...", "i thought we were going to talk to someone")
r(
    4,
    "dismissed",
    "Anyway, let's talk about something else.",
    "oh. ok",
    "i thought u were helping me",
)
r(
    4,
    "advice_dump",
    "Just sleep on it and you'll feel better.",
    "i thought u were coming with me",
    "ok",
)
r(
    4,
    "advice_dump",
    "You should just try to be positive.",
    "thats not going to be enough",
    "i need a person, not a tip",
)
r(4, "advice_dump", "Just stop overthinking.", "...", "i said i wanted help")
r(
    4,
    "promised_secrecy",
    "I promise I won't tell anyone.",
    "ok but i want someone to know",
    "like a counselor",
    f="f4a",
)
r(
    4,
    "promised_secrecy",
    "This stays between us.",
    "ok",
    "but i think i need real help with this",
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
    "i was already thinking about telling them",
    "i wish u asked first",
    "but ok",
)
r(
    4,
    "secrecy_broken",
    "I told your parents. I was scared.",
    "ok. im kind of mad",
    "but also kind of relieved",
)
r(
    4,
    "secrecy_broken",
    "I broke my promise because I care.",
    "i know",
    "i just wish u told me first",
    "but thank u",
)
r(
    4,
    "off_topic",
    "Do you have homework?",
    "yeah but",
    "can we talk about the counselor thing first",
    f="f4a",
)
r(4, "off_topic", "What's your favorite show?", "haha", "can we focus on the real thing rn")
r(4, "off_topic", "Did you eat?", "kind of", "i just want to figure out what to say", f="f4a")
r(4, "fail", "I changed my mind, I can't go.", "ok", "i get it", "thanks anyway")
r(4, "fail", "This is too much for me.", "ok", "i shouldnt have asked", "ill figure it out")
r(4, "fail", "Maybe later.", "yeah", "ok. bye")
