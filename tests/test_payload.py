"""Payload builder tests."""

import json
from datetime import datetime, timezone
from pathlib import Path

from rainsoon.payload import build_rain_alert_data
from rainsoon.open_meteo import normalize_open_meteo

FIXTURES = Path(__file__).parent / "fixtures"


def test_build_rain_alert_data_window_stats():
    data = json.loads((FIXTURES / "open_meteo.json").read_text(encoding="utf-8"))
    forecast = normalize_open_meteo(data)
    now = datetime(2026, 3, 19, 9, 30, tzinfo=timezone.utc)
    payload = build_rain_alert_data(
        forecast,
        now=now,
        lookahead_hours=4,
        probability_threshold=50,
        precipitation_threshold_mm=0.1,
        language="en",
    )
    assert payload.outlook.rain_expected is True
    assert payload.total_precipitation_in_window_mm == 3.2
    assert payload.max_precipitation_in_window_mm == 1.5
    assert len(payload.hourly_forecast) == 4
