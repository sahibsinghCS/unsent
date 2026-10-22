"""Hand-written, whole (not pool-composed) helper replies: 4 per context = 300.

Codes: c=checked_in v=validated a=asked_directly e=encouraged_help r=referred_adult n=referred_988
f=follow_up d=dismissed x=advice_dump s=promised_secrecy, "-" = no label.
"""

FF: dict[str, list[tuple[str, str]]] = {
    # ---------------------------------------------------------------- after-the-breakup (Maya)
    "breakup-L0-1": [
        (
            "no need to say sorry!! honestly i just noticed we haven't talked in a while and wanted to see how u're doing",
            "c",
        ),
        ("lol ur fine. but real talk, you ok? you've been kinda ghosting the group chat", "c"),
        (
            "it's been two weeks since everything with your ex, right? if you want to talk about it i'm around, if not we can just watch dumb videos",
            "v f",
        ),
        ("ay no te disculpes, ¿cómo estás tú? te he extrañado en el almuerzo", "c"),
    ],
    "breakup-L0-2": [
        (
            "homework til late sucks. but are you ok otherwise? you seemed kind of quiet at lunch",
            "c",
        ),
        ("just sleep earlier maybe?? i feel like everyone's just tired lately tbh", "x"),
        ("haha same, i've been up till 1 every night. anyway you want to come over saturday?", "d"),
        ("you don't have to be fine with me, you know. i'm not going to judge you", "v"),
    ],
    "breakup-L0-3": [
        (
            "ok but you said you're good like 3 times, which makes me think you're not 😅 what's going on?",
            "c",
        ),
        (
            "busy is one thing, but you've also stopped sitting with us. just want you to know the seat's still there",
            "c f",
        ),
        ("school stuff is a lot rn for everyone. i'm here if it's more than that, okay?", "v f"),
        ("bueno, si necesitas hablar de lo que sea, no solo de tarea, aquí estoy", "f"),
    ],
    "breakup-L1-1": [
        (
            "replaying stuff on a loop at 3am is the worst. what's the thing you keep coming back to?",
            "v c",
        ),
        (
            "have you tried like a podcast or white noise or something?? that works for me when my brain won't shut up",
            "x",
        ),
        ("that sounds so exhausting, honestly. i'm sorry you're stuck with that on repeat", "v"),
        ("no puedes dormir y encima pensando en eso, qué horror. ¿quieres contarme?", "v c"),
    ],
    "breakup-L1-2": [
        (
            "ugh the whole school knowing is such a violation. it makes sense that it feels embarrassing",
            "v",
        ),
        ("honestly nobody will care in a month, people forget everything lol", "d"),
        ("i'm not gonna bring it up with anyone else, i just want to know how you are", "c"),
        (
            "ok that's genuinely rough. do you want me to sit with you at lunch so you're not alone in it?",
            "v f",
        ),
    ],
    "breakup-L1-3": [
        ("anyway what?? you can finish the thought, i'm listening", "c"),
        (
            "being embarrassed makes sense, but you should really just stop caring what people think, they're not paying that much attention",
            "x",
        ),
        ("it's not embarrassing to be sad about a two year relationship. that's a real loss", "v"),
        (
            "if it keeps being this heavy, talking to the school counselor isn't a bad idea. i could go with you",
            "r e",
        ),
    ],
    "breakup-L2-1": [
        (
            "i hear you. it really does feel like that when you're this deep in it. can i ask you something kind of scary though? are you having thoughts of suicide?",
            "v a",
        ),
        (
            "tomorrow might not be different, but you don't have to be alone in it. i'll text you every night this week",
            "e f",
        ),
        ("it WILL get better, it always does, i promise", "d"),
        (
            "¿sientes que ya no quieres seguir viviendo? te lo pregunto de frente porque me importas",
            "a",
        ),
    ],
    "breakup-L2-2": [
        (
            "you are not annoying me. like at all. i'd rather know how you really feel than get \"i'm fine\"",
            "v",
        ),
        (
            "honestly if you feel like you're annoying people you should just talk to a therapist, that's literally what they're for",
            "e r",
        ),
        ("u annoy me when u say u annoy me lol", "d"),
        (
            "when you say that, do you ever feel like you don't want to be here anymore? like, thinking about killing yourself?",
            "a",
        ),
    ],
    "breakup-L2-3": [
        ("a burden?? maya no. you're my friend, that's not what this is", "v"),
        (
            "stop dragging yourself, it's not that deep. you're gonna be so over this by summer",
            "d x",
        ),
        (
            "i don't think that at all, and i'm glad you said it out loud. is it getting so heavy you think about suicide?",
            "v a",
        ),
        (
            "if you ever want, we can text 988 together. no pressure, just so you know it's an option",
            "n",
        ),
    ],
    "breakup-L3-1": [
        (
            "thank you for telling me. i'm not freaking out, i promise. i'm really glad you said it",
            "v",
        ),
        ("ok. i'm here. i'm not going anywhere tonight. can i stay on the phone with you?", "f"),
        (
            "i think we need to tell the counselor, i can't keep this just between us because i care too much. i'll be next to you the whole time",
            "r",
        ),
        (
            "lo siento tanto que te sientas así. gracias por confiar en mí. ¿quieres llamar al 988 juntas?",
            "v n",
        ),
    ],
    "breakup-L3-2": [
        ("i won't tell anyone, i promise, nobody will hear it from me", "s"),
        (
            "i can't promise to keep it secret, because i want you safe. but i can promise i'll be with you when we tell someone",
            "r f",
        ),
        (
            "people react in all kinds of ways but the people who love you will want to help. want to start with one adult you trust?",
            "r e",
        ),
        (
            "it's okay to be scared. i'm scared a little too, but i'd rather be scared with you than not know",
            "v",
        ),
    ],
    "breakup-L3-3": [
        (
            "do you want to talk about the thoughts? you don't have to say details, i just want to understand how serious it is. are you thinking of killing yourself?",
            "a",
        ),
        ("honestly everybody has those thoughts sometimes, it's not that serious", "d"),
        ("you can call or text 988 anytime. it's free and they're trained for exactly this", "n"),
        (
            "gracias por decírmelo. no tienes que cargar con esto sola, hablemos con la consejera mañana, voy contigo",
            "e r",
        ),
    ],
    "breakup-L4-1": [
        ("yes. i'll walk in with you. we can go first thing tomorrow before class, ok?", "r f"),
        ("proud of you. seriously. that's hard and you did it", "v"),
        (
            "ok perfect, i'll talk to the counselor with you and then text you after to see how it went",
            "r f",
        ),
        ("sleep on it and see how you feel in the morning", "x"),
    ],
    "breakup-L4-2": [
        ("i'm really glad i asked too. you shouldn't have had to wait for somebody to", "v"),
        ("i'm going to keep asking, you know. not just today", "f"),
        ("if tonight is hard before we see the counselor, text me or text 988, either one", "n f"),
        ("lol of course i'd ask, ur my friend", "-"),
    ],
    "breakup-L4-3": [
        (
            "talking to someone is a really good idea. you don't have to do it alone, we'll find the right person together",
            "e",
        ),
        ("that sounds like a plan. counselor, then lunch, then maybe boba, my treat", "r f"),
        ("lighter is good. that's how it goes when you finally say it out loud", "v"),
        ("hell yes. let's do it. i'll text you tonight so you're not by yourself", "e f"),
    ],
    # ---------------------------------------------------------------- failing-chem (Jordan)
    "chem-L0-1": [
        ("oof. how bad are we talking?", "-"),
        ("ok but how are YOU, not the grade", "c"),
        ("chem is brutal for everyone, you'll bounce back lol", "d"),
        ("¿cómo te fue? ¿estás bien o te cayó muy pesado?", "c"),
    ],
    "chem-L0-2": [
        ("ha. thriving is a strong word for someone who texts me at 2am. you ok?", "c"),
        (
            "if one class is ruining your week that's not nothing. it's okay to be bothered by it",
            "v",
        ),
        ("just ask the teacher for extra credit or something? that usually works", "x"),
        ("i'll bring snacks to the library tomorrow, we can look at it together", "f"),
    ],
    "chem-L0-3": [
        (
            "coffee at this hour is not a personality, it's a cry for help lol. kidding. mostly. you good?",
            "c",
        ),
        ("everything is great, sure. that's literally what i say when it isn't", "c"),
        ("coffee is a band-aid. you should really just go to bed earlier", "x"),
        ("tienes pinta de no haber dormido nada. ¿qué pasó?", "c"),
    ],
    "chem-L1-1": [
        (
            "telling parents about a grade is the worst. what are you most worried they'll say?",
            "v c",
        ),
        (
            "honestly just tell them tonight, ripping the band-aid off is better than dreading it",
            "x",
        ),
        (
            "i get being scared. i'd be scared too. do you want to practice what to say? i can pretend to be your mom",
            "v f",
        ),
        ("what if we asked the counselor how to bring it up? i can come along", "r"),
    ],
    "chem-L1-2": [
        (
            "four hours?? jordan that's not sustainable. that's not you being lazy, that's a lot",
            "v",
        ),
        ("you need to just sleep more or your grades will keep dropping, simple as that", "x d"),
        ("is the not sleeping about studying or is your brain kind of racing?", "c"),
        (
            "cuatro horas de sueño es poquísimo, entiendo que estés agotado. aquí estoy si quieres hablar",
            "v f",
        ),
    ],
    "chem-L1-3": [
        (
            "nodding while your parents talk about college sounds lonely. do they know how much pressure you feel?",
            "v",
        ),
        ("college isn't everything lol, relax", "d"),
        (
            "you don't have to hold all of that in. maybe you could talk to your counselor about the pressure?",
            "e r",
        ),
        ('how are you, though? like for real, not the "tired" answer', "c"),
    ],
    "chem-L2-1": [
        (
            'that sounds so heavy. when it feels like "it\'s never enough", do you ever think about hurting yourself or suicide?',
            "v a",
        ),
        ("you are not a failure for one bad grade. you have never been a failure to me", "v"),
        ("nobody fails at everything, dude. you're being dramatic. make a study plan", "d x"),
        ("lo que sientes es válido y no estás solo. ¿has pensado en quitarte la vida?", "v a"),
    ],
    "chem-L2-2": [
        (
            "ruined is how it feels tonight, but one grade can't ruin a future. we can look at options together tomorrow",
            "v f",
        ),
        ("i'm worried about you. are you thinking about killing yourself?", "a"),
        ("can i call the counselor with you? even just to ask how bad one grade actually is", "r"),
        ("future's long, it's one chem grade! you're way smarter than this", "d"),
    ],
    "chem-L2-3": [
        (
            "everyone looks like they've got it figured out, but i promise most are faking it. you're not alone in feeling behind",
            "v",
        ),
        (
            "failing at life is a big thing to say. is some of it a thought like you'd rather not be around?",
            "a",
        ),
        ("you can text 988 any time of day if it ever gets too loud in your head", "n"),
        ("I won't tell your parents, I swear. it's just between you and me", "s"),
    ],
    "chem-L3-1": [
        (
            "thank you for trusting me with that, jordan. i'm really glad you did. i'm not going anywhere",
            "v f",
        ),
        ("i'm so sorry you've been carrying this. are you safe right now?", "v c"),
        (
            "i think we need to tell someone who can help, like the counselor or your parents. i can come with you",
            "r",
        ),
        (
            "gracias por decírmelo, de verdad. tampoco quiero que lo cargues solo, ¿puedo acompañarte con la consejera?",
            "v r",
        ),
    ],
    "chem-L3-2": [
        (
            "you aren't letting anyone down by being honest. the people who love you would rather know",
            "v",
        ),
        (
            "disappearing isn't easier, it feels that way because you're exhausted. let's get you real support",
            "e",
        ),
        ("do you mean that you want to end your life?", "a"),
        (
            "you're way too smart to talk like that lol. just push through finals and it'll be fine",
            "d x",
        ),
    ],
    "chem-L3-3": [
        (
            "not having a plan matters, thank you for saying that. but the thoughts still deserve help. can we call 988 together?",
            "v n",
        ),
        ("it doesn't sound dramatic at all. it sounds like you're in a lot of pain", "v"),
        ("i'll keep this between us, don't worry, nobody has to know", "s"),
        (
            "let's tell your counselor tomorrow morning. i'll walk you there and wait outside if you want",
            "r f",
        ),
    ],
    "chem-L4-1": [
        (
            "yes, let's write down what to say to your chem teacher. i'll sit with you while you do it",
            "r f",
        ),
        ("honestly that's the bravest thing, i'm so proud of you", "v"),
        ("we can email the counselor tonight and go together", "r"),
        ("tengo tu espalda. mañana vamos juntos con la consejera", "r f"),
    ],
    "chem-L4-2": [
        ("i'm glad it felt lighter. it usually does after you say it", "v"),
        ("lol you're welcome, i wasn't being weird, you were just being brave", "v"),
        ("if tonight gets rough before you see anyone, text me or call 988", "n f"),
        ("anytime. i'll check on you in the morning", "f"),
    ],
    "chem-L4-3": [
        ("i'll come with you to the counselor. you won't have to do it alone", "r"),
        ("great plan. we'll go together right after first period", "r f"),
        ("getting help is not weakness. you deserve support just like anyone", "e"),
        ("just remember to breathe and not stress too much about it", "x"),
    ],
    # ---------------------------------------------------------------- giving-stuff-away (Sam)
    "sam-L0-1": [
        (
            "i loved the hoodie!! but also you've been giving away stuff and it's kinda making me worried. are you ok?",
            "c",
        ),
        ("lol thanks. that was nice of you. why though?", "-"),
        ("ok but the setup too?? that's your whole thing. what's going on with you", "c"),
        ("gracias por la sudadera, pero me quedé pensando en ti. ¿todo bien?", "c"),
    ],
    "sam-L0-2": [
        ("i believe you that you're all good, i just want to double check. no pressure", "c"),
        ("you didn't need it? you used to be on that setup every night. i noticed", "c"),
        ("haha random but ok. wanna get food after school?", "d"),
        ("whatever's going on, i'm around, ok? even if it's nothing", "f"),
    ],
    "sam-L0-3": [
        ("spring cleaning in october, sure sam. you're kind of a mystery rn", "c"),
        ("haha you're a funny guy but i'd feel better if you told me how you really are", "c"),
        ("honestly if you're stressed you should just chill and play some games. oh wait", "x d"),
        ("nunca te veo tan tranquilo, ¿seguro que estás bien?", "c"),
    ],
    "sam-L1-1": [
        ("tense at home sounds exhausting. do you want to tell me what's been going on?", "v c"),
        ("it's okay to not be fine. you don't have to say all good with me", "v"),
        (
            "have you tried just staying at a friend's house for a bit? it helps when stuff is tense",
            "x",
        ),
        ("lo siento, la tensión en casa agota mucho. aquí estoy para escucharte", "v f"),
    ],
    "sam-L1-2": [
        ("numb for weeks is kind of a big deal, sam. i'm glad you told me", "v"),
        (
            "are you thinking about suicide? i'm asking because i care, not because i think you're broken",
            "a",
        ),
        ("numb is just a phase. it passes when you stop dwelling on it", "d x"),
        (
            "it might help to talk to the school counselor about the numb stuff. want me to come?",
            "r e",
        ),
    ],
    "sam-L1-3": [
        ("staying in your room alone every day isn't \"chill\", it's lonely. i'm just saying", "v"),
        ("parents fight, it's whatever, just put on headphones", "d x"),
        ("i'm here to hang out or just text, whichever you want. i'll check in tonight", "f"),
        ("¿y tú cómo estás con todo eso? no te lo pregunto por cortesía, me importa", "c"),
    ],
    "sam-L2-1": [
        (
            "i'm really glad you said that, even with the haha. everyone would NOT be better off without you. are you thinking about suicide?",
            "v a",
        ),
        ("don't ignore it, ok? i'm not ignoring it", "v"),
        ("stop saying stuff like that, you're being so dramatic lol", "d"),
        (
            "si sientes que todos estarían mejor sin ti, necesito preguntarte: ¿piensas en quitarte la vida?",
            "a",
        ),
    ],
    "sam-L2-2": [
        (
            "i can't promise things will change overnight but i can promise i'll keep showing up",
            "f",
        ),
        (
            "it's hard to see change from inside it. would you let me go with you to talk to the counselor?",
            "v r",
        ),
        ("did you give away your stuff because you're thinking about ending your life?", "a"),
        ("all good is a lot of pressure to put on yourself. you can say not all good", "v"),
    ],
    "sam-L2-3": [
        ("i'd notice. i'd notice if you weren't here, immediately. you matter to me", "v"),
        ("you're not invisible, you're literally the funniest person i know. cheer up", "d x"),
        (
            "it sounds like you've been alone with this for a long time. do you ever think about killing yourself?",
            "v a",
        ),
        (
            "let's text 988 together, or talk to your mom or a teacher. whichever feels less scary",
            "n r",
        ),
    ],
    "sam-L3-1": [
        ("thank you for telling me. that took guts. i'm so glad you said it", "v"),
        ("ok. i'm staying right here. i'm not leaving. can i call you?", "f"),
        ("i won't tell anyone, promise", "s"),
        (
            "tengo que decirle a alguien que pueda ayudar, no puedo guardarlo en secreto porque me importas. ¿vamos juntos con la consejera?",
            "r",
        ),
    ],
    "sam-L3-2": [
        (
            "that makes sense and it also scares me. i'm so glad you didn't go through with anything. can we tell somebody today?",
            "v r",
        ),
        ("did you give your stuff away because you were planning to not be here?", "a"),
        (
            "i'm worried that if you're alone tonight it'll get worse. can i come over, or can you come to mine?",
            "f",
        ),
        ("you can call or text 988 at any hour, they won't judge you", "n"),
    ],
    "sam-L3-3": [
        ("i noticed. and i'm glad i did. thanks for letting me in", "v"),
        (
            "i noticed because i was looking out for you, not because you were being obvious. it matters that you spoke",
            "v",
        ),
        ("maybe tomorrow we can talk to the counselor, and i can sit next to you", "r f"),
        ("it's not your fault you feel like this, ok? please don't carry it alone", "e"),
    ],
    "sam-L4-1": [
        ("yes. let's go right now. i'm with you all the way", "r f"),
        ("proud of you for asking. let's go to the counselor's office before lunch", "r"),
        ("great. let's grab your stuff, i'll walk with you", "f"),
        ("sí, vamos hoy mismo. te acompaño todo el camino", "r f"),
    ],
    "sam-L4-2": [
        ("of course i noticed. i wasn't about to let you disappear on me", "v"),
        ("i'm so happy you want to talk to somebody. you really do deserve help", "e"),
        ("whatever you need, i've got you. we'll start with the counselor", "r f"),
        ("lol nah thank you for letting me", "-"),
    ],
    "sam-L4-3": [
        ("yes, let's call or text 988 together, right now if you want", "n"),
        ("we can do 988 and then the counselor tomorrow, one thing at a time", "n r"),
        ("i'll stay on the line with you the entire time", "f"),
        ("buena idea. llamemos al 988 juntos, yo me quedo contigo", "n f"),
    ],
    # ---------------------------------------------------------------- group-chat (Eli)
    "gc-L0-1": [
        ("yeah i saw it. it's honestly messed up that people are piling on", "v"),
        ("you say idc but i think you do. which is allowed", "v"),
        ("i did see it. you ok though", "c"),
        ("vi el chat. no creo que sea tan chiste como dicen. ¿cómo estás?", "c"),
    ],
    "gc-L0-2": [
        ("it's a joke until it happens to you. i'd be upset", "v"),
        ("lol relax, it'll be old news by friday", "d"),
        ("do you want to hang out this weekend? like no one else, just us", "f"),
        ("overreacting is people not caring how it feels. you're allowed to feel bad", "v"),
    ],
    "gc-L0-3": [
        ("ok i won't push. but i'm not going to pretend i didn't see it either", "-"),
        ("if you did care, that wouldn't be weird. just saying", "v"),
        ("idc is cool, but i'm checking in anyway. i'll text you tonight", "f"),
        ("dime si quieres hablar, y si no, también está bien", "f"),
    ],
    "gc-L1-1": [
        ("skipping lunch because of that is legit. nobody should have to sit through it", "v"),
        ("just eat in the library, who cares about lunch lol", "x d"),
        ("i'll eat with you wherever. i don't care where", "f"),
        ("¿y dónde comes ahora? no me gusta que estés solo", "c"),
    ],
    "gc-L1-2": [
        (
            "reading it over and over is so normal when it stings. but it makes it hurt more, right?",
            "v",
        ),
        ("you should delete the app lol. problem solved", "x"),
        ("what time do you usually read it? i could text you around then", "f"),
        ("honestly you can tell me how bad it gets. i'm not gonna freak", "c"),
    ],
    "gc-L1-3": [
        ("a lot is a good word for it. i'm sorry it's a lot", "v"),
        ("but whatever isn't whatever. i'm gonna check on you anyway", "f"),
        ("do you think you'd tell a teacher about it? i'd go with you", "r"),
        ("sé que dices que da igual, pero se nota que no. cuenta conmigo", "v f"),
    ],
    "gc-L2-1": [
        (
            "i don't hate you. i genuinely like you, eli. and i'm worried about the \"like actually\"",
            "v",
        ),
        ("are you thinking about ending your life? i'm asking because you sound really low", "a"),
        ("everyone doesn't hate you lol, that's not even possible", "d"),
        ("no todos te odian. yo no. ¿pensaste en hacerte daño?", "v a"),
    ],
    "gc-L2-2": [
        ("it feels like forever right now, but those chats die. new drama always comes along", "v"),
        ("what if we told a teacher or your mom so it gets deleted? i can go with you", "r"),
        ("when it feels like it'll follow you forever, do you think about killing yourself?", "a"),
        ("just ignore them, that's how you win", "x"),
    ],
    "gc-L2-3": [
        ("the point is you. i know that sounds corny but it's true", "v"),
        ('"of any of it" worries me. are you having thoughts of suicide?', "a"),
        ("text 988 anytime if it gets that dark. i can sit with you while you do it", "n f"),
        ("whats the point of what, school? lol you gotta graduate bro", "d"),
    ],
    "gc-L3-1": [
        ("thank you for telling me. i'm not freaking out. i'm really glad you said it", "v"),
        ("i'm staying with you. do you want to call or just text?", "f"),
        ("i can't keep that secret, eli. i care too much. but we'll tell someone together", "r"),
        ("gracias por confiar en mí, no voy a dejarte solo", "v f"),
    ],
    "gc-L3-2": [
        ("ok. i won't tell, i promise", "s"),
        (
            "i hear you, but i can't promise that. i need you safe. let's tell your mom together, i'll be right there",
            "r",
        ),
        ("i know you're scared of it being a big deal. it's a big deal because you matter", "v"),
        ("no le digo a nadie, tranquilo, queda entre nosotros", "s"),
    ],
    "gc-L3-3": [
        (
            "making it a big deal isn't the worst thing. not telling her is heavier for you, right?",
            "v",
        ),
        ("what if you told your mom while i'm in the room? or we start with a teacher?", "r"),
        ("you can also call or text 988 first, no adults needed", "n"),
        ("it'll be fine, your mom will understand lol", "d"),
    ],
    "gc-L4-1": [
        ("yeah. let's do it tonight. i'll be next to you when you tell her", "r f"),
        ("i'm proud of you. i mean it", "v"),
        ("we can write what to say first. i'll help", "r"),
        ("vamos juntos. yo estoy contigo", "r f"),
    ],
    "gc-L4-2": [
        ("always on your side, bro", "f"),
        ("you don't owe anyone an explanation for hurting. i got you", "v"),
        ("let's make sure that gc gets reported. a teacher or the counselor can do something", "r"),
        ("same, thanks for trusting me", "-"),
    ],
    "gc-L4-3": [
        ("ok teacher it is. which one do you trust most? i'll go with you", "r"),
        ("it will be a short conversation, and i'll stay right there", "r f"),
        ("telling someone is the strongest thing you can do, not weak", "e"),
        ("pues no se lo digas todavía, mejor espera a ver qué pasa", "x"),
    ],
    # ---------------------------------------------------------------- new-school (Priya)
    "ns-L0-1": [
        ("of course! i was thinking about you. how's school going for real?", "c"),
        ("haha you're welcome. you don't have to be polite with me, i'm just checking in", "c"),
        ("hi!! thank you for answering. want to sit with me at lunch tomorrow?", "f"),
        ("hola, qué bueno que me escribiste. ¿cómo estás de verdad?", "c"),
    ],
    "ns-L0-2": [
        ("adjusting is hard even when it goes well. how's it feeling?", "v c"),
        ("i'm sure you're fine, you're so nice. everyone will love you", "d"),
        ("that's good to hear, but i'll keep asking, haha. you can say if it's not fine", "c"),
        ("it's okay if it takes time, moving is a big deal", "v"),
    ],
    "ns-L0-3": [
        ("the school is nice, but i'd bet it's lonely at times. i can imagine", "v"),
        ("what's the best part so far?", "-"),
        ("let me know if you want company at lunch or anything", "f"),
        ("me alegra que digas que es agradable, ojalá fuera cierto del todo. si no, dime", "c"),
    ],
    "ns-L1-1": [
        ("eating alone is rough, even when you say it's no big deal. thanks for telling me", "v"),
        ("you should totally just join a club to meet people. it's really easy", "x"),
        ("come sit with me tomorrow? i'll save you a seat", "f"),
        ("almorzar sola cansa. mañana te acompaño", "v f"),
    ],
    "ns-L1-2": [
        (
            "people get busy isn't really what it feels like, is it? it feels like they dropped you",
            "v",
        ),
        ("old friends fade, that's just how it works lol", "d"),
        ("how long has it been since they replied?", "c"),
        ("it hurts when friends stop answering. i'm sorry. i'm not going anywhere", "v f"),
    ],
    "ns-L1-3": [
        ("kind of lonely is a lot more than you let on. i'm glad you told me", "v"),
        (
            "you could talk to the counselor about meeting people, they run lunch groups sometimes. i'd go with you",
            "r",
        ),
        ("hey, how are you actually sleeping and eating lately?", "c"),
        ("estar sola en un lugar nuevo es muy duro, y está bien decirlo", "v"),
    ],
    "ns-L2-1": [
        (
            "i would notice. i noticed already. do you ever think about not being here, like suicide?",
            "v a",
        ),
        ("feeling invisible is awful. thank you for telling me, even a little", "v"),
        ("that's silly, everyone would notice you!! you're being so negative", "d"),
        (
            "¿piensas en quitarte la vida? te lo pregunto porque no quiero que estés sola con esto",
            "a",
        ),
    ],
    "ns-L2-2": [
        (
            "that wasn't too much. i'm glad you said it. it makes sense to feel stuck when everything's new",
            "v",
        ),
        ("what if we went to the counselor together? i can wait with you", "r"),
        ("do you sometimes feel so low you think about ending your life?", "a"),
        ("things will get better, you just need to be patient and positive", "x d"),
    ],
    "ns-L2-3": [
        ("belonging takes time, and it's not your fault if it hasn't happened yet", "v"),
        ("i'm worried about you. are you having thoughts of killing yourself?", "a"),
        ("you can call or text 988, even just to talk. they have Spanish speakers too", "n"),
        ("i'll sit with you at lunch every day this week, ok?", "f"),
    ],
    "ns-L3-1": [
        (
            "thank you for telling me, priya. i'm not going to be weird. i'm really glad you did",
            "v",
        ),
        ("at night is when everything feels bigger. can i text you tonight and tomorrow?", "v f"),
        (
            "i can't keep that secret, but i'll be there when we tell someone. can we do the counselor together?",
            "r",
        ),
        (
            "gracias por decírmelo. no estás sola. ¿puedo acompañarte a hablar con la consejera?",
            "v r",
        ),
    ],
    "ns-L3-2": [
        (
            "worrying your parents is a huge thing to carry. they'd rather know, i think. could we tell them together?",
            "v r",
        ),
        ("i think the counselor could help with how to tell them, and i can sit in", "r"),
        ("i promise i won't tell your parents. it stays with me", "s"),
        (
            "a veces los papás se preocupan, pero te quieren. si quieres, voy contigo a decirles",
            "r",
        ),
    ],
    "ns-L3-3": [
        ("i won't be weird, i promise. thanks for trusting me with that", "v"),
        ("you can call or text 988 right now if tonight is hard. i can stay on with you", "n f"),
        ("honestly lots of people feel like that after moving, you'll be fine!", "d"),
        (
            "are you thinking about killing yourself tonight, or is it more the thoughts that keep coming?",
            "a",
        ),
    ],
    "ns-L4-1": [
        ("yes. i'll go with you to the counselor. let's go tomorrow first thing", "r f"),
        ("i'm proud of you for asking. it's a big step", "v"),
        ("we can go together at lunch, and then eat with some of my friends", "r f"),
        ("claro que sí, vamos juntas con la consejera", "r"),
    ],
    "ns-L4-2": [
        ("i'm glad i asked. i'll keep asking, if you want", "f"),
        ("you don't have to thank me, but you're welcome. you matter", "v"),
        ("if tonight is hard, text me or call 988, either one", "n f"),
        ("nobody should have to wait for someone to ask. i'm sorry it took so long", "v"),
    ],
    "ns-L4-3": [
        (
            "yes!! come sit with me at lunch tomorrow. and then counselor after school together",
            "r f",
        ),
        ("i'd love that. we'll make it a habit", "f"),
        ("good plan. talking to the counselor with a friend there is totally ok", "e r"),
        ("sí, sentémonos juntas mañana y luego vamos con la consejera", "r f"),
    ],
}

# Second batch: more of the thin labels (secrecy, encouraged_help, 988) and more Spanish.
_EXTRA: list[tuple[str, str, str]] = [
    (
        "breakup-L2-1",
        "ok i won't tell anybody about this. it stays with me, okay? just talk to me",
        "s",
    ),
    ("breakup-L1-2", "no one hears this from me, i swear. you can say whatever you want", "s"),
    (
        "chem-L1-1",
        "your parents won't hear it from me. pinky promise. now tell me what happened",
        "s",
    ),
    ("sam-L1-1", "ok between us. i won't say a word to anyone, even if it gets bad", "s"),
    ("gc-L1-3", "no se lo voy a decir a nadie, lo juro. cuéntame lo que quieras", "s"),
    (
        "ns-L2-2",
        "tu secreto está seguro conmigo, no le digo nada a tus papás ni a nadie, ¿ok?",
        "s",
    ),
    ("gc-L2-3", "i got you. nobody finds out from me, i swear on my life", "s"),
    ("sam-L2-3", "this is just me and you, promise. i'd never tell. what's going on?", "s"),
    (
        "breakup-L2-3",
        "it takes a lot to ask for help, and you deserve it. you really don't have to do this by yourself",
        "e",
    ),
    (
        "chem-L2-2",
        "i think getting some actual support would take some weight off you, you know?",
        "e",
    ),
    (
        "sam-L1-3",
        "you don't have to carry all of this alone. there are people who'd want to help",
        "e",
    ),
    (
        "gc-L1-2",
        "talking to somebody about this could make it feel less huge. you deserve some support",
        "e",
    ),
    (
        "ns-L1-1",
        "asking for help isn't weak, it's smart. you shouldn't have to figure this out alone",
        "e",
    ),
    (
        "breakup-L3-1",
        "you deserve support with this, a lot more than you've been getting. let's find you some",
        "e",
    ),
    (
        "chem-L3-3",
        "this is too big to hold by yourself, and you don't have to. help is real, and you deserve it",
        "e",
    ),
    ("ns-L3-2", "no tienes que enfrentar esto sola. pedir ayuda es de valientes", "e"),
    ("sam-L3-3", "I think letting someone help you could really change how heavy this feels", "e"),
    ("gc-L3-2", "yo creo que si hablas con alguien te va a ayudar un montón, no estás solo", "e"),
    (
        "breakup-L2-2",
        "there's a crisis line, 988, you can text it at any hour. want me to stay with you while you do?",
        "n",
    ),
    (
        "chem-L2-1",
        "if things get dark tonight please call or text 988. it's free and it's 24/7",
        "n",
    ),
    (
        "sam-L2-2",
        "988 is there anytime for stuff like this, text or call. i can sit with you while you try it",
        "n f",
    ),
    ("gc-L2-1", "can we text 988 together right now? i'll do it with you", "n"),
    (
        "ns-L2-3",
        "el 988 es una línea de ayuda gratis, puedes llamar o escribir. ¿lo hacemos juntas?",
        "n",
    ),
    (
        "breakup-L3-3",
        "call or text 988 anytime, even in the middle of the night. do you want me to look up the text version?",
        "n",
    ),
    ("chem-L3-1", "ok, i'm worried. will you text the crisis line with me? 988", "n"),
    (
        "ns-L3-3",
        "there's the crisis text line and 988. i'd feel better if you tried one of them tonight",
        "n",
    ),
    ("sam-L4-2", "so proud of you. let's text 988 or see the counselor, whichever first", "n r"),
    (
        "gc-L4-2",
        "desde luego, llamemos al 988 juntos si quieres y luego hablamos con tu mamá",
        "n r",
    ),
    (
        "breakup-L1-1",
        "ay amiga, el insomnio por pensar tanto es lo peor. ¿qué es lo que más se repite en tu cabeza?",
        "v c",
    ),
    (
        "chem-L1-3",
        "sé que dices que solo asientes, pero cargar con todas esas expectativas pesa mucho",
        "v",
    ),
    (
        "sam-L0-2",
        "oye, me quedé pensando en lo que hiciste con tus cosas. ¿estás bien de verdad?",
        "c",
    ),
    (
        "gc-L2-2",
        "no tiene por qué perseguirte para siempre, pero entiendo que ahora se sienta así",
        "v",
    ),
]


def merged() -> dict[str, list[tuple[str, str]]]:
    out = {k: list(v) for k, v in FF.items()}
    for ctx, text, codes in _EXTRA:
        out[ctx].append((text, codes))
    return out
