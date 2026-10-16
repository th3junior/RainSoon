"""Helper tests."""

from rainsoon.const import (
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_LOOKAHEAD_HOURS,
    CONF_PROBABILITY_THRESHOLD,
    CONF_PROVIDER,
)
from rainsoon.helpers import normalize_entry_data


def test_normalize_entry_data_coerces_strings():
    raw = {
        CONF_PROVIDER: "open_meteo",
        CONF_LATITUDE: "-23.55",
        CONF_LONGITUDE: "-46.63",
        CONF_LOOKAHEAD_HOURS: "12",
        CONF_PROBABILITY_THRESHOLD: "50",
        "precipitation_threshold_mm": "0.1",
        "update_interval_minutes": "15",
    }
    out = normalize_entry_data(raw)
    assert out[CONF_LOOKAHEAD_HOURS] == 12
    assert out[CONF_PROBABILITY_THRESHOLD] == 50.0
    assert isinstance(out[CONF_LATITUDE], float)
