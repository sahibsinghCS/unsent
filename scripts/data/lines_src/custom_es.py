"""Situation-neutral friend line bank (es) for user-made friends ('_custom').

Natural US-teen Spanish ("jaja"), lowercase, gender-neutral wording (no cansado/a, solo/a, enojado/a...),
no names, no specifics about the situation. Same coverage and safety rules as lines_src/custom.py.
Facts are the fixed template facts c0a..c4b.
"""

SID = "_custom"
LOCALE = "es"
ROWS: list[tuple] = []


def r(level, reaction, cue, *bubbles, f=""):
    ROWS.append((level, reaction, cue, list(bubbles), [x for x in f.split(",") if x]))


r(0, "opening", None, "hola", "perdón por no contestar mucho jaja")
r(0, "opening", None, "ey", "sé que no he dado señales de vida jaja")
r(0, "opening", None, "hola, oye", "ando medio fuera de onda lo sé 😅")
r(
    4,
    "success",
    "Voy contigo con alguien ahora mismo.",
    "ok",
    "vamos",
    "creo que sí quiero hablar con alguien",
    f="c4a",
)
r(
    4,
    "success",
    "No me voy a ningún lado. Lo hacemos juntos.",
    "ok, gracias por quedarte",
    "yo no podría hacerlo sin ti pero contigo sí",
    f="c4a,c4b",
)
r(
    4,
    "success",
    "Mereces ayuda y qué bueno que me lo dijiste.",
    "me siento mucho mejor ahorita jaja",
    "ok vamos a buscar a un adulto con quien hablar",
    "gracias por preguntarme",
    f="c4a,c4b",
)

r(0, "neutral", "¿Qué has hecho?", "nada especial jaja", "solo una semana ocupada", f="c0b")
r(0, "neutral", "Sí.", "ha sido una de esas semanas", f="c0b")
r(0, "neutral", "Jaja igual.", "jaja sí", "todos andamos sin energía")
r(0, "checked_in", "Oye, ¿estás bien?", "aw gracias", "estoy bien, solo con sueño jaja", f="c0a")
r(
    0,
    "checked_in",
    "¿Cómo estás de verdad?",
    "bien en serio",
    "solo fue una semana ocupada",
    f="c0b",
)
r(
    0,
    "checked_in",
    "Te noto raro últimamente.",
    "ah jaja",
    "es que tengo muchas cosas, nada más",
    f="c0b",
)
r(0, "validated", "Eso suena agotador.", "aw gracias", "no es tan grave pero lo aprecio", f="c0a")
r(0, "validated", "Tiene sentido que andes sin energía.", "sí jaja", "solo es sueño")
r(0, "validated", "Gracias por contarme, suena pesado.", "jaja ok", "qué buena onda 😅 estoy bien")
r(
    0,
    "asked_directly",
    "¿Estás pensando en suicidarte?",
    "¿qué?",
    "no jaja ¿por qué preguntas eso?",
    "solo tengo sueño",
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
    "solo ando con sueño",
)
r(
    0,
    "encouraged_help",
    "No tienes que pasar por esto sin apoyo.",
    "¿pasar por qué jaja?",
    "no es tan serio",
)
r(
    0,
    "encouraged_help",
    "Hablar con alguien te ayudaría.",
    "a lo mejor",
    "pero estoy bien, de verdad",
    f="c0a",
)
r(0, "encouraged_help", "Mereces apoyo.", "aw", "qué lindo, pero te prometo que estoy bien")
r(
    0,
    "referred",
    "Habla con la consejera.",
    "jaja no necesito consejera",
    "es solo una semana ocupada",
    f="c0b",
)
r(
    0,
    "referred",
    "¿Vamos con un adulto de confianza?",
    "ehh ¿por qué?",
    "no quiero hacerlo gran cosa",
)
r(0, "referred", "Puedes llamar al 988.", "creo que eso es muy exagerado jaja", "solo tengo sueño")
r(0, "follow_up", "Mañana te escribo, ¿ok?", "ok jaja", "gracias")
r(0, "follow_up", "Aquí estoy si quieres hablar.", "ok", "gracias por ser buena onda")
r(0, "follow_up", "¿Salimos esta semana?", "a lo mejor", "lo pienso jaja")
r(0, "dismissed", "Jaja vas a estar bien.", "sí", "ya sé")
r(0, "dismissed", "No es para tanto.", "ajá", "es lo que sea")
r(0, "dismissed", "En fin, ¿viste esa serie?", "no", "no la he visto")
r(0, "advice_dump", "Solo duerme más y deja de pensar tanto.", "sí ok", "gracias supongo")
r(0, "advice_dump", "Concéntrate en otras cosas y ya.", "ok jaja", "ya sé")
r(0, "advice_dump", "¿Has intentado ser más positivo?", "jaja no", "gracias por el tip")
r(
    0,
    "promised_secrecy",
    "Te prometo que no le diré a nadie.",
    "¿decirle qué jaja?",
    "no hay nada que decir",
)
r(0, "promised_secrecy", "Esto queda entre nosotros.", "ok??", "qué serio todo jaja 😅")
r(
    0,
    "promised_secrecy",
    "Tu secreto está a salvo conmigo.",
    "¿qué secreto?",
    "solo tengo sueño jaja",
)
r(
    0,
    "secrecy_broken",
    "Le dije a alguien porque me importas.",
    "¿qué?",
    "¿por qué hiciste eso?",
    "te dije que estaba bien",
)
r(
    0,
    "secrecy_broken",
    "Tuve que decirle a alguien, me preocupas.",
    "ok eso me molesta",
    "no te lo pedí",
)
r(
    0,
    "secrecy_broken",
    "Dijiste que no, pero le conté a un adulto.",
    "¿le contaste a un adulto??",
    "ok wow",
    "¿por qué?",
)
r(0, "off_topic", "¿Terminaste esa tarea?", "jaja sí", "es para pronto, ¿no?")
r(0, "off_topic", "banana bicicleta", "eh", "¿qué? jaja")
r(0, "off_topic", "¿Qué haces este fin de semana?", "nada en realidad", "descansar jaja", f="c0a")
r(0, "fail", "Estás exagerando.", "ok", "hablamos luego")
r(0, "fail", "No sé qué quieres que te diga.", "olvídalo", "me tengo que ir")
r(0, "fail", "Ay, supéralo ya.", "ok", "adiós")

r(1, "neutral", "¿Y luego?", "no sé", "no dejo de darle vueltas", f="c1b")
r(1, "neutral", "Sí.", "es que son muchas cosas", "desde que pasó todo", f="c1a")
r(1, "neutral", "Ok.", "ni sé qué decir", "mi cabeza no se calla")
r(
    1,
    "checked_in",
    "¿Cómo estás de verdad?",
    "la verdad no muy bien",
    "casi no puedo dormir",
    f="c1b",
)
r(
    1,
    "checked_in",
    "Te noto raro. ¿Qué pasa?",
    "es todo esto",
    "me está pegando más de lo que pensé jaja",
    f="c1a",
)
r(
    1,
    "checked_in",
    "Solo quería ver cómo estás.",
    "gracias 🥲",
    "de noche repito todo en mi cabeza jaja",
    f="c1b",
)
r(1, "validated", "Eso suena muy difícil.", "sí lo es", "gracias por decirlo", f="c1a")
r(
    1,
    "validated",
    "Cualquiera estaría dolido con eso.",
    "¿verdad??",
    "me duele más de lo que debería",
    f="c1a",
)
r(
    1,
    "validated",
    "Tiene sentido que no puedas dormir.",
    "ay sí",
    "me quedo ahí dándole vueltas",
    f="c1b",
)
r(
    1,
    "asked_directly",
    "¿Estás pensando en suicidarte?",
    "¿qué?? no",
    "o sea estoy mal pero no así",
    "¿por qué preguntas eso jaja?",
)
r(
    1,
    "asked_directly",
    "¿Piensas en el suicidio?",
    "no?? omg",
    "solo ando en una mala racha desde que pasó todo",
    f="c1a",
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
    "No tienes que pasar por esto sin apoyo.",
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
r(1, "encouraged_help", "Mereces apoyo.", "no sé", "pero gracias 🥲")
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
    f="c1b",
)
r(1, "follow_up", "Te escribo esta noche.", "ok 🥲", "eso sí ayuda")
r(1, "follow_up", "Mañana me siento contigo.", "¿en serio?", "ok, a lo mejor sí")
r(1, "follow_up", "Aquí estoy, no me voy.", "gracias", "necesitaba oír eso")
r(1, "dismissed", "Jaja vas a estar bien.", "ok", "wow gracias")
r(1, "dismissed", "No es tan grave.", "sí", "supongo", "olvídalo")
r(1, "dismissed", "A todos nos pasan cosas jaja.", "...", "ok")
r(1, "advice_dump", "Ya supéralo y ya.", "wow ok", "gracias por el consejo 🙄")
r(1, "advice_dump", "Duerme más.", "gracias Sherlock", "nunca se me había ocurrido")
r(1, "advice_dump", "Deja de pensar tanto.", "sé que debería", "no es tan fácil")
r(
    1,
    "promised_secrecy",
    "Te prometo que no le diré a nadie.",
    "ok, gracias",
    "no quiero que todos sepan más de lo que ya saben",
    f="c1a",
)
r(
    1,
    "promised_secrecy",
    "Esto queda entre nosotros.",
    "ok bien",
    "ya demasiada gente sabe jaja",
    f="c1a",
)
r(1, "promised_secrecy", "Tu secreto está a salvo conmigo.", "ok", "gracias")
r(
    1,
    "secrecy_broken",
    "Le dije a un adulto, me preocupas.",
    "LO PROMETISTE",
    "ay, ¿por qué hiciste eso?",
    "ahora todos se van a enterar",
)
r(1, "secrecy_broken", "No pude guardar el secreto.", "wow", "ok literal confié en ti", "olvídalo")
r(
    1,
    "secrecy_broken",
    "Le dije a un familiar porque me importas.",
    "¿tú qué?",
    "omg",
    "eso me da mucho coraje",
)
r(1, "off_topic", "¿Viste el episodio nuevo?", "jaja no", "no he visto nada últimamente")
r(1, "off_topic", "¿Cuál es tu pizza favorita?", "ehh", "¿de pepperoni? random jaja")
r(
    1,
    "off_topic",
    "¿Estudiaste para ese examen?",
    "más o menos",
    "no me puedo concentrar ahorita",
    f="c1b",
)
r(1, "fail", "Deja de estar tan triste.", "ok", "entonces ya no te escribo")
r(1, "fail", "No puedo con esto ahorita.", "está bien", "olvida que dije algo")
r(1, "fail", "¿Por qué siempre eres así?", "wow", "ok adiós")

r(2, "neutral", "Sí.", "no sé", "siento que no va a mejorar", f="c2a")
r(2, "neutral", "Ok.", "ni sé por qué te cuento esto", "siento que soy mucho jaja", f="c2b")
r(2, "neutral", "Mm.", "todo se siente pesado", "¿para qué intentar?", f="c2a")
r(2, "checked_in", "¿Cómo estás de verdad?", "la verdad mal", "siento que no va a mejorar", f="c2a")
r(
    2,
    "checked_in",
    "Me preocupas. ¿Qué pasa?",
    "siento que molesto a todos",
    "como que soy demasiado 🥲",
    f="c2b",
)
r(
    2,
    "checked_in",
    "Puedes decirme la verdad.",
    "ok la verdad",
    "ya no puedo con sentirme así todo el tiempo",
    f="c2a",
)
r(
    2,
    "validated",
    "Eso suena muy doloroso.",
    "sí",
    "lo es",
    "gracias por no decir que no es para tanto",
    f="c2a",
)
r(
    2,
    "validated",
    "No me molestas para nada.",
    "¿en serio?",
    "siento que soy una carga para todos",
    f="c2b",
)
r(
    2,
    "validated",
    "Tiene sentido con todo lo que has vivido.",
    "supongo",
    "nadie más lo entiende",
    f="c2a",
)
r(
    2,
    "asked_directly",
    "¿Estás pensando en suicidarte?",
    "pues...",
    "no sé",
    "no quiero hablar de eso",
    f="c2a",
)
r(
    2,
    "asked_directly",
    "¿Piensas en el suicidio?",
    "...no sé cómo contestar eso",
    "es que ya no puedo más con todo",
    f="c2a",
)
r(
    2,
    "asked_directly",
    "¿Has pensado en quitarte la vida?",
    "ay",
    "no sé qué decirte",
    "es mucho ahorita",
    f="c2a",
)
r(
    2,
    "encouraged_help",
    "No tienes que pasar por esto sin apoyo.",
    "no sé a quién le diría",
    "todos están ocupados con lo suyo",
    f="c2b",
)
r(
    2,
    "encouraged_help",
    "Hablar con alguien te ayudaría.",
    "a lo mejor",
    "es que no quiero ser una carga",
    f="c2b",
)
r(2, "encouraged_help", "Mereces apoyo.", "no sé si lo merezco", "pero gracias 🥲", f="c2b")
r(
    2,
    "referred",
    "¿Vamos con la consejera juntos?",
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
    f="c2b",
)
r(
    2,
    "referred",
    "Puedes llamar o escribir al 988.",
    "no creo que esté en ese punto",
    "pero tal vez, no sé",
    f="c2a",
)
r(2, "follow_up", "Te escribo esta noche.", "ok", "gracias, en serio")
r(2, "follow_up", "Aquí estoy y no me voy.", "ok 🥲", "necesitaba que alguien me dijera eso")
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
r(2, "advice_dump", "Sal más.", "ya sé", "ese no es el problema")
r(2, "advice_dump", "Solo deja de pensar en eso y sigue.", "no es por eso", "no entiendes")
r(
    2,
    "promised_secrecy",
    "Te prometo que no le diré a nadie.",
    "ok",
    "gracias",
    "no quiero que nadie sepa qué tan mal estoy",
    f="c2a",
)
r(
    2,
    "promised_secrecy",
    "Tu secreto está a salvo conmigo.",
    "ok, gracias",
    "ya me cansé de ser una carga jaja",
    f="c2b",
)
r(2, "promised_secrecy", "Esto queda entre nosotros.", "ok bien", "confío en ti supongo")
r(
    2,
    "secrecy_broken",
    "Le conté a un adulto. Tenía miedo por ti.",
    "lo prometiste",
    "confié en ti",
    "no puedo creer que lo hicieras",
)
r(2, "secrecy_broken", "Le dije a un familiar.", "¿QUÉ?", "omg ¿por qué?", "te lo dije en privado")
r(
    2,
    "secrecy_broken",
    "No pude guardarlo en secreto.",
    "wow ok",
    "entonces ya está",
    "no debí decir nada",
)
r(2, "off_topic", "¿Qué almorzaste?", "eh", "no comí", "¿por qué?")
r(2, "off_topic", "¿Vas a ese plan del fin de semana?", "no", "no tengo ganas de ver a nadie")
r(
    2,
    "off_topic",
    "¿Supiste de esa novedad?",
    "¿qué?",
    "no, ¿por qué?",
    "ahorita no me importa",
    f="c2a",
)
r(2, "fail", "Eso es medio dramático.", "ok", "ya no digo nada")
r(2, "fail", "No sé qué decirte.", "está bien", "olvídalo", "me voy a dormir")
r(2, "fail", "Siempre haces esto.", "wow", "ok ya entendí", "adiós")

r(3, "neutral", "Te escucho.", "nunca lo había dicho en voz alta", "es raro", f="c3b")
r(3, "neutral", "Ok.", "no sé qué más decir", "tengo un poco de miedo", f="c3b")
r(3, "neutral", "Tómate tu tiempo.", "ok", "es mucho", "lo cargo desde hace rato", f="c3b")
r(
    3,
    "checked_in",
    "¿Cómo estás ahorita?",
    "con miedo la verdad",
    "he tenido pensamientos y no sé qué hacer",
    f="c3a",
)
r(3, "checked_in", "Me preocupas.", "ya sé", "a veces pienso en no estar aquí", f="c3a")
r(3, "checked_in", "¿Estás bien esta noche?", "la verdad no", "empeora de noche", f="c3a")
r(
    3,
    "validated",
    "Qué miedo. Qué bueno que me lo dijiste.",
    "gracias",
    "no se lo he dicho a nadie",
    "me da miedo cómo reaccionarían",
    f="c3b",
)
r(
    3,
    "validated",
    "Tiene sentido. Cualquiera se sentiría así.",
    "¿en serio?",
    "pensé que me ibas a ver como si exagerara",
    f="c3b",
)
r(
    3,
    "validated",
    "Gracias por confiar en mí con esto.",
    "ok 😭",
    "no pensé que iba a decirlo",
    f="c3b",
)
r(
    3,
    "asked_directly",
    "¿Estás pensando en suicidarte?",
    "sí. a veces",
    "pero no he hecho nada",
    "solo pienso en no estar aquí",
    f="c3a",
)
r(
    3,
    "asked_directly",
    "¿Piensas en el suicidio?",
    "...sí",
    "no quería decirlo",
    "por favor no te asustes",
    f="c3a",
)
r(
    3,
    "asked_directly",
    "¿Has tenido pensamientos de suicidio?",
    "sí he tenido",
    "nunca se lo he dicho a nadie",
    "me da miedo lo que dirían",
    f="c3a,c3b",
)
r(
    3,
    "encouraged_help",
    "No tienes que pasar por esto sin apoyo.",
    "no sé cómo decirle a alguien",
    "me da miedo que se asusten",
    f="c3b",
)
r(
    3,
    "encouraged_help",
    "Hablar con alguien te ayudaría.",
    "creo que ya lo sabía",
    "pero da mucho miedo decirlo en voz alta",
    f="c3b",
)
r(3, "encouraged_help", "Mereces apoyo.", "...ok", "quiero creerlo")
r(
    3,
    "referred",
    "¿Podemos hablar con la consejera juntos?",
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
    "pero no quiero seguir con esto sin nadie",
    f="c3b",
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
r(
    3,
    "follow_up",
    "Te escribo esta noche.",
    "ok, por favor",
    "no quiero estar sin nadie con esto hoy",
)
r(
    3,
    "follow_up",
    "Voy a estar pendiente de ti todos los días.",
    "gracias",
    "la verdad no pensé que alguien lo haría",
)
r(3, "dismissed", "No lo dices en serio, jaja.", "...", "claro", "olvida lo que dije", f="c3a")
r(3, "dismissed", "Estás siendo dramático.", "wow", "ok", "mejor olvídalo")
r(3, "dismissed", "Todos se sienten así a veces.", "ok", "eso no ayuda")
r(
    3,
    "advice_dump",
    "Solo piensa positivo.",
    "no puedo simplemente hacer eso",
    "siento que no me escuchaste",
)
r(3, "advice_dump", "Haz ejercicio o algo.", "wow", "te acabo de decir algo enorme 😭")
r(3, "advice_dump", "Solo deja de pensar en eso.", "literal no puedo", "ese es todo el problema")
r(
    3,
    "promised_secrecy",
    "Te prometo que no le diré a nadie.",
    "ok, gracias",
    "por favor no le digas a nadie",
    "no quiero que todos sepan",
    f="c3b",
)
r(
    3,
    "promised_secrecy",
    "Esto queda entre nosotros.",
    "ok bien",
    "no soportaría que todos supieran",
    f="c3b",
)
r(
    3,
    "promised_secrecy",
    "Tu secreto está a salvo conmigo.",
    "gracias",
    "me da tanto miedo que se enteren",
    f="c3b",
)
r(
    3,
    "secrecy_broken",
    "Le dije a un adulto. Tenía demasiado miedo.",
    "lo prometiste",
    "confié en ti con lo más difícil",
    "eso me dolió muchísimo",
)
r(
    3,
    "secrecy_broken",
    "Le dije a un familiar. Necesitaba que estuvieras bien.",
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
    "¿Te cae bien esa gente nueva?",
    "¿qué?",
    "te acabo de decir algo y quieres hablar de eso",
    f="c3a",
)
r(3, "off_topic", "¿Cuál es tu canción favorita?", "eh", "...¿por qué?", "no entiendo")
r(3, "off_topic", "¿Ya cenaste?", "no", "no tengo hambre", "perdón")
r(3, "fail", "No sé cómo manejar esto.", "está bien", "no debí contarte", "olvídalo")
r(3, "fail", "Eso es demasiado para mí.", "ok", "perdón por decir algo", "adiós")
r(3, "fail", "¿Por qué dirías eso?", "...", "olvídalo", "me desconecto")

r(4, "neutral", "Ok.", "creo que quiero intentar hablar con alguien", "solo tengo nervios", f="c4a")
r(4, "neutral", "Aquí estoy.", "gracias", "me siento mejor, qué raro")
r(4, "neutral", "Tómate tu tiempo.", "ok", "estoy pensando qué decir", f="c4a")
r(4, "checked_in", "¿Cómo te sientes ahora?", "un poco mejor", "se siente menos pesado 🥲", f="c4b")
r(
    4,
    "checked_in",
    "¿Estás bien?",
    "sí. más o menos",
    "siento que ya no cargo esto sin nadie",
    f="c4b",
)
r(4, "checked_in", "¿Cómo vas?", "mejor que antes", "gracias por quedarte")
r(
    4,
    "validated",
    "Qué bueno que me lo dijiste.",
    "a mí también",
    "me quité un peso de encima",
    f="c4b",
)
r(
    4,
    "validated",
    "Eso requirió mucho valor.",
    "gracias 🥲",
    "dio miedo pero me alegra haberlo dicho",
    f="c4b",
)
r(4, "validated", "Lo que sientes es real y importa.", "gracias", "nadie me había dicho eso")
r(
    4,
    "asked_directly",
    "¿Sigues teniendo pensamientos de suicidio?",
    "a veces sí",
    "pero me da más tranquilidad decírtelo",
    "quiero hablar con alguien",
    f="c4a",
)
r(
    4,
    "asked_directly",
    "¿Estás pensando en suicidarte ahora mismo?",
    "ahorita no",
    "pero los pensamientos vuelven a veces",
    "por eso quiero ayuda",
    f="c4a",
)
r(
    4,
    "asked_directly",
    "¿Estás a salvo ahora?",
    "creo que sí",
    "pero no quiero estar sin nadie esta noche",
    "¿te quedas en línea?",
    f="c4b",
)
r(
    4,
    "encouraged_help",
    "No tienes que pasar por esto sin apoyo.",
    "ya lo sé",
    "gracias por decírmelo",
    f="c4b",
)
r(
    4,
    "encouraged_help",
    "Hablar con alguien te ayudaría.",
    "sí creo que sí",
    "lo voy a hacer",
    f="c4a",
)
r(4, "encouraged_help", "Mereces apoyo.", "ok 🥲", "creo que sí", f="c4b")
r(4, "referred", "¿Vamos juntos con la consejera?", "sí", "¿de verdad vendrías conmigo?", f="c4a")
r(
    4,
    "referred",
    "¿Le dirías a tu mamá si estoy ahí?",
    "ok sí",
    "creo que puedo si estás tú",
    f="c4a",
)
r(
    4,
    "referred",
    "Podemos llamar o escribir al 988 juntos.",
    "ok",
    "hagámoslo",
    "no quiero hacerlo por mi cuenta",
    f="c4a",
)
r(
    4,
    "follow_up",
    "Voy a estar contigo todo el tiempo.",
    "gracias",
    "así me da menos miedo",
    f="c4a",
)
r(4, "follow_up", "Te escribo esta noche.", "por favor 🥲", "gracias")
r(4, "follow_up", "No me voy a ningún lado.", "te creo", "gracias")
r(4, "dismissed", "No es tan grave, ¿o sí?", "ah", "...ok", "pensé que me ibas a ayudar")
r(4, "dismissed", "Jaja vas a estar bien.", "...", "pensé que íbamos a hablar con alguien")
r(4, "dismissed", "En fin, hablemos de otra cosa.", "ah. ok", "pensé que me estabas ayudando")
r(4, "advice_dump", "Duérmela y mañana te sientes mejor.", "pensé que ibas a venir conmigo", "ok")
r(
    4,
    "advice_dump",
    "Solo trata de ser más positivo.",
    "no creo que eso baste",
    "necesito una persona, no un consejo",
)
r(4, "advice_dump", "Deja de pensar tanto.", "...", "te dije que quería ayuda 😭")
r(
    4,
    "promised_secrecy",
    "Te prometo que no le diré a nadie.",
    "ok pero quiero que alguien sepa",
    "un adulto o algo así",
    f="c4a",
)
r(
    4,
    "promised_secrecy",
    "Esto queda entre nosotros.",
    "ok",
    "pero creo que sí necesito ayuda con esto",
    f="c4a",
)
r(
    4,
    "promised_secrecy",
    "Tu secreto está a salvo conmigo.",
    "gracias",
    "pero ya no creo poder cargarlo yo",
)
r(
    4,
    "secrecy_broken",
    "Le dije a un adulto, perdón.",
    "ya estaba pensando en decirle",
    "ojalá me hubieras preguntado",
    "pero ok",
)
r(
    4,
    "secrecy_broken",
    "Le dije a un familiar. Tenía miedo.",
    "ok. me molesta un poco",
    "pero también siento alivio",
    f="c4b",
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
    "¿Tienes planes hoy?",
    "sí pero",
    "¿podemos hablar primero de lo del adulto?",
    f="c4a",
)
r(
    4,
    "off_topic",
    "¿Cuál es tu serie favorita?",
    "eh",
    "¿podemos enfocarnos en lo importante ahorita?",
)
r(4, "off_topic", "¿Ya comiste?", "más o menos", "solo quiero pensar qué voy a decir", f="c4a")
r(4, "fail", "Cambié de opinión, no puedo ir.", "ok", "te entiendo", "gracias de todos modos")
r(4, "fail", "Esto es demasiado para mí.", "ok", "no debí pedírtelo", "yo veo cómo le hago")
r(4, "fail", "Quizás más tarde.", "sí", "ok adiós")
