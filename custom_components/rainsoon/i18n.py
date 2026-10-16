"""User-facing strings (integration language setting, not HA UI locale)."""

from __future__ import annotations

LANG_EN = "en"
LANG_PT = "pt"
LANG_ES = "es"

SUPPORTED_LANGUAGES = (LANG_EN, LANG_PT, LANG_ES)
DEFAULT_LANGUAGE = LANG_EN


def normalize_language(value: str | None) -> str:
    if not value:
        return DEFAULT_LANGUAGE
    v = str(value).lower().replace("_", "-")
    if v in ("pt", "pt-br", "pt_br"):
        return LANG_PT
    if v.startswith("es"):
        return LANG_ES
    if v.startswith("en"):
        return LANG_EN
    if value in SUPPORTED_LANGUAGES:
        return value
    return DEFAULT_LANGUAGE


def format_time_until(minutes: int, lang: str) -> str:
    lang = normalize_language(lang)
    if minutes <= 0:
        return {"en": "now", "pt": "agora", "es": "ahora"}[lang]
    hours = minutes // 60
    mins = minutes % 60

    if lang == LANG_EN:
        if hours == 0:
            return f"{mins} minute{'s' if mins != 1 else ''}"
        if mins == 0:
            return f"{hours} hour{'s' if hours != 1 else ''}"
        return (
            f"{hours} hour{'s' if hours != 1 else ''} and "
            f"{mins} minute{'s' if mins != 1 else ''}"
        )

    if lang == LANG_ES:
        if hours == 0:
            return f"{mins} minuto{'s' if mins != 1 else ''}"
        if mins == 0:
            return f"{hours} hora{'s' if hours != 1 else ''}"
        h = f"{hours} hora{'s' if hours != 1 else ''}"
        m = f"{mins} minuto{'s' if mins != 1 else ''}"
        return f"{h} y {m}"

    # Portuguese
    if hours == 0:
        return f"{mins} minuto{'s' if mins != 1 else ''}"
    if mins == 0:
        return f"{hours} hora{'s' if hours != 1 else ''}"
    h = "1 hora" if hours == 1 else f"{hours} horas"
    m = "1 minuto" if mins == 1 else f"{mins} minutos"
    return f"{h} e {m}"


def _forecast_period_phrase(hours: int, lang: str) -> str:
    """Alexa-friendly period, always includes the hour count."""
    lang = normalize_language(lang)
    h = max(1, int(hours))
    if lang == LANG_EN:
        if h == 1:
            return "the next 1 hour"
        return f"the next {h} hours"
    if lang == LANG_ES:
        if h == 1:
            return "la próxima 1 hora"
        return f"las próximas {h} horas"
    if h == 1:
        return "na próxima 1 hora"
    return f"nas próximas {h} horas"


def build_messages(
    minutes: int | None,
    probability: float | None,
    rain_expected: bool,
    lang: str,
    *,
    lookahead_hours: int = 12,
    max_probability_in_period: float | None = None,
    probability_threshold: float | None = None,
) -> tuple[str, str]:
    lang = normalize_language(lang)
    if not rain_expected or minutes is None or probability is None:
        period = _forecast_period_phrase(lookahead_hours, lang)
        prob_int = (
            int(round(max_probability_in_period))
            if max_probability_in_period is not None
            else None
        )
        thresh_int = (
            int(round(probability_threshold))
            if probability_threshold is not None
            else None
        )

        if lang == LANG_EN:
            short = f"For {period}, no rain is expected."
            if prob_int is not None and thresh_int is not None and prob_int < thresh_int:
                message = (
                    f"For {period}, no rain meets your alert settings. "
                    f"The highest chance in that time is {prob_int}%, "
                    f"below your {thresh_int}% threshold."
                )
            elif prob_int is not None:
                message = (
                    f"For {period}, no rain meets your alert settings. "
                    f"The highest chance in that time is {prob_int}%."
                )
            else:
                message = short
            return message, short

        if lang == LANG_ES:
            short = f"En {period}, no se espera lluvia."
            if prob_int is not None and thresh_int is not None and prob_int < thresh_int:
                message = (
                    f"En {period}, no hay lluvia que cumpla tu configuración. "
                    f"La probabilidad máxima en ese tiempo es {prob_int}%, "
                    f"por debajo de tu umbral del {thresh_int}%."
                )
            elif prob_int is not None:
                message = (
                    f"En {period}, no hay lluvia que cumpla tu configuración. "
                    f"La probabilidad máxima en ese tiempo es {prob_int}%."
                )
            else:
                message = short
            return message, short

        # Portuguese — period already includes "nas/próximas N horas"
        short = f"{period.capitalize()}, não há chuva prevista."
        if prob_int is not None and thresh_int is not None and prob_int < thresh_int:
            message = (
                f"{period.capitalize()}, não há chuva prevista com os limiares que você configurou. "
                f"A maior probabilidade nesse intervalo é {prob_int}%, "
                f"abaixo do seu limite de {thresh_int}%."
            )
        elif prob_int is not None:
            message = (
                f"{period.capitalize()}, não há chuva prevista com os limiares que você configurou. "
                f"A maior probabilidade nesse intervalo é {prob_int}%."
            )
        else:
            message = short
        return message, short

    prob_int = int(round(probability))
    when = format_time_until(minutes, lang)

    if lang == LANG_EN:
        if when == "now":
            message = (
                f"Attention, rain is expected now, with a {prob_int}% probability."
            )
            short = (
                f"Attention, rain is expected now, "
                f"with a {prob_int} percent probability."
            )
        else:
            message = (
                f"Attention, rain is expected in {when}, "
                f"with a {prob_int}% probability."
            )
            short = (
                f"Attention, rain is expected in {when}, "
                f"with a {prob_int} percent probability."
            )
        return message, short

    if lang == LANG_ES:
        if when == "ahora":
            message = (
                f"Atención, se espera lluvia ahora, con un {prob_int}% de probabilidad."
            )
            short = (
                f"Atención, lloverá ahora, con un {prob_int} por ciento de probabilidad."
            )
        else:
            message = (
                f"Atención, lloverá en {when}, con un {prob_int}% de probabilidad."
            )
            short = (
                f"Atención, lloverá en {when}, "
                f"con un {prob_int} por ciento de probabilidad."
            )
        return message, short

    # Portuguese
    if when == "agora":
        message = f"Atenção, chuva prevista para agora, com probabilidade de {prob_int}%."
        short = (
            f"Atenção, irá chover agora, com {prob_int} por cento de probabilidade."
        )
    else:
        message = f"Atenção, irá chover em {when}, com probabilidade de {prob_int}%."
        short = (
            f"Atenção, irá chover em {when}, "
            f"com {prob_int} por cento de probabilidade."
        )
    return message, short


def alert_status_label(level: str, lang: str) -> str:
    lang = normalize_language(lang)
    table = {
        "none": {
            LANG_EN: "No alert",
            LANG_PT: "Sem alerta",
            LANG_ES: "Sin alerta",
        },
        "info": {
            LANG_EN: "Rain later",
            LANG_PT: "Chuva mais tarde",
            LANG_ES: "Lluvia más tarde",
        },
        "watch": {
            LANG_EN: "Rain approaching",
            LANG_PT: "Chuva se aproximando",
            LANG_ES: "Lluvia acercándose",
        },
        "alert": {
            LANG_EN: "Rain soon",
            LANG_PT: "Chuva em breve",
            LANG_ES: "Lluvia pronto",
        },
    }
    return table.get(level, {}).get(lang, level)


def preset_custom_label(lang: str) -> str:
    lang = normalize_language(lang)
    return {
        LANG_EN: "Custom",
        LANG_PT: "Personalizado",
        LANG_ES: "Personalizado",
    }[lang]


def language_display_labels() -> dict[str, str]:
    """Labels for language selector (always native script)."""
    return {
        LANG_EN: "English",
        LANG_PT: "Português",
        LANG_ES: "Español",
    }


def preset_option_labels(lang: str) -> dict[str, str]:
    """Human-readable preset names for config flow (integration language)."""
    lang = normalize_language(lang)
    if lang == LANG_PT:
        return {
            "recommended": "Equilibrado — 12 h, 50%, 0,1 mm/h (recomendado)",
            "heavy": "Só chuva relevante — 12 h, 70%, 0,5 mm/h",
            "sensitive": "Alerta cedo — 24 h, 40%, 0,05 mm/h",
            "custom": "Personalizado — ajustar números",
        }
    if lang == LANG_ES:
        return {
            "recommended": "Equilibrado — 12 h, 50%, 0,1 mm/h (recomendado)",
            "heavy": "Solo lluvia relevante — 12 h, 70%, 0,5 mm/h",
            "sensitive": "Aviso temprano — 24 h, 40%, 0,05 mm/h",
            "custom": "Personalizado — ajustar valores",
        }
    return {
        "recommended": "Balanced — 12 h, 50%, 0.1 mm/h (recommended)",
        "heavy": "Heavy rain only — 12 h, 70%, 0.5 mm/h",
        "sensitive": "Early warning — 24 h, 40%, 0.05 mm/h",
        "custom": "Custom — set numbers on next screen",
    }


_ENTITY_NAMES: dict[str, dict[str, str]] = {
    "proxima_chuva": {
        LANG_EN: "Next rain",
        LANG_PT: "Próxima chuva",
        LANG_ES: "Próxima lluvia",
    },
    "horas_ate_chuva": {
        LANG_EN: "Hours until rain",
        LANG_PT: "Horas até a chuva",
        LANG_ES: "Horas hasta la lluvia",
    },
    "estado_alerta": {
        LANG_EN: "Alert status",
        LANG_PT: "Estado do alerta",
        LANG_ES: "Estado de alerta",
    },
    "proxima_probabilidade": {
        LANG_EN: "Next rain probability",
        LANG_PT: "Probabilidade da próxima chuva",
        LANG_ES: "Probabilidad próxima lluvia",
    },
    "max_probabilidade": {
        LANG_EN: "Max probability in period",
        LANG_PT: "Probabilidade máxima no período",
        LANG_ES: "Probabilidad máxima en el período",
    },
    "precipitacao_proxima_chuva": {
        LANG_EN: "Rain intensity at next alert",
        LANG_PT: "Intensidade na próxima chuva",
        LANG_ES: "Intensidad en la próxima lluvia",
    },
    "condicao_proxima_chuva": {
        LANG_EN: "Condition at next rain",
        LANG_PT: "Condição na próxima chuva",
        LANG_ES: "Condición en la próxima lluvia",
    },
    "condicao_atual": {
        LANG_EN: "Condition now",
        LANG_PT: "Condição agora",
        LANG_ES: "Condición ahora",
    },
    "temperatura_atual": {
        LANG_EN: "Temperature now",
        LANG_PT: "Temperatura agora",
        LANG_ES: "Temperatura ahora",
    },
    "umidade_atual": {
        LANG_EN: "Humidity now",
        LANG_PT: "Umidade agora",
        LANG_ES: "Humedad ahora",
    },
    "vento_atual": {
        LANG_EN: "Wind now",
        LANG_PT: "Vento agora",
        LANG_ES: "Viento ahora",
    },
    "nuvens_atual": {
        LANG_EN: "Cloud cover now",
        LANG_PT: "Nuvens agora",
        LANG_ES: "Nubosidad ahora",
    },
    "precipitacao_atual": {
        LANG_EN: "Rain now (mm/h)",
        LANG_PT: "Chuva agora (mm/h)",
        LANG_ES: "Lluvia ahora (mm/h)",
    },
    "precipitacao_total_janela": {
        LANG_EN: "Total rain in forecast period",
        LANG_PT: "Chuva acumulada no período",
        LANG_ES: "Lluvia total en el período",
    },
    "precipitacao_max_janela": {
        LANG_EN: "Heaviest rain in forecast period",
        LANG_PT: "Maior chuva prevista no período",
        LANG_ES: "Mayor lluvia en el período",
    },
    "vento_max_janela": {
        LANG_EN: "Peak wind in forecast period",
        LANG_PT: "Pico de vento no período",
        LANG_ES: "Pico de viento en el período",
    },
    "chuva_prevista": {
        LANG_EN: "Rain expected",
        LANG_PT: "Chuva prevista",
        LANG_ES: "Lluvia prevista",
    },
    "chuva_agora": {
        LANG_EN: "Raining now",
        LANG_PT: "Chuva caindo agora",
        LANG_ES: "Lloviendo ahora",
    },
}


def entity_name(key: str, lang: str) -> str:
    """Friendly entity name from integration language (not HA UI locale)."""
    language = normalize_language(lang)
    names = _ENTITY_NAMES.get(key, {})
    return names.get(language, names.get(LANG_EN, key))
