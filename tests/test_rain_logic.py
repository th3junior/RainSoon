"""Rain outlook algorithm tests."""

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

from rainsoon.const import PROVIDER_OPEN_METEO
from rainsoon.rain_logic import compute_rain_outlook
from rainsoon.weather_provider import HourlyForecastSlot, NormalizedForecast


def _forecast(slots):
    return NormalizedForecast(slots=slots, source=PROVIDER_OPEN_METEO)


def test_no_rain_in_window():
    tz = ZoneInfo("America/Sao_Paulo")
    now = datetime(2026, 3, 19, 10, 30, tzinfo=tz)
    slots = [
        HourlyForecastSlot(
            time=now + timedelta(hours=1),
            precipitation_probability=30,
            precipitation_mm=0.0,
            weather_code=0,
        ),
    ]
    outlook = compute_rain_outlook(
        _forecast(slots),
        now=now,
        lookahead_hours=12,
        probability_threshold=50,
        precipitation_threshold_mm=0.1,
    )
    assert not outlook.rain_expected
    assert outlook.minutes_until is None
    assert outlook.max_probability == 30.0


def test_first_matching_slot():
    tz = ZoneInfo("America/Sao_Paulo")
    now = datetime(2026, 3, 19, 10, 30, tzinfo=tz)
    slots = [
        HourlyForecastSlot(
            time=datetime(2026, 3, 19, 11, 0, tzinfo=tz),
            precipitation_probability=75,
            precipitation_mm=0.5,
            weather_code=61,
        ),
        HourlyForecastSlot(
            time=datetime(2026, 3, 19, 12, 0, tzinfo=tz),
            precipitation_probability=90,
            precipitation_mm=2.0,
            weather_code=63,
        ),
    ]
    outlook = compute_rain_outlook(
        _forecast(slots),
        now=now,
        lookahead_hours=12,
        probability_threshold=50,
        precipitation_threshold_mm=0.1,
        language="pt",
    )
    assert outlook.rain_expected
    assert outlook.minutes_until == 30
    assert outlook.next_probability == 75.0
    assert outlook.message.startswith("Atenção, irá chover em 30 minutos")
    assert "75%" in outlook.message
    assert outlook.message_short.startswith("Atenção, irá chover em 30 minutos")
    assert outlook.max_probability == 90.0


def test_message_hours_and_minutes():
    tz = ZoneInfo("America/Sao_Paulo")
    now = datetime(2026, 3, 19, 10, 0, tzinfo=tz)
    slots = [
        HourlyForecastSlot(
            time=datetime(2026, 3, 19, 12, 15, tzinfo=tz),
            precipitation_probability=54,
            precipitation_mm=1.0,
            weather_code=61,
        ),
    ]
    outlook = compute_rain_outlook(
        _forecast(slots),
        now=now,
        lookahead_hours=12,
        probability_threshold=50,
        precipitation_threshold_mm=0.1,
        language="pt",
    )
    assert outlook.minutes_until == 135
    assert "2 horas e 15 minutos" in outlook.message
    assert "54%" in outlook.message


def test_probability_only_when_mm_missing():
    tz = timezone.utc
    now = datetime(2026, 3, 19, 12, 0, tzinfo=tz)
    slots = [
        HourlyForecastSlot(
            time=now + timedelta(hours=1),
            precipitation_probability=60,
            precipitation_mm=None,
            weather_code=None,
        ),
    ]
    outlook = compute_rain_outlook(
        _forecast(slots),
        now=now,
        lookahead_hours=6,
        probability_threshold=50,
        precipitation_threshold_mm=0.1,
    )
    assert outlook.rain_expected
    assert outlook.minutes_until == 60


def test_integration_open_meteo_fixture():
    import json
    from pathlib import Path

    from rainsoon.open_meteo import normalize_open_meteo

    data = json.loads(
        (Path(__file__).parent / "fixtures" / "open_meteo.json").read_text(
            encoding="utf-8"
        )
    )
    forecast = normalize_open_meteo(data)
    tz = ZoneInfo("America/Sao_Paulo")
    now = datetime(2026, 3, 19, 10, 15, tzinfo=tz)
    outlook = compute_rain_outlook(
        forecast,
        now=now,
        lookahead_hours=12,
        probability_threshold=50,
        precipitation_threshold_mm=0.1,
    )
    assert outlook.rain_expected
    assert outlook.next_probability == 75.0
    assert outlook.minutes_until == 45
