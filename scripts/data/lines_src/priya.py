"""Friend line bank: Priya (new-school). Polite, short answers, lots of 'haha', avoids talking about herself, guarded at first."""

SID = "new-school"
ROWS: list[tuple] = []


def r(level, reaction, cue, *bubbles, f=""):
    ROWS.append((level, reaction, cue, list(bubbles), [x for x in f.split(",") if x]))


r(0, "opening", None, "hi haha", "thanks for texting me")
r(0, "opening", None, "oh hi!", "sorry i took a while to answer haha")
r(0, "opening", None, "hey haha", "thanks for checking on me. im good")
r(
    4,
    "success",
    "I'll go with you to the counselor.",
    "ok",
    "yes. thank you",
    "i think i can talk to the counselor if you come with me",
    f="f4a",
)
r(
    4,
    "success",
    "I'll sit with you at lunch, and we'll go together.",
    "ok haha... thank you",
    "i would really like to sit with someone at lunch",
    "and i can talk to the counselor",
    f="f4a,f4b",
)
r(
    4,
    "success",
    "I'm so glad you told me. You're not alone.",
    "thank you. really",
    "i feel lighter",
    "lets go to the counselor together",
    f="f4a",
)

r(0, "neutral", "How's school?", "its fine haha", "everyone is nice", f="f0b")
r(0, "neutral", "Yeah.", "haha yeah", "im adjusting", f="f0a")
r(0, "neutral", "Okay.", "thanks for asking haha", "how are you?")
r(0, "checked_in", "Hey, how are you doing?", "im good haha", "adjusting well", f="f0a")
r(0, "checked_in", "Are you ok?", "yes haha", "why? do i seem not ok?")
r(
    0,
    "checked_in",
    "How's the new school going?",
    "its nice! the school is really nice haha",
    f="f0b",
)
r(0, "validated", "That sounds like a lot.", "haha its not that bad", "im adjusting", f="f0a")
r(0, "validated", "Moving must be hard.", "its ok haha", "i like the school", f="f0b")
r(0, "validated", "I'm glad you told me.", "haha told you what", "im fine!")
r(
    0,
    "asked_directly",
    "Are you thinking about killing yourself?",
    "oh!",
    "no haha, why would you ask that?",
    "im fine, really",
)
r(
    0,
    "asked_directly",
    "Are you thinking about suicide?",
    "um no haha",
    "that is a really big question",
    "im just adjusting",
)
r(
    0,
    "asked_directly",
    "Have you thought about ending your life?",
    "what? no! haha",
    "i like the school",
    "why did you ask that?",
    f="f0b",
)
r(
    0,
    "encouraged_help",
    "You don't have to deal with this alone.",
    "oh thank you haha",
    "but im ok",
    f="f0a",
)
r(
    0,
    "encouraged_help",
    "Talking to someone could help.",
    "maybe haha",
    "i dont think i need it right now",
)
r(0, "encouraged_help", "You deserve support.", "aw thanks haha", "im good tho")
r(0, "referred", "Maybe talk to the counselor.", "haha im ok", "its just a new school", f="f0a")
r(0, "referred", "Tell your parents.", "oh no haha", "they have enough going on")
r(0, "referred", "You can call or text 988.", "oh. haha thats a lot", "im ok, thanks though")
r(0, "follow_up", "I'll check on you tomorrow.", "ok haha", "thank you")
r(0, "follow_up", "I'm here if you need me.", "aw thank you haha")
r(0, "follow_up", "Want to sit together at lunch?", "oh! maybe haha", "thank you for asking")
r(0, "dismissed", "Lol you'll be fine.", "haha yeah", "i know")
r(0, "dismissed", "It's just a new school.", "right haha", "thats true")
r(0, "dismissed", "Anyway, did you see the game?", "oh haha no", "i didnt")
r(0, "advice_dump", "You should just join a club.", "haha good idea", "thank you")
r(0, "advice_dump", "Just talk to people more.", "haha yeah", "i should", "thanks")
r(0, "advice_dump", "Have you tried being more outgoing?", "haha not really", "ill try")
r(0, "promised_secrecy", "I promise I won't tell anyone.", "haha tell anyone what", "im fine!")
r(0, "promised_secrecy", "This stays between us.", "um ok haha", "thank you?")
r(0, "promised_secrecy", "Your secret is safe with me.", "haha what secret", "im ok")
r(
    0,
    "secrecy_broken",
    "I told the counselor.",
    "oh",
    "why did you do that",
    "i said im fine haha... i mean it",
)
r(
    0,
    "secrecy_broken",
    "I told your parents.",
    "oh no",
    "why would you do that",
    "they have enough going on",
)
r(0, "secrecy_broken", "I had to tell someone.", "oh... ok", "i didnt ask you to")
r(0, "off_topic", "Did you finish the homework?", "haha yes", "it was easy")
r(0, "off_topic", "banana bicycle", "haha what?", "ok")
r(0, "off_topic", "What are you doing this weekend?", "not much haha", "homework probably")
r(0, "fail", "You're being awkward.", "oh haha ok", "sorry. i have to go")
r(0, "fail", "I don't know what you want me to say.", "its ok haha", "never mind", "bye")
r(0, "fail", "Ugh, whatever.", "oh ok haha", "bye")

r(1, "neutral", "And then?", "i mostly eat lunch by myself haha", "its not a big deal", f="f1a")
r(
    1,
    "neutral",
    "Yeah.",
    "my old friends kind of stopped texting back haha",
    "people get busy",
    f="f1b",
)
r(1, "neutral", "Okay.", "its been kind of lonely here haha", "but im ok")
r(1, "checked_in", "How are you really doing?", "um haha", "its kind of lonely sometimes", f="f1a")
r(
    1,
    "checked_in",
    "Is everything okay at school?",
    "i mostly eat lunch alone haha",
    "its not that bad",
    f="f1a",
)
r(
    1,
    "checked_in",
    "I'm worried about you.",
    "oh thats nice haha",
    "my old friends stopped texting, thats all",
    f="f1b",
)
r(1, "validated", "That sounds lonely.", "haha yeah", "kind of", f="f1a")
r(
    1,
    "validated",
    "That would hurt, your old friends not texting.",
    "haha yeah",
    "it does a little",
    f="f1b",
)
r(1, "validated", "I'm glad you told me.", "thank you haha", "its kind of nice to say it")
r(
    1,
    "asked_directly",
    "Are you thinking about killing yourself?",
    "oh haha no",
    "i mean i feel lonely but not like that",
)
r(
    1,
    "asked_directly",
    "Are you thinking about suicide?",
    "no haha...",
    "i dont think so",
    "im just a little lonely",
    f="f1a",
)
r(
    1,
    "asked_directly",
    "Have you thought about ending your life?",
    "...no",
    "why are you asking that haha",
    "im ok",
)
r(
    1,
    "encouraged_help",
    "You don't have to deal with this alone.",
    "haha thank you",
    "i dont want to bother anyone",
)
r(1, "encouraged_help", "Talking to someone could help.", "maybe haha", "i dont know who")
r(1, "encouraged_help", "You deserve support.", "aw haha thanks", "i guess")
r(1, "referred", "Can we talk to the counselor?", "haha i dont think i need that", "its just lunch")
r(1, "referred", "Maybe tell your parents.", "oh no haha", "theyre so stressed about the move")
r(
    1,
    "referred",
    "You can call or text 988.",
    "oh haha thats for people in crisis",
    "im just lonely",
)
r(1, "follow_up", "I'll text you tonight.", "ok haha", "that would be nice")
r(1, "follow_up", "Want to sit together at lunch?", "really? haha", "ok maybe", f="f1a")
r(1, "follow_up", "I'm here if you need me.", "thank you", "that means a lot")
r(1, "dismissed", "Lol you'll make friends.", "haha yeah", "of course")
r(1, "dismissed", "Everyone is lonely at a new school.", "right haha", "i know")
r(1, "dismissed", "It's not a big deal.", "haha yeah", "thats what i said")
r(1, "advice_dump", "You should join a club.", "haha ok", "good idea")
r(1, "advice_dump", "Just talk to people more.", "haha right", "i will try")
r(1, "advice_dump", "Be more outgoing.", "haha yeah", "ill work on it")
r(
    1,
    "promised_secrecy",
    "I promise I won't tell anyone.",
    "ok haha",
    "thank you",
    "i dont want my parents to worry",
)
r(1, "promised_secrecy", "This stays between us.", "ok good haha", "thank you")
r(1, "promised_secrecy", "Your secret is safe with me.", "thank you haha")
r(1, "secrecy_broken", "I told the counselor.", "oh", "you said you wouldnt", "ok")
r(
    1,
    "secrecy_broken",
    "I told your parents.",
    "oh no",
    "why would you do that",
    "they have enough to worry about",
)
r(1, "secrecy_broken", "I couldn't keep it a secret.", "oh ok", "its fine haha", "i guess")
r(1, "off_topic", "Did you see the new episode?", "haha no", "i havent been watching much")
r(1, "off_topic", "What did you have for lunch?", "oh haha", "just a sandwich. by myself", f="f1a")
r(1, "off_topic", "Are you going to the game?", "probably not haha", "i dont know anyone yet")
r(1, "fail", "You're so awkward.", "oh haha ok", "sorry. bye")
r(1, "fail", "I don't know how to help.", "its ok haha", "dont worry about it", "bye")
r(1, "fail", "Stop being weird.", "ok haha", "sorry", "ill stop")

r(2, "neutral", "Yeah.", "sometimes i feel invisible haha", "sorry, that was a lot", f="f2a")
r(2, "neutral", "Okay.", "i dont think it will get better here haha", "sorry", f="f2b")
r(2, "neutral", "Go on.", "its like no one would notice if i wasnt here", "haha sorry", f="f2a")
r(
    2,
    "checked_in",
    "How are you really doing?",
    "um honestly not great",
    "i feel kind of invisible",
    f="f2a",
)
r(
    2,
    "checked_in",
    "What's going on?",
    "i dont think its going to get better here",
    "sorry haha that was a lot",
    f="f2b",
)
r(
    2,
    "checked_in",
    "I'm worried about you.",
    "oh. thank you",
    "i didnt think anyone would notice haha",
    f="f2a",
)
r(2, "validated", "That sounds really painful.", "thank you", "it kind of is", f="f2a")
r(2, "validated", "I would notice if you weren't here.", "really? haha", "thank you", f="f2a")
r(2, "validated", "That makes sense.", "oh", "i thought i was being dramatic")
r(
    2,
    "asked_directly",
    "Are you thinking about killing yourself?",
    "...",
    "i dont know how to answer that",
    "sometimes i think about it",
    f="f2a",
)
r(
    2,
    "asked_directly",
    "Are you thinking about suicide?",
    "um...",
    "kind of. at night",
    "i dont want to talk about it haha",
    f="f2a",
)
r(
    2,
    "asked_directly",
    "Have you thought about ending your life?",
    "...maybe a little",
    "i dont know",
    "sorry",
    f="f2b",
)
r(
    2,
    "encouraged_help",
    "You don't have to deal with this alone.",
    "thank you haha",
    "i dont know who i would tell",
    f="f2a",
)
r(2, "encouraged_help", "Talking to someone could help.", "maybe", "its hard to say it out loud")
r(2, "encouraged_help", "You deserve support.", "oh. thank you", "i dont know if i do")
r(
    2,
    "referred",
    "Can we talk to the counselor together?",
    "i dont know haha",
    "what would i even say",
)
r(
    2,
    "referred",
    "Maybe tell your parents.",
    "oh no",
    "theyre so stressed about the move",
    "i dont want to add to it",
)
r(2, "referred", "You can call or text 988.", "i dont think im there", "but thank you")
r(2, "follow_up", "I'll text you tonight.", "ok haha", "thank you", "that helps")
r(2, "follow_up", "I'm not going anywhere.", "oh. ok", "thank you")
r(2, "follow_up", "I'll check on you tomorrow.", "you dont have to haha", "...but thank you")
r(2, "dismissed", "Lol you'll be fine.", "haha yeah", "forget i said anything")
r(2, "dismissed", "Everyone feels invisible sometimes.", "right haha", "ok")
r(2, "dismissed", "You're being dramatic.", "oh haha", "sorry")
r(2, "advice_dump", "Just think positive.", "haha ok", "ill try")
r(2, "advice_dump", "You should join a club.", "haha yes", "thats not really it")
r(2, "advice_dump", "Just talk to more people.", "haha ok", "thanks for the advice")
r(
    2,
    "promised_secrecy",
    "I promise I won't tell anyone.",
    "ok. thank you",
    "i dont want anyone to know how bad it is",
)
r(2, "promised_secrecy", "This stays between us.", "ok thank you", "haha")
r(2, "promised_secrecy", "Your secret is safe with me.", "thank you", "i trust you i think")
r(2, "secrecy_broken", "I told the counselor.", "you said you wouldnt", "i said it in confidence")
r(
    2,
    "secrecy_broken",
    "I told your parents.",
    "oh no",
    "why would you do that",
    "this makes it worse",
)
r(
    2,
    "secrecy_broken",
    "I couldn't keep it a secret.",
    "oh ok",
    "good to know",
    "i wont tell you things again",
)
r(2, "off_topic", "Did you eat?", "haha yes", "a little")
r(2, "off_topic", "What's your favorite show?", "oh haha", "i dont watch much lately")
r(2, "off_topic", "Did you see the game?", "no haha", "i dont really go to those")
r(2, "fail", "That's kind of dark.", "oh haha sorry", "forget it")
r(2, "fail", "I can't talk about this.", "its ok haha", "i understand", "bye")
r(2, "fail", "Stop being negative.", "ok haha", "sorry", "ill stop")

r(
    3,
    "neutral",
    "I'm listening.",
    "i havent told anyone this",
    "i dont want my parents to worry",
    f="f3b",
)
r(3, "neutral", "Take your time.", "ok haha", "this is hard to say")
r(3, "neutral", "Okay.", "i dont really know how to say it")
r(
    3,
    "checked_in",
    "How are you doing right now?",
    "honestly? scared",
    "ive had thoughts of suicide, mostly at night",
    f="f3a",
)
r(
    3,
    "checked_in",
    "I'm worried about you.",
    "you should be, a little",
    "i havent told my parents",
    f="f3b",
)
r(3, "checked_in", "Are you okay tonight?", "no. not really", "its worse at night", f="f3a")
r(
    3,
    "validated",
    "I'm really glad you told me.",
    "thank you",
    "please dont be weird about it haha",
    f="f3b",
)
r(3, "validated", "That sounds so heavy.", "it is", "i didnt want to worry anyone", f="f3b")
r(3, "validated", "That makes sense.", "really?", "i thought you would think im dramatic")
r(
    3,
    "asked_directly",
    "Are you thinking about killing yourself?",
    "...yeah",
    "at night mostly",
    "please dont be weird about it",
    f="f3a",
)
r(
    3,
    "asked_directly",
    "Are you thinking about suicide?",
    "yes. haha sorry",
    "i dont know why i laughed",
    "ive had thoughts like that",
    f="f3a",
)
r(
    3,
    "asked_directly",
    "Have you been having thoughts of suicide?",
    "yes. i have",
    "i havent told my parents",
    "theyre so stressed about the move",
    f="f3a,f3b",
)
r(
    3,
    "encouraged_help",
    "You don't have to deal with this alone.",
    "i know i should tell someone",
    "i just dont know how",
)
r(3, "encouraged_help", "Talking to someone could help.", "i think youre right", "its scary though")
r(3, "encouraged_help", "You deserve support.", "thank you", "i want to believe that")
r(
    3,
    "referred",
    "Can we talk to the school counselor together?",
    "i think i could do that",
    "but im nervous",
    "will you stay with me?",
)
r(
    3,
    "referred",
    "Would you tell your parents if I came with you?",
    "i dont know. theyre so stressed",
    "but maybe",
    f="f3b",
)
r(
    3,
    "referred",
    "You can call or text 988 anytime.",
    "ok. i will think about it",
    "can you stay with me while i think?",
)
r(
    3,
    "follow_up",
    "I'm not going anywhere.",
    "thank you",
    "i dont want to be alone with this tonight",
)
r(3, "follow_up", "I'll text you tonight.", "please do", "that means a lot")
r(3, "follow_up", "I'll check on you every day.", "oh. thank you", "i honestly didnt expect that")
r(3, "dismissed", "You don't mean that.", "...", "oh. ok", "forget i said it", f="f3a")
r(3, "dismissed", "Lol you're fine.", "haha yeah", "of course", "never mind")
r(3, "dismissed", "Everyone feels like that.", "oh. ok", "that wasnt helpful")
r(3, "advice_dump", "Just think positive.", "i cant just do that", "i dont think you heard me")
r(3, "advice_dump", "You should join a club.", "haha... ok", "i just told you something huge")
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
    "ok. thank you",
    "please dont tell my parents",
    f="f3b",
)
r(3, "promised_secrecy", "This stays between us.", "ok good", "i couldnt handle everyone knowing")
r(3, "promised_secrecy", "Your secret is safe with me.", "thank you", "i feel a little safer")
r(
    3,
    "secrecy_broken",
    "I told the counselor. I was too worried.",
    "you said you wouldnt",
    "i trusted you with the hardest thing",
)
r(3, "secrecy_broken", "I told your parents. I needed you safe.", "oh no", "i need a minute")
r(3, "secrecy_broken", "I couldn't keep that a secret.", "i get it i guess", "but it hurts")
r(
    3,
    "off_topic",
    "Did you see the game?",
    "i just told you something really hard",
    "can we not talk about the game",
)
r(
    3,
    "off_topic",
    "What's your favorite song?",
    "oh haha",
    "i thought we were talking about what i said",
)
r(3, "off_topic", "Did you do the reading?", "no", "i cant think about that right now")
r(3, "fail", "That's too much for me.", "oh. ok", "sorry", "forget i said anything")
r(3, "fail", "I don't know how to handle this.", "its ok", "i shouldnt have told you")
r(3, "fail", "Why would you say that?", "...", "never mind", "bye")

r(4, "neutral", "Okay.", "i think i want to talk to someone", "im just nervous haha", f="f4a")
r(4, "neutral", "I'm here.", "thank you", "i feel lighter, which is weird")
r(4, "neutral", "Take your time.", "ok", "im trying to figure out what to say")
r(4, "checked_in", "How are you feeling now?", "better honestly", "lighter than before")
r(4, "checked_in", "Are you okay?", "yes. kind of", "less alone")
r(4, "checked_in", "How are you doing?", "better than i was", "thank you for staying")
r(4, "validated", "I'm so glad you told me.", "me too actually", "it feels good to say it")
r(4, "validated", "That took a lot of courage.", "thank you haha", "it was scary but im glad")
r(4, "validated", "What you feel is real and it matters.", "thank you", "nobody said that before")
r(
    4,
    "asked_directly",
    "Are you still having thoughts of suicide?",
    "sometimes yes",
    "but i feel safer saying it to you",
    "i want to talk to someone who can help",
    f="f4a",
)
r(
    4,
    "asked_directly",
    "Are you thinking about killing yourself right now?",
    "not right now",
    "but the thoughts come back at night sometimes",
    "thats why i want help",
    f="f4a",
)
r(
    4,
    "asked_directly",
    "Are you safe right now?",
    "i think so",
    "i dont want to be alone tonight though",
)
r(
    4,
    "encouraged_help",
    "You don't have to deal with this alone.",
    "i know that now",
    "thank you for saying it",
)
r(4, "encouraged_help", "Talking to someone could help.", "yes i think so", "ill do it", f="f4a")
r(4, "encouraged_help", "You deserve support.", "ok", "i think i do")
r(
    4,
    "referred",
    "Can we talk to the counselor together?",
    "yes",
    "would you come with me?",
    f="f4a",
)
r(
    4,
    "referred",
    "Would you tell your parents if I was there?",
    "ok yes",
    "i think i can if you are there",
)
r(
    4,
    "referred",
    "We can call or text 988 together.",
    "ok. lets do that",
    "i dont want to do it by myself",
)
r(4, "follow_up", "I'll be with you the whole time.", "thank you", "that makes me feel less scared")
r(
    4,
    "follow_up",
    "Can I sit with you at lunch tomorrow?",
    "yes please haha",
    "i would really like that",
    f="f4b",
)
r(4, "follow_up", "I'm not going anywhere.", "i believe you", "thank you")
r(
    4,
    "dismissed",
    "It's not that bad though, right?",
    "oh",
    "ok",
    "i thought you were going to help",
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
    "i thought you were coming with me",
    "ok",
)
r(
    4,
    "advice_dump",
    "You should just join a club.",
    "that wont be enough",
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
    "thank you",
    "i just dont think i can keep it by myself anymore",
)
r(
    4,
    "secrecy_broken",
    "I told the counselor, I'm sorry.",
    "i was already thinking about telling them",
    "i wish you asked first",
    "but ok",
)
r(
    4,
    "secrecy_broken",
    "I told your parents. I was scared.",
    "ok. im kind of upset",
    "but also kind of relieved",
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
    "Do you have homework?",
    "yes but",
    "can we talk about the counselor first",
    f="f4a",
)
r(4, "off_topic", "What's your favorite show?", "haha", "can we focus on the real thing right now")
r(4, "off_topic", "Did you eat?", "kind of", "i just want to figure out what to say", f="f4a")
r(4, "fail", "I changed my mind, I can't go.", "ok", "i understand", "thanks anyway")
r(4, "fail", "This is too much for me.", "ok", "i shouldnt have asked", "ill figure it out")
r(4, "fail", "Maybe later.", "ok haha", "bye")
