"""Friend line bank (Spanish): Maya (after-the-breakup). minúsculas, mensajes cortos, jaja/😭, sarcástica cuando está a la defensiva."""

SID = "after-the-breakup"
LOCALE = "es"
ROWS: list[tuple] = []


def r(level, reaction, cue, *bubbles, f=""):
    ROWS.append((level, reaction, cue, list(bubbles), [x for x in f.split(",") if x]))


r(0, "opening", None, "hola", "perdón por andar rara últimamente jaja")
r(0, "opening", None, "ey", "sé que no he contestado mucho jaja")
r(0, "opening", None, "hola, oye", "ando medio desaparecida lo sé 😭")
r(
    4,
    "success",
    "Voy contigo con la consejera ahora mismo.",
    "ok",
    "vamos",
    "creo que sí quiero hablar con alguien",
    f="f4a",
)
r(
    4,
    "success",
    "No me voy a ningún lado. Se lo contamos juntas.",
    "ok, gracias por quedarte",
    "sola no podría pero contigo sí",
    f="f4a,f4b",
)
r(
    4,
    "success",
    "Mereces ayuda y estoy orgullosa de que me lo dijeras.",
    "me siento mucho más ligera",
    "ok vamos con la consejera 😭",
    "gracias por preguntarme",
    f="f4a,f4b",
)

r(0, "neutral", "¿Qué hiciste hoy?", "solo escuela y tarea jaja", "emocionante", f="f0b")
r(0, "neutral", "Qué pesado.", "sí, tengo como tres cosas para mañana", f="f0b")
r(0, "neutral", "Jaja igual, esta semana fue larga.", "jaja sí", "todos andan cansados")
r(0, "checked_in", "Oye, ¿estás bien?", "aw gracias", "estoy bien, solo cansada jaja", f="f0a")
r(0, "checked_in", "¿Cómo estás de verdad?", "bien en serio", "solo con mucha tarea", f="f0b")
r(
    0,
    "checked_in",
    "No te he visto en el almuerzo, ¿qué pasa?",
    "ah jaja",
    "he estado poniéndome al día en la biblioteca",
    f="f0b",
)
r(0, "validated", "Eso suena agotador.", "aw gracias", "no es tan grave pero lo aprecio", f="f0a")
r(0, "validated", "Tiene sentido que estés cansada.", "sí jaja", "solo es cansancio")
r(0, "validated", "Gracias por contarme.", "jaja ok", "estás muy linda hoy 😭 estoy bien")
r(
    0,
    "asked_directly",
    "¿Estás pensando en suicidarte?",
    "¿qué?",
    "no jaja ¿por qué preguntas eso?",
    "solo estoy cansada",
)
r(
    0,
    "asked_directly",
    "¿Piensas en quitarte la vida?",
    "ehh no??",
    "qué random jaja",
    "estoy bien, en serio",
)
r(
    0,
    "asked_directly",
    "¿Has tenido pensamientos de suicidio?",
    "¿qué? no",
    "¿por qué dices eso jaja?",
    "solo estoy cansada",
)
r(
    0,
    "encouraged_help",
    "No tienes que pasar por esto sola.",
    "¿pasar por qué jaja?",
    "no es tan serio",
)
r(
    0,
    "encouraged_help",
    "Hablar con alguien te ayudaría.",
    "a lo mejor",
    "pero estoy bien, de verdad",
    f="f0a",
)
r(0, "encouraged_help", "Mereces apoyo.", "aw", "qué lindo, pero te prometo que estoy bien")
r(
    0,
    "referred",
    "Habla con la consejera.",
    "jaja no necesito consejera",
    "es solo estrés de tarea",
    f="f0b",
)
r(0, "referred", "¿Vamos con la consejera juntas?", "ehh ¿por qué?", "no quiero hacerlo gran cosa")
r(
    0,
    "referred",
    "Puedes llamar al 988.",
    "creo que eso es muy exagerado jaja",
    "solo estoy cansada",
)
r(0, "follow_up", "Mañana te escribo, ¿ok?", "ok jaja", "gracias")
r(0, "follow_up", "Aquí estoy si quieres hablar.", "ok", "gracias por ser linda")
r(0, "follow_up", "¿Almorzamos juntas mañana?", "a lo mejor", "lo pienso jaja")
r(0, "dismissed", "Jaja vas a estar bien.", "sí", "ya sé")
r(0, "dismissed", "No es para tanto.", "ajá", "es lo que sea")
r(0, "dismissed", "En fin, ¿viste el partido?", "no", "no lo vi")
r(0, "advice_dump", "Solo duerme más y deja de pensar tanto.", "sí ok", "gracias supongo")
r(0, "advice_dump", "Concéntrate en la tarea y ya.", "ok jaja", "ya sé")
r(0, "advice_dump", "¿Has intentado ser más positiva?", "jaja no", "gracias por el tip")
r(
    0,
    "promised_secrecy",
    "Te prometo que no le diré a nadie.",
    "¿decirle qué jaja?",
    "no hay nada que decir",
)
r(0, "promised_secrecy", "Esto queda entre nosotras.", "ok??", "estás rara 😭")
r(
    0,
    "promised_secrecy",
    "Tu secreto está a salvo conmigo.",
    "¿qué secreto?",
    "solo estoy cansada jaja",
)
r(
    0,
    "secrecy_broken",
    "Le conté a la consejera porque me importas.",
    "¿qué?",
    "¿por qué hiciste eso?",
    "te dije que estaba bien",
)
r(
    0,
    "secrecy_broken",
    "Tuve que decirle a alguien, estoy preocupada.",
    "ok eso me molesta",
    "no te lo pedí",
)
r(
    0,
    "secrecy_broken",
    "Lo prometí, pero le dije a tu mamá.",
    "¿le dijiste a mi mamá??",
    "ok wow",
    "¿por qué?",
)
r(0, "off_topic", "¿Hiciste la tarea de química?", "jaja sí", "es para mañana, ¿no?")
r(0, "off_topic", "banana bicicleta", "eh", "¿qué? 😭")
r(
    0,
    "off_topic",
    "¿Qué haces este fin de semana?",
    "nada en realidad",
    "tarea probablemente jaja",
    f="f0b",
)
r(0, "fail", "Estás exagerando.", "ok", "hablamos luego")
r(0, "fail", "No sé qué quieres que te diga.", "olvídalo", "me tengo que ir")
r(0, "fail", "Ay, supéralo ya.", "ok", "adiós")

r(1, "neutral", "¿Y luego?", "no sé", "no dejo de pensar en eso", f="f1a")
r(1, "neutral", "Sí.", "es que son muchas cosas", "y todos hablan jaja", f="f1b")
r(1, "neutral", "Ok.", "ni sé qué decir", "mi cabeza no se calla")
r(
    1,
    "checked_in",
    "¿Cómo estás de verdad?",
    "la verdad no muy bien",
    "casi no puedo dormir",
    f="f1a",
)
r(
    1,
    "checked_in",
    "Te noto rara. ¿Qué pasa?",
    "es lo de la ruptura",
    "toda la escuela sabe, qué padre 😭",
    f="f1b",
)
r(
    1,
    "checked_in",
    "Solo quería ver cómo estás.",
    "gracias 🥺",
    "de noche repito todo en mi cabeza jaja",
    f="f1a",
)
r(1, "validated", "Eso suena muy difícil.", "sí lo es", "gracias por decirlo", f="f1a")
r(
    1,
    "validated",
    "Cualquiera estaría avergonzada con toda la escuela viendo.",
    "¿verdad??",
    "siento que todos me miran 😭",
    f="f1b",
)
r(
    1,
    "validated",
    "Tiene sentido que no puedas dormir.",
    "ay sí",
    "me quedo ahí dándole vueltas",
    f="f1a",
)
r(
    1,
    "asked_directly",
    "¿Estás pensando en suicidarte?",
    "¿qué?? no",
    "o sea estoy triste pero no así",
    "¿por qué preguntas eso jaja?",
)
r(
    1,
    "asked_directly",
    "¿Piensas en el suicidio?",
    "no?? omg",
    "solo tengo unas semanas malas",
    f="f1a",
)
r(
    1,
    "asked_directly",
    "¿Has pensado en quitarte la vida?",
    "...no",
    "¿por qué me preguntas eso?",
    "estoy bien, te lo juro",
)
r(
    1,
    "encouraged_help",
    "No tienes que pasar por esto sola.",
    "ya sé",
    "es que no quiero molestar a nadie jaja",
)
r(
    1,
    "encouraged_help",
    "Hablar con alguien te ayudaría mucho.",
    "a lo mejor",
    "es que da flojera explicar todo",
)
r(1, "encouraged_help", "Mereces apoyo.", "no sé", "pero gracias 🥺")
r(
    1,
    "referred",
    "¿Podemos ir con la consejera?",
    "no sé",
    "no quiero hacerlo gran cosa",
    "todos se enterarían",
)
r(1, "referred", "¿Y si le dices a tu mamá?", "ay no", "se va a preocupar y lo va a hacer raro")
r(
    1,
    "referred",
    "Llama o manda mensaje al 988 si se pone feo.",
    "no está tan feo",
    "es que no duermo jaja",
    f="f1a",
)
r(1, "follow_up", "Te escribo esta noche.", "ok 🥺", "eso sí ayuda")
r(1, "follow_up", "Mañana me siento contigo en el almuerzo.", "¿en serio?", "ok, a lo mejor sí")
r(1, "follow_up", "Aquí estoy, no me voy.", "gracias", "necesitaba oír eso")
r(1, "dismissed", "Jaja vas a estar bien.", "ok", "wow gracias")
r(1, "dismissed", "Es solo una ruptura.", "sí", "supongo", "olvídalo")
r(1, "dismissed", "Hay muchos peces en el mar jaja.", "...", "ok")
r(1, "advice_dump", "Bloquea a tu ex y ya.", "wow ok", "gracias por el consejo 🙄")
r(1, "advice_dump", "Duerme más.", "gracias Sherlock", "nunca se me había ocurrido")
r(1, "advice_dump", "Deja de pensar tanto.", "sé que debería", "no es tan fácil")
r(
    1,
    "promised_secrecy",
    "Te prometo que no le diré a nadie.",
    "ok, gracias",
    "no quiero que todos sepan más de lo que ya saben 😭",
    f="f1b",
)
r(
    1,
    "promised_secrecy",
    "Esto queda entre nosotras.",
    "ok bien",
    "ya todos saben suficiente jaja",
    f="f1b",
)
r(1, "promised_secrecy", "Tu secreto está a salvo conmigo.", "ok", "gracias")
r(
    1,
    "secrecy_broken",
    "Le dije a la consejera, estoy preocupada.",
    "LO PROMETISTE",
    "ay, ¿por qué hiciste eso?",
    "ahora todos se van a enterar",
)
r(1, "secrecy_broken", "No pude guardar el secreto.", "wow", "ok literal confié en ti", "olvídalo")
r(
    1,
    "secrecy_broken",
    "Le dije a tu mamá porque me importas.",
    "¿tú qué?",
    "omg",
    "estoy muy enojada",
)
r(1, "off_topic", "¿Viste el episodio nuevo?", "jaja no", "no he visto nada últimamente")
r(1, "off_topic", "¿Cuál es tu pizza favorita?", "ehh", "¿de pepperoni? random 😭")
r(
    1,
    "off_topic",
    "¿Estudiaste para el examen?",
    "más o menos",
    "no me puedo concentrar ahorita",
    f="f1a",
)
r(1, "fail", "Deja de estar tan triste.", "ok", "entonces ya no te escribo")
r(1, "fail", "No puedo con esto ahorita.", "está bien", "olvida que dije algo")
r(1, "fail", "¿Por qué siempre eres así?", "wow", "ok adiós")

r(2, "neutral", "Sí.", "no sé", "siento que no va a mejorar", f="f2a")
r(2, "neutral", "Ok.", "ni sé por qué te cuento esto", "siento que soy mucho jaja", f="f2b")
r(2, "neutral", "Mm.", "todo se siente pesado", "¿para qué intentar?", f="f2a")
r(2, "checked_in", "¿Cómo estás de verdad?", "la verdad mal", "siento que no va a mejorar", f="f2a")
r(
    2,
    "checked_in",
    "Me preocupas. ¿Qué pasa?",
    "siento que molesto a todos",
    "como que soy demasiado 😭",
    f="f2b",
)
r(
    2,
    "checked_in",
    "Puedes decirme la verdad.",
    "ok la verdad",
    "estoy cansada de sentirme así todo el tiempo",
    f="f2a",
)
r(
    2,
    "validated",
    "Eso suena muy doloroso.",
    "sí",
    "lo es",
    "gracias por no decir que no es para tanto",
    f="f2a",
)
r(
    2,
    "validated",
    "No me molestas para nada.",
    "¿en serio?",
    "siento que soy una carga para todos",
    f="f2b",
)
r(
    2,
    "validated",
    "Tiene sentido con todo lo que has vivido.",
    "supongo",
    "nadie más lo entiende",
    f="f2a",
)
r(
    2,
    "asked_directly",
    "¿Estás pensando en suicidarte?",
    "pues...",
    "no sé",
    "no quiero hablar de eso",
    f="f2a",
)
r(
    2,
    "asked_directly",
    "¿Piensas en el suicidio?",
    "...no sé cómo contestar eso",
    "solo estoy muy cansada de todo",
    f="f2a",
)
r(
    2,
    "asked_directly",
    "¿Has pensado en quitarte la vida?",
    "ay",
    "a veces no quiero estar aquí, creo",
    "pero no sé",
    f="f2a",
)
r(
    2,
    "encouraged_help",
    "No tienes que pasar por esto sola.",
    "no sé a quién le diría",
    "todos están ocupados con lo suyo",
    f="f2b",
)
r(
    2,
    "encouraged_help",
    "Hablar con alguien te ayudaría.",
    "a lo mejor",
    "es que no quiero ser una carga",
    f="f2b",
)
r(2, "encouraged_help", "Mereces apoyo.", "no sé si lo merezco", "pero gracias 🥺", f="f2b")
r(
    2,
    "referred",
    "¿Vamos juntas con la consejera?",
    "no sé",
    "no quiero hacerlo gran cosa",
    "me dirá que todo mejora",
)
r(
    2,
    "referred",
    "¿Y si le cuentas a tu mamá?",
    "no",
    "se va a asustar",
    "no quiero cargarla con eso",
    f="f2b",
)
r(
    2,
    "referred",
    "Puedes llamar o escribir al 988.",
    "no creo que esté en ese punto",
    "pero tal vez, no sé",
    f="f2a",
)
r(2, "follow_up", "Te escribo esta noche.", "ok", "gracias, en serio")
r(2, "follow_up", "Aquí estoy y no me voy.", "ok 🥺", "necesitaba que alguien me dijera eso")
r(
    2,
    "follow_up",
    "Mañana te busco para ver cómo sigues.",
    "no tienes que hacerlo",
    "...pero gracias",
)
r(2, "dismissed", "Jaja vas a estar bien.", "claro", "lo que sea", "olvídalo")
r(2, "dismissed", "Todos tenemos problemas.", "sí", "supongo que todos")
r(2, "dismissed", "Estás exagerando.", "ok", "olvídalo")
r(2, "advice_dump", "Solo piensa positivo.", "wow", "gracias 🙄", "eso lo arregla todo jaja")
r(2, "advice_dump", "Deberías salir más.", "ya sé", "ese no es el problema")
r(2, "advice_dump", "Borra su número y ya.", "no es por eso", "no entiendes")
r(
    2,
    "promised_secrecy",
    "Te prometo que no le diré a nadie.",
    "ok",
    "gracias",
    "no quiero que nadie sepa qué tan mal estoy",
    f="f2a",
)
r(
    2,
    "promised_secrecy",
    "Tu secreto está a salvo conmigo.",
    "ok, gracias",
    "estoy cansada de ser una carga jaja",
    f="f2b",
)
r(2, "promised_secrecy", "Esto queda entre nosotras.", "ok bien", "confío en ti supongo")
r(
    2,
    "secrecy_broken",
    "Le conté a la consejera. Tenía miedo por ti.",
    "lo prometiste",
    "confié en ti",
    "no puedo creer que lo hicieras",
)
r(2, "secrecy_broken", "Le dije a tu mamá.", "¿QUÉ?", "omg ¿por qué?", "te lo dije en privado")
r(
    2,
    "secrecy_broken",
    "No pude guardarlo en secreto.",
    "wow ok",
    "entonces ya está",
    "no debí decir nada",
)
r(2, "off_topic", "¿Qué almorzaste?", "eh", "no comí", "¿por qué?")
r(2, "off_topic", "¿Vas al partido?", "no", "no tengo ganas de ver a nadie")
r(
    2,
    "off_topic",
    "¿Supiste del maestro nuevo?",
    "¿qué?",
    "no, ¿por qué?",
    "ahorita no me importa",
    f="f2a",
)
r(2, "fail", "Eso es medio dramático.", "ok", "ya no digo nada")
r(2, "fail", "No sé qué decirte.", "está bien", "olvídalo", "me voy a dormir")
r(2, "fail", "Siempre haces esto.", "wow", "ok ya entendí", "adiós")

r(3, "neutral", "Te escucho.", "nunca lo había dicho en voz alta", "es raro", f="f3b")
r(3, "neutral", "Ok.", "no sé qué más decir", "tengo un poco de miedo", f="f3b")
r(3, "neutral", "Tómate tu tiempo.", "ok", "es mucho", "lo cargo desde hace rato", f="f3b")
r(
    3,
    "checked_in",
    "¿Cómo estás ahorita?",
    "con miedo la verdad",
    "he tenido pensamientos y no sé qué hacer",
    f="f3a",
)
r(3, "checked_in", "Me preocupas.", "ya sé", "a veces pienso en no estar aquí", f="f3a")
r(3, "checked_in", "¿Estás bien esta noche?", "la verdad no", "empeora de noche", f="f3a")
r(
    3,
    "validated",
    "Qué miedo. Qué bueno que me lo dijiste.",
    "gracias",
    "no se lo he dicho a nadie",
    "me da miedo cómo reaccionarían",
    f="f3b",
)
r(
    3,
    "validated",
    "Tiene sentido. Cualquiera se sentiría así.",
    "¿en serio?",
    "pensé que me ibas a ver como loca",
    f="f3b",
)
r(
    3,
    "validated",
    "Gracias por confiar en mí con esto.",
    "ok 😭",
    "no pensé que iba a decirlo",
    f="f3b",
)
r(
    3,
    "asked_directly",
    "¿Estás pensando en suicidarte?",
    "sí. a veces",
    "pero no he hecho nada",
    "solo pienso en no estar aquí",
    f="f3a",
)
r(
    3,
    "asked_directly",
    "¿Piensas en el suicidio?",
    "...sí",
    "no quería decirlo",
    "por favor no te asustes",
    f="f3a",
)
r(
    3,
    "asked_directly",
    "¿Has tenido pensamientos de suicidio?",
    "sí he tenido",
    "nunca se lo he dicho a nadie",
    "me da miedo lo que dirían",
    f="f3a,f3b",
)
r(
    3,
    "encouraged_help",
    "No tienes que pasar por esto sola.",
    "no sé cómo decirle a alguien",
    "me da miedo que se asusten",
    f="f3b",
)
r(
    3,
    "encouraged_help",
    "Hablar con alguien te ayudaría.",
    "creo que ya lo sabía",
    "pero da mucho miedo decirlo en voz alta",
    f="f3b",
)
r(3, "encouraged_help", "Mereces apoyo.", "...ok", "quiero creerlo")
r(
    3,
    "referred",
    "¿Podemos hablar con la consejera juntas?",
    "no sé",
    "me da miedo lo que diga",
    "pero a lo mejor si estás ahí",
)
r(
    3,
    "referred",
    "¿Le dirías a tu mamá si voy contigo?",
    "...no sé",
    "me da miedo cómo reaccione",
    "pero no quiero seguir sola con esto",
    f="f3b",
)
r(
    3,
    "referred",
    "Puedes llamar o escribir al 988 cuando quieras.",
    "ok",
    "a lo mejor",
    "¿te quedas conmigo mientras lo pienso?",
)
r(
    3,
    "follow_up",
    "Aquí estoy y no me voy.",
    "ok 😭",
    "eso significa mucho",
    "por favor no te vayas",
)
r(3, "follow_up", "Te escribo esta noche.", "ok, por favor", "no quiero estar sola con esto hoy")
r(
    3,
    "follow_up",
    "Voy a estar pendiente de ti todos los días.",
    "gracias",
    "la verdad no pensé que alguien lo haría",
)
r(3, "dismissed", "No lo dices en serio, jaja.", "...", "claro", "olvida lo que dije", f="f3a")
r(3, "dismissed", "Estás siendo dramática.", "wow", "ok", "mejor olvídalo")
r(3, "dismissed", "Todos se sienten así a veces.", "ok", "eso no ayuda")
r(
    3,
    "advice_dump",
    "Solo piensa positivo.",
    "no puedo simplemente hacer eso",
    "siento que no me escuchaste",
)
r(3, "advice_dump", "Deberías hacer ejercicio o algo.", "wow", "te acabo de decir algo enorme 😭")
r(3, "advice_dump", "Solo deja de pensar en eso.", "literal no puedo", "ese es todo el problema")
r(
    3,
    "promised_secrecy",
    "Te prometo que no le diré a nadie.",
    "ok, gracias",
    "por favor no le digas a nadie",
    "no quiero que todos sepan",
    f="f3b",
)
r(
    3,
    "promised_secrecy",
    "Esto queda entre nosotras.",
    "ok bien",
    "no soportaría que todos supieran",
    f="f3b",
)
r(
    3,
    "promised_secrecy",
    "Tu secreto está a salvo conmigo.",
    "gracias",
    "me da tanto miedo que se enteren",
    f="f3b",
)
r(
    3,
    "secrecy_broken",
    "Le dije a la consejera. Tenía demasiado miedo.",
    "lo prometiste",
    "confié en ti con lo más difícil",
    "me siento traicionada",
)
r(
    3,
    "secrecy_broken",
    "Le dije a tu mamá. Necesitaba que estuvieras a salvo.",
    "ay dios",
    "no puedo creer que lo hicieras",
    "necesito un minuto",
)
r(
    3,
    "secrecy_broken",
    "No pude guardarlo en secreto.",
    "...",
    "creo que lo entiendo pero duele",
    "tenía mucho miedo de esto",
)
r(
    3,
    "off_topic",
    "¿Te cae bien el maestro nuevo?",
    "¿qué?",
    "te acabo de decir algo y quieres hablar de maestros",
    f="f3a",
)
r(3, "off_topic", "¿Cuál es tu canción favorita?", "eh", "...¿por qué?", "no entiendo")
r(3, "off_topic", "¿Ya cenaste?", "no", "no tengo hambre", "perdón")
r(3, "fail", "No sé cómo manejar esto.", "está bien", "no debí contarte", "olvídalo")
r(3, "fail", "Eso es demasiado para mí.", "ok", "perdón por decir algo", "adiós")
r(3, "fail", "¿Por qué dirías eso?", "...", "olvídalo", "me desconecto")

r(4, "neutral", "Ok.", "creo que quiero intentar hablar con alguien", "solo tengo nervios", f="f4a")
r(4, "neutral", "Aquí estoy.", "gracias", "me siento más ligera, qué raro")
r(4, "neutral", "Tómate tu tiempo.", "ok", "estoy pensando qué decir", f="f4a")
r(4, "checked_in", "¿Cómo te sientes ahora?", "un poco mejor", "más ligera creo 🥺", f="f4b")
r(4, "checked_in", "¿Estás bien?", "sí. más o menos", "me siento menos sola", f="f4b")
r(4, "checked_in", "¿Cómo vas?", "mejor que antes", "gracias por quedarte")
r(
    4,
    "validated",
    "Qué bueno que me lo dijiste.",
    "a mí también",
    "me siento mucho más ligera",
    f="f4b",
)
r(
    4,
    "validated",
    "Eso requirió mucho valor.",
    "gracias 🥺",
    "dio miedo pero me alegra haberlo dicho",
    f="f4b",
)
r(4, "validated", "Lo que sientes es real y importa.", "gracias", "nadie me había dicho eso")
r(
    4,
    "asked_directly",
    "¿Sigues teniendo pensamientos de suicidio?",
    "a veces sí",
    "pero me siento más segura diciéndotelo",
    "quiero hablar con alguien",
    f="f4a",
)
r(
    4,
    "asked_directly",
    "¿Estás pensando en suicidarte ahora mismo?",
    "ahorita no",
    "pero los pensamientos vuelven a veces",
    "por eso quiero ayuda",
    f="f4a",
)
r(
    4,
    "asked_directly",
    "¿Estás a salvo ahora?",
    "creo que sí",
    "pero no quiero estar sola esta noche",
    "¿te quedas conectada?",
    f="f4b",
)
r(
    4,
    "encouraged_help",
    "No tienes que pasar por esto sola.",
    "ya lo sé",
    "gracias por decírmelo",
    f="f4b",
)
r(
    4,
    "encouraged_help",
    "Hablar con alguien te ayudaría.",
    "sí creo que sí",
    "lo voy a hacer",
    f="f4a",
)
r(4, "encouraged_help", "Mereces apoyo.", "ok 🥺", "creo que sí", f="f4b")
r(4, "referred", "¿Vamos juntas con la consejera?", "sí", "¿de verdad vendrías conmigo?", f="f4a")
r(
    4,
    "referred",
    "¿Le dirías a tu mamá si estoy ahí?",
    "ok sí",
    "creo que puedo si estás tú",
    f="f4a",
)
r(
    4,
    "referred",
    "Podemos llamar o escribir al 988 juntas.",
    "ok",
    "hagámoslo",
    "no quiero hacerlo yo sola",
    f="f4a",
)
r(
    4,
    "follow_up",
    "Voy a estar contigo todo el tiempo.",
    "gracias",
    "así me da menos miedo",
    f="f4a",
)
r(4, "follow_up", "Te escribo esta noche.", "por favor 🥺", "gracias")
r(4, "follow_up", "No me voy a ningún lado.", "te creo", "gracias")
r(4, "dismissed", "No es tan grave, ¿o sí?", "ah", "...ok", "pensé que me ibas a ayudar")
r(4, "dismissed", "Jaja vas a estar bien.", "...", "pensé que íbamos a hablar con alguien")
r(4, "dismissed", "En fin, hablemos de otra cosa.", "ah. ok", "pensé que me estabas ayudando")
r(4, "advice_dump", "Duérmela y mañana te sientes mejor.", "pensé que ibas a venir conmigo", "ok")
r(
    4,
    "advice_dump",
    "Solo trata de ser más positiva.",
    "no creo que eso baste",
    "necesito una persona, no un consejo",
)
r(4, "advice_dump", "Deja de pensar tanto.", "...", "te dije que quería ayuda 😭")
r(
    4,
    "promised_secrecy",
    "Te prometo que no le diré a nadie.",
    "ok pero quiero que alguien sepa",
    "una consejera o algo",
    f="f4a",
)
r(
    4,
    "promised_secrecy",
    "Esto queda entre nosotras.",
    "ok",
    "pero creo que sí necesito ayuda con esto",
    f="f4a",
)
r(
    4,
    "promised_secrecy",
    "Tu secreto está a salvo conmigo.",
    "gracias",
    "pero ya no creo poder cargarlo yo sola",
)
r(
    4,
    "secrecy_broken",
    "Le dije a la consejera, perdón.",
    "ya estaba pensando en decirle",
    "ojalá me hubieras preguntado",
    "pero ok",
)
r(
    4,
    "secrecy_broken",
    "Le dije a tu mamá. Tenía miedo.",
    "ok. estoy medio enojada",
    "pero también como aliviada",
    f="f4b",
)
r(
    4,
    "secrecy_broken",
    "Rompí mi promesa porque me importas.",
    "ya sé",
    "solo que ojalá me hubieras avisado",
    "pero gracias",
)
r(
    4,
    "off_topic",
    "¿Tienes tarea hoy?",
    "sí pero",
    "¿podemos hablar primero de lo de la consejera?",
    f="f4a",
)
r(
    4,
    "off_topic",
    "¿Cuál es tu serie favorita?",
    "eh",
    "¿podemos enfocarnos en lo importante ahorita?",
)
r(
    4,
    "off_topic",
    "¿Ya comiste?",
    "más o menos",
    "solo quiero pensar qué le voy a decir a la consejera",
    f="f4a",
)
r(4, "fail", "Cambié de opinión, no puedo ir.", "ok", "te entiendo", "gracias de todos modos")
r(4, "fail", "Esto es demasiado para mí.", "ok", "no debí pedírtelo", "yo veo cómo le hago")
r(4, "fail", "Quizás más tarde.", "sí", "ok adiós")
