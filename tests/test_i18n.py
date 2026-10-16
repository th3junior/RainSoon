"""i18n message tests."""

from rainsoon.i18n import build_messages, entity_name, normalize_language, preset_option_labels


def test_normalize_language():
    assert normalize_language("pt-BR") == "pt"
    assert normalize_language("es") == "es"
    assert normalize_language(None) == "en"


def test_build_messages_english():
    msg, short = build_messages(90, 54.0, True, "en")
    assert msg.startswith("Attention, rain is expected in 1 hour and 30 minutes")
    assert "54%" in msg
    assert "percent" in short


def test_build_messages_no_rain_with_lookahead():
    msg, short = build_messages(
        None,
        None,
        False,
        "pt",
        lookahead_hours=12,
        max_probability_in_period=40.0,
        probability_threshold=99.0,
    )
    assert "próximas 12 horas" in msg
    assert "40%" in msg
    assert "99%" in msg
    assert short == "Nas próximas 12 horas, não há chuva prevista."


def test_preset_labels_portuguese():
    labels = preset_option_labels("pt")
    assert "Equilibrado" in labels["recommended"]
    assert labels["heavy"].startswith("Só chuva")


def test_build_messages_spanish():
    msg, _ = build_messages(45, 60.0, True, "es")
    assert msg.startswith("Atención, lloverá en 45 minutos")


def test_entity_name_follows_integration_language():
    assert entity_name("proxima_chuva", "en") == "Next rain"
    assert entity_name("proxima_chuva", "pt") == "Próxima chuva"
    assert entity_name("chuva_prevista", "es") == "Lluvia prevista"
