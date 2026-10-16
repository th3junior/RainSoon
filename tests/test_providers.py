"""Provider normalization tests."""

import json
from pathlib import Path

from rainsoon.const import PROVIDER_OPEN_METEO
from rainsoon.open_meteo import forecast_fetch_hours, normalize_open_meteo

FIXTURES = Path(__file__).parent / "fixtures"


def test_normalize_open_meteo():
    data = json.loads((FIXTURES / "open_meteo.json").read_text(encoding="utf-8"))
    forecast = normalize_open_meteo(data)
    assert forecast.source == PROVIDER_OPEN_METEO
    assert len(forecast.slots) == 4
    assert forecast.slots[1].precipitation_probability == 75.0
    assert forecast.slots[1].precipitation_mm == 0.5


def test_forecast_fetch_hours_uses_buffer():
    assert forecast_fetch_hours(4) >= 48
    assert forecast_fetch_hours(12) >= 48
    assert forecast_fetch_hours(40) >= 52
