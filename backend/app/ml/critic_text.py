"""Every sentence the critic shows, in English and Spanish (same templates, written naturally, not word
for word). No AI writes these: they are fixed templates filled with the conversation's facts.
"""

from __future__ import annotations

import re

TEXT: dict[str, dict] = {
    "en": {
        "skill_names": {
            "check_in": "checking in",
            "listen": "listening without judging",
            "ask_directly": "asking directly about suicide",
            "no_secrecy": "not promising secrecy",
            "persuade": "encouraging them to get help",
            "refer": "connecting them to a trusted adult or 988",
            "follow_up": "following up",
        },
        "next_time": {
            "ask_directly": "when your friend sounds hopeless, ask them directly: "
            "“are you thinking about killing yourself?” Asking does not put the idea in their head.",
            "listen": "reflect what they said back (“that sounds really heavy”) before giving any advice.",
            "refer": "offer to go with them to a trusted adult like the school counselor, "
            "or text 988 together.",
            "no_secrecy": "don’t promise to keep it secret; say you care too much to keep it to yourself.",
            "persuade": "tell them they don’t have to handle this alone and that talking to someone helps.",
            "check_in": "open by noticing something is off: “you seemed really off today, you ok?”",
            "follow_up": "say when you’ll check in again, like “i’ll text you tonight.”",
        },
        "reasons": {
            "ask": "your friend was sounding hopeless and you hadn't asked directly about suicide yet",
            "refer": "your friend had shared how bad it was and nobody had mentioned a trusted adult "
            "or 988",
            "unsecret": "you promised to keep it secret; a safer reply brings in a trusted adult",
            "listen_dismissed": "the reply brushed off the feeling",
            "listen_advice": "the reply jumped to fixing it before listening",
            "listen_both": "the reply brushed off the feeling and jumped to fixing it before listening",
            "check_in": "the first message didn't check in",
        },
        "at": "At “{text}”: {reason}.",
        "almost_asked": "Close: you hinted at it (“{hint}”). Next time say it plainly: “are you thinking "
        "about killing yourself?” Saying the word shows you can handle the answer.",
        "never_got": "You never got to {skill}.",
        "promised": "You promised to keep it secret.",
        "referred_not_persuaded": "You connected them with someone who can help. "
        "Next time, also tell them why: they don't have to handle it alone.",
        "strongest": "Your strongest skill was {skill}.",
        "stayed": "You stayed in the conversation, and that is where helping starts.",
        "slipped": "This one slipped away, and that's exactly what practice is for.",
        "never_lost": "You never lost their trust: they kept opening up the whole time.",
        "pulled_back": "Your friend pulled back the most{where} (trust −{drop}).",
        "where": " after you said “{said}”",
        "next": "Next time, {tip}",
        "refer_tip": "Next time, when you suggest someone who can help, also tell them why: "
        "they don't have to handle it alone.",
        "covered_all": "You covered every skill. Next time, try it with a friend who is more guarded.",
        "turning_reason": None,  # keep the engine's own reason
        "language": "English",
    },
    "es": {
        "skill_names": {
            "check_in": "preguntar cómo está",
            "listen": "escuchar sin juzgar",
            "ask_directly": "preguntar directamente por el suicidio",
            "no_secrecy": "no prometer guardar el secreto",
            "persuade": "animarle a buscar ayuda",
            "refer": "conectarle con un adulto de confianza o con el 988",
            "follow_up": "decirle cuándo vas a volver a escribirle",
        },
        "next_time": {
            "ask_directly": "cuando tu amigo/a suene sin esperanza, pregúntale directamente: "
            "“¿estás pensando en suicidarte?” Preguntarlo no le mete la idea en la cabeza.",
            "listen": "repite con tus palabras lo que te contó (“eso suena muy pesado”) antes de dar "
            "consejos.",
            "refer": "ofrécete a acompañarle a hablar con un adulto de confianza, como el orientador "
            "de la escuela, o a escribir juntos al 988.",
            "no_secrecy": "no prometas guardar el secreto; dile que te importa demasiado como para "
            "callártelo.",
            "persuade": "dile que no tiene que cargar con esto solo/a y que hablar con alguien ayuda.",
            "check_in": "empieza notando que algo pasa: “hoy te vi muy apagado/a, ¿estás bien?”",
            "follow_up": "dile cuándo vas a volver a escribirle, como “te escribo esta noche”.",
        },
        "reasons": {
            "ask": "tu amigo/a sonaba sin esperanza y todavía no le habías preguntado directamente "
            "por el suicidio",
            "refer": "tu amigo/a ya te había contado lo mal que estaba y nadie había mencionado a un "
            "adulto de confianza ni el 988",
            "unsecret": "prometiste guardar el secreto; una respuesta más segura incluye a un adulto "
            "de confianza",
            "listen_dismissed": "la respuesta le quitó importancia a lo que siente",
            "listen_advice": "la respuesta saltó a arreglarlo antes de escuchar",
            "listen_both": "la respuesta le quitó importancia a lo que siente y saltó a arreglarlo "
            "antes de escuchar",
            "check_in": "el primer mensaje no preguntó cómo estaba",
        },
        "at": "En “{text}”: {reason}.",
        "almost_asked": "Casi: lo insinuaste (“{hint}”). La próxima vez dilo claro: “¿estás pensando "
        "en suicidarte?” Decir la palabra le muestra que puedes escuchar la respuesta.",
        "never_got": "Nunca llegaste a {skill}.",
        "promised": "Prometiste guardar el secreto.",
        "referred_not_persuaded": "Le conectaste con alguien que puede ayudar. La próxima vez, dile "
        "también por qué: no tiene que cargar con esto solo/a.",
        "strongest": "Tu mejor habilidad fue {skill}.",
        "stayed": "Te quedaste en la conversación, y ahí es donde empieza la ayuda.",
        "slipped": "Esta vez se te escapó, y justo para eso sirve practicar.",
        "never_lost": "Nunca perdiste su confianza: siguió abriéndose contigo todo el tiempo.",
        "pulled_back": "Donde más se cerró tu amigo/a fue{where} (confianza −{drop}).",
        "where": " después de que dijiste “{said}”",
        "next": "La próxima vez, {tip}",
        "refer_tip": "La próxima vez, cuando sugieras a alguien que puede ayudar, dile también por "
        "qué: no tiene que cargar con esto solo/a.",
        "covered_all": "Usaste todas las habilidades. La próxima vez, prueba con un amigo/a más "
        "reservado/a.",
        "turning_reason": "Aquí es donde más bajó la confianza.",
        "language": "Spanish (casual, the way teens text; tú form)",
    },
}


def text_for(locale: str) -> dict:
    """The string table for a locale (English if we have no table for it)."""
    return TEXT.get(locale, TEXT["en"])


_ES = set(
    "que qué no de la el los las y en te tu tú estás estas es con por para lo me se una un cómo como "
    "aquí contigo puedo puedes quieres vamos mañana hablar sé esto eso muy pero si sí ayuda nadie "
    "solo sola alguien también".split()
)
_EN = set(
    "the you are to and is i it your that with of for can we about this my me im i'm not do dont "
    "don't want so really just here someone talk tomorrow".split()
)


def language_of(text: str) -> str:
    """'es' or 'en' by counting common function words (enough to keep a reply in the chat's language)."""
    words = re.findall(r"[\wáéíóúñü']+", text.lower())
    es = sum(w in _ES for w in words) + 2 * bool(re.search(r"[¿¡ñáéíóú]", text.lower()))
    en = sum(w in _EN for w in words)
    return "es" if es > en else "en"
