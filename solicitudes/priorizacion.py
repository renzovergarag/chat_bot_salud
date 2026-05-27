URGENT_KEYWORDS = {
    "dolor pecho",
    "dificultad respiratoria",
    "falta de aire",
    "convulsion",
    "desmayo",
    "sangrado",
    "embarazo",
    "gestante",
    "suicida",
}

MODERATE_KEYWORDS = {
    "fiebre",
    "dolor intenso",
    "vomitos",
    "diarrea",
    "infeccion",
    "herida",
}


def _contains_any(text, keywords):
    normalized = (text or "").lower()
    return any(keyword in normalized for keyword in keywords)


def calcular_prioridad(datos):
    edad = int(datos.get("edad") or 0)
    puntaje = 0
    clinical_text = f"{datos.get('motivo', '')} {datos.get('detalle_motivo', '')}"

    if _contains_any(clinical_text, URGENT_KEYWORDS):
        puntaje += 4

    if _contains_any(clinical_text, MODERATE_KEYWORDS):
        puntaje += 1

    if edad <= 5 or edad >= 65:
        puntaje += 2

    if bool(datos.get("credendencial_cuidador_discapacidad")):
        puntaje += 2

    if bool(datos.get("Neurodivergente_prais_gestante")):
        puntaje += 2

    if puntaje >= 6:
        clasificacion = "URGENTE"
        etiqueta = "Urgente"
    elif puntaje >= 4:
        clasificacion = "ALTA"
        etiqueta = "Alta"
    elif puntaje >= 2:
        clasificacion = "MEDIA"
        etiqueta = "Media"
    else:
        clasificacion = "BAJA"
        etiqueta = "Baja"

    return {
        "puntaje": puntaje,
        "clasificacion": clasificacion,
        "etiqueta": etiqueta,
    }
