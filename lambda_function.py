"""
Alexa Skill Lambda: Menu Semanal
Lee la hoja de Google Sheets con el plan de comidas y responde qué hay hoy,
mañana o cualquier día de la semana.
"""

import csv
import io
import locale
import logging
from datetime import datetime, timedelta
from urllib.request import urlopen

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# URL de exportación CSV de tu Google Sheet (debe ser público o "cualquiera con el enlace")
SHEET_CSV_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "TU_SPREADSHEET_ID_AQUI"
    "/export?format=csv&gid=0"
)

DIAS_SEMANA = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]

# Mapeo de datetime.weekday() (0=Monday) a nombre en español
WEEKDAY_TO_DIA = {
    0: "lunes",
    1: "martes",
    2: "miércoles",
    3: "jueves",
    4: "viernes",
    5: "sábado",
    6: "domingo",
}


def fetch_menu():
    """Descarga el CSV y devuelve una lista de semanas.
    Cada semana es un dict {dia: {"comida": ..., "cena": ...}}.
    """
    response = urlopen(SHEET_CSV_URL)
    content = response.read().decode("utf-8")
    reader = csv.reader(io.StringIO(content))

    weeks = []
    current_week = {}

    header = next(reader, None)  # Saltar cabecera (, Comida, Cena)

    for row in reader:
        if len(row) < 3:
            continue

        dia_raw = row[0].strip().lower()

        # Normalizar: quitar tildes para comparación
        dia_norm = _normalize(dia_raw)

        if dia_norm not in [_normalize(d) for d in DIAS_SEMANA]:
            continue

        # Encontrar el día real con tilde
        dia = next(d for d in DIAS_SEMANA if _normalize(d) == dia_norm)

        comida = row[1].strip() if row[1].strip() else None
        cena = row[2].strip() if row[2].strip() else None

        # Si ya vimos este día, estamos en una nueva semana
        if dia in current_week:
            weeks.append(current_week)
            current_week = {}

        current_week[dia] = {"comida": comida, "cena": cena}

    if current_week:
        weeks.append(current_week)

    return weeks


def _normalize(text):
    """Quita tildes para comparar días."""
    replacements = {"á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u"}
    result = text.lower()
    for accented, plain in replacements.items():
        result = result.replace(accented, plain)
    return result


def get_menu_for_day(target_date):
    """Devuelve (comida, cena) para una fecha dada."""
    weeks = fetch_menu()
    if not weeks:
        return None, None

    dia = WEEKDAY_TO_DIA[target_date.weekday()]

    # Usar el número de semana ISO para alternar entre semanas
    iso_week = target_date.isocalendar()[1]
    week_index = iso_week % len(weeks)

    week = weeks[week_index]
    if dia in week:
        return week[dia]["comida"], week[dia]["cena"]

    return None, None


def build_meal_speech(dia_nombre, comida, cena):
    """Construye la frase de respuesta."""
    parts = []
    if comida and cena:
        parts.append(f"El {dia_nombre}, de comida hay {comida} y de cena {cena}")
    elif comida:
        parts.append(f"El {dia_nombre}, de comida hay {comida}. No hay cena planificada")
    elif cena:
        parts.append(f"El {dia_nombre}, no hay comida planificada, pero de cena hay {cena}")
    else:
        parts.append(f"El {dia_nombre} no hay nada planificado")
    return ". ".join(parts)


def resolve_target_date(day_slot_value):
    """Convierte el valor del slot AMAZON.DATE a una fecha.
    AMAZON.DATE devuelve formatos como: 2026-02-17, 2026-W08, 2026-W08-WE
    """
    today = datetime.now()

    if not day_slot_value:
        return today

    val = day_slot_value.strip()

    # AMAZON.DATE devuelve fechas ISO: "2026-02-17"
    try:
        return datetime.strptime(val, "%Y-%m-%d")
    except ValueError:
        pass

    # También puede devolver semanas: "2026-W08" — usar el lunes de esa semana
    try:
        return datetime.strptime(val + "-1", "%G-W%V-%u")
    except ValueError:
        pass

    # Fallback: intentar matchear nombre de día en español
    val_norm = _normalize(val.lower())
    for i, dia in enumerate(DIAS_SEMANA):
        if _normalize(dia) == val_norm:
            today_weekday = today.weekday()
            days_ahead = i - today_weekday
            if days_ahead <= 0:
                days_ahead += 7
            if days_ahead == 7:
                days_ahead = 0
            return today + timedelta(days=days_ahead)

    return today


# ─── Alexa Handlers ───────────────────────────────────────────────────────────


def lambda_handler(event, context):
    """Entry point de la Lambda."""
    logger.info("Event: %s", event)

    request = event.get("request", {})
    request_type = request.get("type", "")

    if request_type == "LaunchRequest":
        return handle_launch()
    elif request_type == "IntentRequest":
        return handle_intent(request)
    elif request_type == "SessionEndedRequest":
        return handle_session_end()
    else:
        return build_response("No he entendido la petición.", should_end=True)


def handle_launch():
    """Cuando el usuario abre la skill sin decir nada más."""
    today = datetime.now()
    dia = WEEKDAY_TO_DIA[today.weekday()]
    comida, cena = get_menu_for_day(today)

    speech = build_meal_speech(dia, comida, cena)
    speech += ". ¿Quieres consultar otro día?"
    reprompt = "¿Qué día quieres consultar? Puedes decir mañana, o un día de la semana."

    return build_response(speech, reprompt=reprompt, should_end=False)


def handle_intent(request):
    """Maneja los diferentes intents."""
    intent_name = request["intent"]["name"]

    if intent_name == "ConsultarMenuIntent":
        return handle_consultar_menu(request)
    elif intent_name in ("NingunoIntent", "AMAZON.NoIntent"):
        return build_response("¡Buen provecho!", should_end=True)
    elif intent_name == "AMAZON.HelpIntent":
        return handle_help()
    elif intent_name in ("AMAZON.CancelIntent", "AMAZON.StopIntent"):
        return build_response("¡Buen provecho!", should_end=True)
    elif intent_name == "AMAZON.FallbackIntent":
        return build_response(
            "No he entendido. Puedes decir: ¿qué hay de comer mañana? "
            "O decir un día de la semana.",
            reprompt="¿Qué día quieres consultar?",
            should_end=False,
        )
    else:
        return build_response(
            "No he entendido. ¿Qué día quieres consultar?",
            reprompt="Puedes decir mañana, o un día como lunes o martes.",
            should_end=False,
        )


def handle_consultar_menu(request):
    """Maneja el intent de consultar menú para un día."""
    slots = request["intent"].get("slots", {})
    day_slot = slots.get("dia", {})
    day_value = day_slot.get("value")

    target_date = resolve_target_date(day_value)
    dia = WEEKDAY_TO_DIA[target_date.weekday()]
    comida, cena = get_menu_for_day(target_date)

    speech = build_meal_speech(dia, comida, cena)
    speech += ". ¿Quieres consultar otro día?"
    reprompt = "¿Qué otro día quieres consultar?"

    return build_response(speech, reprompt=reprompt, should_end=False)


def handle_help():
    speech = (
        "Puedo decirte qué hay de comer y cenar cada día. "
        "Prueba a decir: ¿qué hay de comer mañana? "
        "O también: ¿qué hay el viernes?"
    )
    return build_response(speech, reprompt="¿Qué día quieres consultar?", should_end=False)


def handle_session_end():
    return build_response("", should_end=True)


# ─── Response builder ─────────────────────────────────────────────────────────


def build_response(speech, reprompt=None, should_end=True):
    response = {
        "version": "1.0",
        "response": {
            "outputSpeech": {
                "type": "PlainText",
                "text": speech,
            },
            "shouldEndSession": should_end,
        },
    }

    if reprompt:
        response["response"]["reprompt"] = {
            "outputSpeech": {
                "type": "PlainText",
                "text": reprompt,
            }
        }

    return response
