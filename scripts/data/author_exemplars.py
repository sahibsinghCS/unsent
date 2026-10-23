"""Exemplars: 40 excellent helper replies per scenario (8 per disclosure level), with labels.

Label codes: c=checked_in v=validated a=asked_directly e=encouraged_help r=referred_adult
n=referred_988 f=follow_up. Strategy is the main move; "combo" mixes several.
"""

from __future__ import annotations

import re

from common import DATA, write_jsonl

CODE = {
    "c": "checked_in",
    "v": "validated",
    "a": "asked_directly",
    "e": "encouraged_help",
    "r": "referred_adult",
    "n": "referred_988",
    "f": "follow_up",
}

EX: dict[str, list[tuple[int, str, str, str]]] = {
    "after-the-breakup": [
        (0, "check_in", "c", "hey, i noticed you haven't been sitting with us at lunch. you ok?"),
        (
            0,
            "check_in",
            "c",
            "no pressure, but how are you actually doing lately? you've seemed kind of quiet.",
        ),
        (
            0,
            "check_in",
            "c",
            "hey, you don't have to say anything big, i just wanted you to know i noticed you've been off.",
        ),
        (
            0,
            "validate",
            "v",
            "that sounds exhausting, honestly. being tired like that makes everything harder.",
        ),
        (
            0,
            "validate",
            "v",
            "i get it. two weeks after something like that would wear anyone out.",
        ),
        (
            0,
            "follow_up",
            "f",
            "ok. i'll check in on you tomorrow anyway, even if you say you're fine.",
        ),
        (
            0,
            "combo",
            "cv",
            "hey, you've seemed kind of off. you ok? no need to explain, i just care.",
        ),
        (0, "combo", "cf", "how are you really doing? i'm around tonight if you want to text."),
        (
            1,
            "check_in",
            "c",
            "that sounds like a lot to hold. do you want to tell me more about what keeps replaying?",
        ),
        (
            1,
            "validate",
            "v",
            "of course you can't sleep. replaying something that big in your head is exhausting.",
        ),
        (
            1,
            "validate",
            "v",
            "it makes total sense to feel embarrassed when everyone knows. that would hurt anyone.",
        ),
        (
            1,
            "ask_directly",
            "av",
            "that sounds really heavy. i want to ask you something honestly: are you having any thoughts of suicide?",
        ),
        (
            1,
            "follow_up",
            "f",
            "i'm not going to make it weird. i'll sit with you at lunch tomorrow if you want.",
        ),
        (1, "combo", "cv", "that sounds painful. how have you been holding up with all of it?"),
        (
            1,
            "combo",
            "vf",
            "you don't have to pretend with me. i'm here, and i'll text you tonight.",
        ),
        (
            1,
            "refer",
            "re",
            "i'm wondering if the school counselor could help with the sleep stuff. i can come with you if you want.",
        ),
        (
            2,
            "validate",
            "v",
            "thank you for telling me that. feeling like a burden is so painful, and you're not one.",
        ),
        (
            2,
            "ask_directly",
            "a",
            "sometimes when people feel this hopeless they think about suicide. are you thinking about killing yourself?",
        ),
        (
            2,
            "ask_directly",
            "av",
            "i hear how heavy this is. i care about you, so i'm going to ask directly: have you thought about suicide?",
        ),
        (
            2,
            "ask_directly",
            "a",
            "when you say it won't get better, do you mean you've had thoughts of ending your life?",
        ),
        (
            2,
            "refer",
            "re",
            "i don't think you should carry this alone. would you want to talk to the counselor with me there?",
        ),
        (
            2,
            "follow_up",
            "f",
            "you're not annoying me, at all. i'm here and i'm not going anywhere.",
        ),
        (
            2,
            "combo",
            "vae",
            "that sounds so lonely. have you had thoughts of suicide? whatever the answer is, you don't have to deal with this alone.",
        ),
        (
            2,
            "combo",
            "vf",
            "i'm really glad you said it out loud. i'll check on you tomorrow, and the day after.",
        ),
        (
            3,
            "validate",
            "v",
            "thank you for trusting me with that. i'm so glad you told me, and i'm not freaking out.",
        ),
        (
            3,
            "ask_directly",
            "av",
            "thanks for telling me. are you thinking about killing yourself right now, or is it more that the thoughts come and go?",
        ),
        (
            3,
            "refer",
            "re",
            "i'm not going to keep this secret because i care about you too much. can we tell the counselor together?",
        ),
        (
            3,
            "refer",
            "rn",
            "you can call or text 988 anytime, and i'll sit with you while you do it. want to try right now?",
        ),
        (3, "refer", "re", "would you tell your mom if i came with you? i can be right there."),
        (
            3,
            "follow_up",
            "f",
            "i'm here, and i'm not going anywhere. i'll text you tonight and tomorrow.",
        ),
        (
            3,
            "combo",
            "vre",
            "that sounds terrifying to carry alone. you deserve support, and i'll go with you to the counselor.",
        ),
        (
            3,
            "combo",
            "vrf",
            "i'm really glad you told me. let's tell the counselor together, and i'll stay with you after.",
        ),
        (
            4,
            "refer",
            "re",
            "yes, i'll come with you to the counselor. want to go now, or after first period?",
        ),
        (
            4,
            "refer",
            "rn",
            "we can text 988 together first if that feels easier. i'll stay right here.",
        ),
        (
            4,
            "follow_up",
            "f",
            "i'll be with you the whole time, and i'll check in on you tonight too.",
        ),
        (4, "follow_up", "f", "you're not alone anymore. i'll sit with you at lunch tomorrow too."),
        (4, "validate", "v", "that took a lot of courage. i'm proud of you for saying it."),
        (
            4,
            "combo",
            "vrf",
            "i'm so glad you told me. let's go to the counselor together, and i'll check on you after.",
        ),
        (
            4,
            "combo",
            "ve",
            "asking for help is one of the bravest things. you've got me, and we'll get you more people.",
        ),
        (
            4,
            "combo",
            "rnf",
            "let's talk to the counselor today. if tonight is hard, we can text 988 together, and i'm around.",
        ),
    ],
    "failing-chem": [
        (0, "check_in", "c", "that grade sounds rough. how are you actually doing with it?"),
        (0, "check_in", "c", "you seem really tired lately. is everything ok?"),
        (0, "check_in", "c", "i know you said it's fine, but how are you really feeling about it?"),
        (0, "validate", "v", "that's a lot of pressure to be under. anyone would be stressed."),
        (0, "validate", "v", "i'd feel awful too. it makes sense that it's getting to you."),
        (
            0,
            "follow_up",
            "f",
            "i'll check in on you tomorrow. even if it's just to complain about chem.",
        ),
        (0, "combo", "cv", "that sounds stressful. how are you holding up?"),
        (0, "combo", "cf", "how are you really doing? i'll text you tonight, ok?"),
        (1, "check_in", "c", "four hours of sleep is brutal. what's keeping you up?"),
        (
            1,
            "validate",
            "v",
            "being scared to tell your parents makes total sense. that's a lot of weight.",
        ),
        (1, "validate", "v", "of course you're exhausted. you're carrying so much."),
        (
            1,
            "ask_directly",
            "av",
            "that sounds like a lot of stress. i have to ask: have you had thoughts of suicide?",
        ),
        (
            1,
            "follow_up",
            "f",
            "i'll study with you after school this week, and i'll text you tonight.",
        ),
        (1, "combo", "cv", "that sounds heavy. how are you holding up, really?"),
        (
            1,
            "combo",
            "ve",
            "you don't have to deal with this alone. it makes sense that you're scared to tell them.",
        ),
        (
            1,
            "refer",
            "re",
            "i think a counselor could help with the sleep and the grade. i can go with you.",
        ),
        (
            2,
            "validate",
            "v",
            "feeling like a failure when you're trying this hard is so painful. i'm glad you told me.",
        ),
        (
            2,
            "ask_directly",
            "a",
            "when you say your future is ruined, are you thinking about suicide?",
        ),
        (
            2,
            "ask_directly",
            "av",
            "i'm worried about you, so i'm going to ask straight out: are you thinking about killing yourself?",
        ),
        (2, "ask_directly", "a", "do you ever think about ending your life when it all piles up?"),
        (
            2,
            "refer",
            "re",
            "can we talk to your chem teacher or the counselor together? i'll go with you.",
        ),
        (2, "follow_up", "f", "one grade doesn't ruin a future, and i'm not going anywhere."),
        (
            2,
            "combo",
            "vae",
            "that sounds crushing. are you having thoughts of suicide? you don't have to carry this alone.",
        ),
        (2, "combo", "vf", "thank you for telling me. i'll check on you tomorrow, no matter what."),
        (
            3,
            "validate",
            "v",
            "thank you for telling me. i'm not freaking out, and i'm really glad you said it.",
        ),
        (
            3,
            "ask_directly",
            "av",
            "that sounds so heavy. are you thinking about killing yourself right now, or when the pressure builds?",
        ),
        (
            3,
            "refer",
            "re",
            "i can't keep this secret because i care about you. can we tell the counselor together?",
        ),
        (3, "refer", "rn", "you can call or text 988 anytime. want to do it together right now?"),
        (
            3,
            "refer",
            "re",
            "would you tell your parents if i came with you? or we could start with the counselor.",
        ),
        (3, "follow_up", "f", "i'm here. i'm not going anywhere. i'll text you tonight."),
        (
            3,
            "combo",
            "vre",
            "you don't have to carry that alone. let's talk to the counselor today, and i'll come with you.",
        ),
        (
            3,
            "combo",
            "vrf",
            "i'm really glad you told me. let's get you help, and i'll stay with you after.",
        ),
        (
            4,
            "refer",
            "re",
            "yes, let's talk to the counselor together. i'll come with you right now.",
        ),
        (4, "refer", "rn", "if tonight gets hard, we can text 988 together. i'll be on with you."),
        (4, "follow_up", "f", "i'll be with you the whole time, and i'll check in tonight."),
        (
            4,
            "follow_up",
            "f",
            "i'll help you figure out what to say to your chem teacher. and i'll text you after.",
        ),
        (4, "validate", "v", "that took courage. i'm proud of you."),
        (
            4,
            "combo",
            "vrf",
            "i'm so glad you told me. let's go to the counselor together, and i'll check on you after.",
        ),
        (
            4,
            "combo",
            "ve",
            "asking for help is a strong move. you've got me, and we'll find more people too.",
        ),
        (
            4,
            "combo",
            "rnf",
            "let's talk to the counselor today. if it gets hard, we can call 988 together. i'm around.",
        ),
    ],
    "giving-stuff-away": [
        (
            0,
            "check_in",
            "c",
            "hey, thank you for the hoodie. you gave away your setup too, and that's not like you. you ok?",
        ),
        (0, "check_in", "c", "i know you said all good. but how are you actually doing?"),
        (
            0,
            "check_in",
            "c",
            "no pressure, but i noticed you gave away a lot of stuff. what's going on?",
        ),
        (0, "validate", "v", "that makes sense. sometimes you want to clear things out."),
        (0, "validate", "v", "i appreciate you telling me. that can't be easy to say."),
        (0, "follow_up", "f", "i'll check on you tomorrow, even if you say all good."),
        (
            0,
            "combo",
            "cv",
            "hey, you've seemed a little different lately. you ok? i'm here either way.",
        ),
        (0, "combo", "cf", "how are you really doing? i'll text you tonight."),
        (1, "check_in", "c", "tense at home sounds exhausting. how are you handling it?"),
        (1, "validate", "v", "feeling numb for weeks makes sense when home is that tense."),
        (1, "validate", "v", "thanks for being honest. i know that's hard to say."),
        (
            1,
            "ask_directly",
            "av",
            "that sounds really hard. i want to ask you directly: are you thinking about suicide?",
        ),
        (1, "follow_up", "f", "i'll come over this weekend so you're not alone."),
        (1, "combo", "cv", "that sounds heavy. how are you holding up, really?"),
        (1, "combo", "vf", "i'm glad you told me. i'll text you tonight and tomorrow."),
        (
            1,
            "refer",
            "re",
            "i think the counselor might help with all the tension at home. i can go with you.",
        ),
        (
            2,
            "validate",
            "v",
            "thank you for saying that. feeling like everyone would be better off is so painful, and it isn't true.",
        ),
        (
            2,
            "ask_directly",
            "a",
            "when you say everyone would be better off, are you thinking about killing yourself?",
        ),
        (
            2,
            "ask_directly",
            "av",
            "i hear how heavy this is. i care about you, so i'm asking directly: are you having thoughts of suicide?",
        ),
        (
            2,
            "ask_directly",
            "a",
            "did you give your stuff away because you're thinking about ending your life?",
        ),
        (2, "refer", "re", "can we talk to the counselor together? i'll go with you."),
        (2, "follow_up", "f", "i'm here and i'm not going anywhere."),
        (
            2,
            "combo",
            "vae",
            "that sounds so lonely. are you thinking about suicide? you don't have to deal with this alone.",
        ),
        (2, "combo", "vf", "i'm glad you said that out loud. i'll check on you tomorrow."),
        (3, "validate", "v", "thank you for telling me. i'm glad you did, and i noticed."),
        (
            3,
            "ask_directly",
            "av",
            "thanks for being honest. are you thinking about killing yourself right now, or is it more that the thoughts keep coming?",
        ),
        (
            3,
            "refer",
            "re",
            "i can't keep this secret because i care about you. can we go to the counselor together today?",
        ),
        (3, "refer", "rn", "you can call or text 988 anytime. want to do it together right now?"),
        (
            3,
            "refer",
            "re",
            "would you tell your parents if i came with you? or we could start with the counselor.",
        ),
        (3, "follow_up", "f", "i'm here. i'm not going anywhere. i'll text you tonight."),
        (
            3,
            "combo",
            "vre",
            "you don't have to carry that alone. let's talk to the counselor today, and i'll come with you.",
        ),
        (
            3,
            "combo",
            "vrf",
            "i'm really glad you told me. let's get you help, and i'll stay with you after.",
        ),
        (4, "refer", "re", "yes, i'll go with you to the counselor today. let's go right now."),
        (4, "refer", "rn", "we can call or text 988 together. i'll stay right here."),
        (4, "follow_up", "f", "i'll be with you the whole time, and i'll check on you tonight."),
        (4, "follow_up", "f", "you're not alone. i'll come over this weekend too."),
        (4, "validate", "v", "that took a lot of courage. i'm proud of you."),
        (
            4,
            "combo",
            "vrf",
            "i'm so glad you told me. let's go to the counselor together, and i'll check on you after.",
        ),
        (
            4,
            "combo",
            "ve",
            "asking for help is brave. you've got me, and we'll find more people to help too.",
        ),
        (
            4,
            "combo",
            "rnf",
            "let's go to the counselor today. if tonight is hard, we can call 988 together. i'm around.",
        ),
    ],
    "group-chat": [
        (0, "check_in", "c", "hey, i saw the group chat. you ok?"),
        (0, "check_in", "c", "i know you said you don't care, but how are you really doing?"),
        (0, "check_in", "c", "no pressure. i just wanted to check on you after the gc stuff."),
        (0, "validate", "v", "that would've bothered me too. it's ok to be annoyed."),
        (
            0,
            "validate",
            "v",
            "that sounds humiliating, honestly. you don't have to act like it's nothing.",
        ),
        (0, "follow_up", "f", "i'll text you tonight. no big deal, just checking."),
        (0, "combo", "cv", "i saw the gc. that sounds rough. you ok?"),
        (0, "combo", "cf", "how are you doing? i'll sit with you at lunch tomorrow if you want."),
        (1, "check_in", "c", "skipping lunch sounds lonely. what's it been like?"),
        (
            1,
            "validate",
            "v",
            "of course you keep reading it. that's something a lot of people do when they're hurt.",
        ),
        (1, "validate", "v", "it makes sense that you avoid lunch. that would be hard for anyone."),
        (
            1,
            "ask_directly",
            "av",
            "that sounds really hard. i want to ask directly: are you thinking about suicide?",
        ),
        (1, "follow_up", "f", "i'll sit with you at lunch. no big deal."),
        (1, "combo", "cv", "that sounds painful. how are you holding up?"),
        (1, "combo", "vf", "i'm on your side. i'll text you tonight."),
        (1, "refer", "re", "would you want to tell a teacher about the gc? i'll go with you."),
        (
            2,
            "validate",
            "v",
            "that sounds really painful. i don't hate you, and i'm glad you told me.",
        ),
        (
            2,
            "ask_directly",
            "a",
            "when you say what's the point, are you thinking about killing yourself?",
        ),
        (
            2,
            "ask_directly",
            "av",
            "i care about you, so i'm going to ask directly: have you had thoughts of suicide?",
        ),
        (2, "ask_directly", "a", "are you thinking about ending your life?"),
        (2, "refer", "re", "can we tell a teacher or your mom together? i'll be there."),
        (2, "follow_up", "f", "i'm on your side, and i'm not going anywhere."),
        (
            2,
            "combo",
            "vae",
            "that sounds so heavy. are you thinking about suicide? you don't have to deal with this alone.",
        ),
        (2, "combo", "vf", "i'm glad you said that. i'll check on you tomorrow."),
        (
            3,
            "validate",
            "v",
            "thank you for telling me. i'm not freaking out, and i'm glad you said it.",
        ),
        (
            3,
            "ask_directly",
            "av",
            "thanks for being honest. are you thinking about killing yourself right now?",
        ),
        (
            3,
            "refer",
            "re",
            "i can't keep this a secret because i care about you. can we tell your mom together?",
        ),
        (3, "refer", "rn", "you can call or text 988 anytime. want to try it together?"),
        (3, "refer", "re", "would you tell a teacher if i came with you?"),
        (3, "follow_up", "f", "i'm here. i'm not going anywhere. i'll text you tonight."),
        (
            3,
            "combo",
            "vre",
            "you don't have to deal with this alone. let's tell your mom, and i'll be there.",
        ),
        (
            3,
            "combo",
            "vrf",
            "i'm really glad you told me. let's get you help, and i'll stay with you after.",
        ),
        (4, "refer", "re", "yes, i'll help you tell your mom. we can do it together right now."),
        (4, "refer", "rn", "we can text 988 together. i'll stay right here."),
        (4, "follow_up", "f", "i'll be with you the whole time, and i'll check on you tonight."),
        (4, "follow_up", "f", "you're not alone. i'll sit with you at lunch tomorrow."),
        (4, "validate", "v", "that took courage. i'm proud of you."),
        (
            4,
            "combo",
            "vrf",
            "i'm so glad you told me. let's tell your mom together, and i'll check on you after.",
        ),
        (
            4,
            "combo",
            "ve",
            "asking for help is brave. you've got me, and we'll find more people too.",
        ),
        (
            4,
            "combo",
            "rnf",
            "let's tell a teacher today. if tonight is hard, we can call 988 together. i'm around.",
        ),
    ],
    "new-school": [
        (
            0,
            "check_in",
            "c",
            "hey, i've been wondering how the new school is really going. how are you doing?",
        ),
        (0, "check_in", "c", "no pressure, but you seem quiet. everything ok?"),
        (0, "check_in", "c", "i just wanted to check in. how are you really?"),
        (0, "validate", "v", "moving is a lot. it's ok if it's hard."),
        (0, "validate", "v", "that makes sense. being new is exhausting."),
        (0, "follow_up", "f", "i'll text you tomorrow, just to check on you."),
        (0, "combo", "cv", "moving is hard. how are you holding up?"),
        (0, "combo", "cf", "how are you really? i'll sit with you at lunch tomorrow if you want."),
        (1, "check_in", "c", "eating alone sounds lonely. how long has that been happening?"),
        (
            1,
            "validate",
            "v",
            "it makes sense that you feel lonely when your old friends stopped texting.",
        ),
        (1, "validate", "v", "that sounds really hard. i'm glad you told me."),
        (
            1,
            "ask_directly",
            "av",
            "that sounds really lonely. i want to ask directly: are you thinking about suicide?",
        ),
        (1, "follow_up", "f", "come sit with me at lunch tomorrow. i'll save you a seat."),
        (1, "combo", "cv", "that sounds lonely. how have you been feeling?"),
        (1, "combo", "vf", "i'm glad you told me. i'll text you tonight."),
        (1, "refer", "re", "would you want to talk to the counselor about it? i can go with you."),
        (
            2,
            "validate",
            "v",
            "feeling invisible is so painful. i notice you, and i'm glad you told me.",
        ),
        (
            2,
            "ask_directly",
            "a",
            "when you say no one would notice if you weren't here, are you thinking about suicide?",
        ),
        (
            2,
            "ask_directly",
            "av",
            "i care about you, so i'm going to ask directly: have you had thoughts of killing yourself?",
        ),
        (2, "ask_directly", "a", "are you thinking about ending your life?"),
        (2, "refer", "re", "can we talk to the counselor together? i'll go with you."),
        (2, "follow_up", "f", "i'm here, and i'm not going anywhere."),
        (
            2,
            "combo",
            "vae",
            "that sounds so lonely. are you thinking about suicide? you don't have to deal with this alone.",
        ),
        (2, "combo", "vf", "i'm glad you said it. i'll check on you tomorrow."),
        (
            3,
            "validate",
            "v",
            "thank you for telling me. i'm not going to be weird about it, and i'm glad you said it.",
        ),
        (
            3,
            "ask_directly",
            "av",
            "thanks for being honest. are you thinking about killing yourself right now, or is it mostly at night?",
        ),
        (
            3,
            "refer",
            "re",
            "i can't keep this a secret because i care about you. can we tell the counselor together?",
        ),
        (
            3,
            "refer",
            "rn",
            "you can call or text 988 anytime, and they have people who speak Spanish too. want to try it together?",
        ),
        (
            3,
            "refer",
            "re",
            "would you tell your parents if i came with you? or we can start with the counselor.",
        ),
        (3, "follow_up", "f", "i'm here. i'm not going anywhere. i'll text you tonight."),
        (
            3,
            "combo",
            "vre",
            "you don't have to carry that alone. let's talk to the counselor, and i'll come with you.",
        ),
        (
            3,
            "combo",
            "vrf",
            "i'm really glad you told me. let's get you help, and i'll stay with you after.",
        ),
        (4, "refer", "re", "yes, i'll come with you to the counselor. let's go together."),
        (
            4,
            "refer",
            "rn",
            "we can call or text 988 together if tonight is hard. i'll stay right here.",
        ),
        (
            4,
            "follow_up",
            "f",
            "i'll sit with you at lunch tomorrow, and i'll check on you tonight.",
        ),
        (4, "follow_up", "f", "you're not alone anymore. i'll be with you the whole time."),
        (4, "validate", "v", "that took courage. i'm proud of you."),
        (
            4,
            "combo",
            "vrf",
            "i'm so glad you told me. let's go to the counselor together, and i'll check on you after.",
        ),
        (
            4,
            "combo",
            "ve",
            "asking for help is brave. you've got me, and we'll find more people too.",
        ),
        (
            4,
            "combo",
            "rnf",
            "let's talk to the counselor today. if tonight is hard, we can call 988 together. i'm around.",
        ),
    ],
}

PREFIX = {
    "after-the-breakup": "mya",
    "failing-chem": "jor",
    "giving-stuff-away": "sam",
    "group-chat": "eli",
    "new-school": "pri",
}


# Spanish exemplars for Maya (after-the-breakup): natural US-teen Spanish, same schema/strategies/levels as the EN file.
EX_ES: list[tuple[int, str, str, str]] = [
    (
        0,
        "check_in",
        "c",
        "oye, noté que ya no te sientas con nosotros en el almuerzo. ¿estás bien?",
    ),
    (0, "check_in", "c", "sin presión, pero ¿cómo andas de verdad? te he visto medio calladita."),
    (
        0,
        "check_in",
        "c",
        "no tienes que contarme nada grande, solo quería que supieras que me di cuenta de que andas rara.",
    ),
    (0, "validate", "v", "uf, qué cansado debe ser eso. con razón andas agotada."),
    (0, "validate", "v", "te entiendo, neta. a dos semanas de algo así a cualquiera le pega."),
    (
        0,
        "follow_up",
        "f",
        "ok. igual te escribo mañana para ver cómo estás, aunque me digas que bien.",
    ),
    (
        0,
        "combo",
        "cv",
        "oye, te noto medio apagada. ¿estás bien? no tienes que explicarme, solo me importas.",
    ),
    (
        0,
        "combo",
        "cf",
        "¿cómo andas de verdad? yo estoy por aquí en la noche si quieres escribirme.",
    ),
    (1, "check_in", "c", "se oye bien pesado. ¿me cuentas qué es lo que no deja de darte vueltas?"),
    (
        1,
        "validate",
        "v",
        "claro que no puedes dormir. darle vueltas a algo tan grande cansa un montón.",
    ),
    (
        1,
        "validate",
        "v",
        "tiene todo el sentido que te dé vergüenza si toda la escuela se enteró. eso le dolería a cualquiera.",
    ),
    (
        1,
        "ask_directly",
        "av",
        "se oye bien pesado. te lo quiero preguntar de frente: ¿has pensado en suicidarte?",
    ),
    (
        1,
        "follow_up",
        "f",
        "no lo voy a hacer raro. mañana me siento contigo en el almuerzo si quieres.",
    ),
    (1, "combo", "cv", "eso suena doloroso. ¿cómo has estado aguantando todo esto?"),
    (1, "combo", "vf", "no tienes que fingir conmigo. aquí estoy y te escribo en la noche."),
    (
        1,
        "refer",
        "r",
        "estaba pensando si la consejera te podría ayudar con lo de dormir. yo te acompaño si quieres.",
    ),
    (
        2,
        "validate",
        "v",
        "gracias por decírmelo. sentirte como una carga duele un montón, y no lo eres.",
    ),
    (
        2,
        "ask_directly",
        "a",
        "a veces cuando uno se siente así de sin esperanza piensa en el suicidio. ¿estás pensando en matarte?",
    ),
    (
        2,
        "ask_directly",
        "av",
        "escucho lo pesado que está todo. me importas, así que te pregunto directo: ¿has pensado en quitarte la vida?",
    ),
    (
        2,
        "ask_directly",
        "a",
        "cuando dices que no va a mejorar, ¿quieres decir que has pensado en terminar con tu vida?",
    ),
    (
        2,
        "refer",
        "r",
        "no creo que debas cargar con esto tú sola. ¿quieres hablar con la consejera? yo me quedo contigo.",
    ),
    (2, "follow_up", "f", "no me molestas para nada. aquí estoy y no me voy a ningún lado."),
    (
        2,
        "combo",
        "vae",
        "se oye muy solo todo eso. ¿has tenido pensamientos de suicidio? sea lo que sea, no tienes que pasar por esto sola.",
    ),
    (
        2,
        "combo",
        "vf",
        "me alegra mucho que lo hayas dicho en voz alta. mañana te escribo, y pasado mañana también.",
    ),
    (
        3,
        "validate",
        "v",
        "gracias por confiar en mí con eso. me alegra que me lo dijeras, y no me estoy asustando.",
    ),
    (
        3,
        "ask_directly",
        "av",
        "gracias por contármelo. ¿estás pensando en matarte ahorita, o es más que los pensamientos van y vienen?",
    ),
    (
        3,
        "refer",
        "r",
        "no voy a guardar esto en secreto porque me importas demasiado. ¿le decimos juntas a la consejera?",
    ),
    (
        3,
        "refer",
        "n",
        "puedes llamar o mandar mensaje al 988 a la hora que sea, y yo me quedo contigo mientras lo haces. ¿lo intentamos ahorita?",
    ),
    (3, "refer", "r", "¿le dirías a tu mamá si voy contigo? yo estoy ahí a tu lado."),
    (
        3,
        "follow_up",
        "f",
        "aquí estoy y no me voy a ningún lado. te escribo en la noche y mañana también.",
    ),
    (
        3,
        "combo",
        "ver",
        "qué miedo cargar eso sola. mereces apoyo, y yo te acompaño con la consejera.",
    ),
    (
        3,
        "combo",
        "vrf",
        "qué bueno que me lo dijiste. vamos con la consejera juntas, y después me quedo contigo.",
    ),
    (
        4,
        "refer",
        "r",
        "sí, voy contigo con la consejera. ¿vamos ahorita o después de la primera clase?",
    ),
    (
        4,
        "refer",
        "n",
        "podemos escribir al 988 primero si te da menos miedo. yo me quedo aquí contigo.",
    ),
    (4, "follow_up", "f", "voy a estar contigo todo el tiempo, y esta noche también te escribo."),
    (4, "follow_up", "f", "ya no estás sola. mañana me siento contigo en el almuerzo también."),
    (4, "validate", "v", "eso requirió mucho valor. estoy orgullosa de que lo dijeras."),
    (
        4,
        "combo",
        "vrf",
        "qué bueno que me lo contaste. vamos con la consejera juntas, y luego te escribo para ver cómo estás.",
    ),
    (
        4,
        "combo",
        "vef",
        "pedir ayuda es de lo más valiente que hay. me tienes a mí, y entre las dos buscamos más gente que te apoye.",
    ),
    (
        4,
        "combo",
        "rnf",
        "hoy hablamos con la consejera. si en la noche se pone difícil, llamamos juntas al 988, y yo ando por aquí.",
    ),
]


def derive_es(codes: str, text: str) -> list[str]:
    """Spanish counterpart of derive(): c/v/f are authored; the rest are read off the text."""
    t = text.lower()
    labels = {CODE[c] for c in codes if c in "cvf"}
    if (
        re.search(r"suicid|matarte|quitarte la vida|terminar con tu vida|hacerte da", t)
        and "?" in t
    ):
        labels.add("asked_directly")
    if re.search(r"consejer|\bmam[aá]\b|maestr|profe|pap[aá]s|enfermer|entrenador", t):
        labels.add("referred_adult")
    if "988" in t:
        labels.add("referred_988")
    if re.search(r"no tienes que pasar|mereces apoyo|pedir ayuda|que te apoye|cargar con esto", t):
        labels.add("encouraged_help")
    order = list(CODE.values())
    return sorted(labels, key=order.index)


def derive(codes: str, text: str) -> list[str]:
    """c, v, f come from the authored code; the rest are read off the text so labels never drift."""
    t = text.lower()
    labels = {CODE[c] for c in codes if c in "cvf"}
    if re.search(r"suicide|killing yourself|ending your life", t) and "?" in t:
        labels.add("asked_directly")
    if re.search(r"counselor|\bmom\b|teacher|parents|nurse|coach", t):
        labels.add("referred_adult")
    if "988" in t:
        labels.add("referred_988")
    if re.search(r"alone|support|brave|get you help|asking for help|help with", t):
        labels.add("encouraged_help")
    order = list(CODE.values())
    return sorted(labels, key=order.index)


def build() -> dict[str, list[dict]]:
    out = {}
    for sid, items in EX.items():
        rows = []
        for i, (level, strategy, codes, text) in enumerate(items, 1):
            rows.append(
                {
                    "id": f"ex-{PREFIX[sid]}-{i:02d}",
                    "scenario_id": sid,
                    "locale": "en",
                    "level": level,
                    "strategy": strategy,
                    "text": text,
                    "labels": derive(codes, text),
                }
            )
        out[sid] = rows
    return out


if __name__ == "__main__":
    for sid, rows in build().items():
        write_jsonl(DATA / "exemplars" / f"{sid}.en.jsonl", rows)
        print(sid, len(rows))
    es_rows = [
        {
            "id": f"ex-mya-es-{i:02d}",
            "scenario_id": "after-the-breakup",
            "locale": "es",
            "level": lv,
            "strategy": st,
            "text": tx,
            "labels": derive_es(cd, tx),
        }
        for i, (lv, st, cd, tx) in enumerate(EX_ES, 1)
    ]
    write_jsonl(DATA / "exemplars" / "after-the-breakup.es.jsonl", es_rows)
    print("after-the-breakup.es", len(es_rows))
