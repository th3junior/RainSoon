"""Shared rain outlook computation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from .i18n import DEFAULT_LANGUAGE, build_messages, normalize_language
from .weather_provider import HourlyForecastSlot, NormalizedForecast


@dataclass
class RainOutlook:
    """Computed rain outlook for automations."""

    minutes_until: int | None
    next_probability: float | None
    max_probability: float | None
    rain_expected: bool
    forecast_time: datetime | None
    precipitation_mm: float | None
    weather_code: int | None
    data_source: str
    message: str
    message_short: str


def _slot_matches(
    slot: HourlyForecastSlot,
    probability_threshold: float,
    precipitation_threshold_mm: float,
) -> bool:
    prob = slot.precipitation_probability
    if prob is None or prob < probability_threshold:
        return False
    if slot.precipitation_mm is None:
        return True
    return slot.precipitation_mm >= precipitation_threshold_mm


def compute_rain_outlook(
    forecast: NormalizedForecast,
    *,
    now: datetime,
    lookahead_hours: int,
    probability_threshold: float,
    precipitation_threshold_mm: float,
    language: str = DEFAULT_LANGUAGE,
) -> RainOutlook:
    """Find first matching hourly slot within the lookahead window."""
    lang = normalize_language(language)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    window_end = now + timedelta(hours=lookahead_hours)
    probs: list[float] = []

    first_slot: HourlyForecastSlot | None = None
    first_minutes: int | None = None

    for slot in forecast.slots:
        slot_time = slot.time
        if slot_time.tzinfo is None:
            slot_time = slot_time.replace(tzinfo=now.tzinfo or timezone.utc)
        if slot_time < now or slot_time > window_end:
            continue
        if slot.precipitation_probability is not None:
            probs.append(slot.precipitation_probability)
        if first_slot is None and _slot_matches(
            slot, probability_threshold, precipitation_threshold_mm
        ):
            delta = slot_time - now
            first_minutes = max(0, int(delta.total_seconds() // 60))
            first_slot = slot

    max_prob = max(probs) if probs else None
    rain_expected = first_slot is not None

    forecast_time = first_slot.time if first_slot else None
    next_prob = first_slot.precipitation_probability if first_slot else None
    precip = first_slot.precipitation_mm if first_slot else None
    wcode = first_slot.weather_code if first_slot else None

    message, message_short = build_messages(
        first_minutes,
        next_prob,
        rain_expected,
        lang,
        lookahead_hours=lookahead_hours,
        max_probability_in_period=max_prob,
        probability_threshold=probability_threshold,
    )

    return RainOutlook(
        minutes_until=first_minutes,
        next_probability=next_prob,
        max_probability=max_prob,
        rain_expected=rain_expected,
        forecast_time=forecast_time,
        precipitation_mm=precip,
        weather_code=wcode,
        data_source=forecast.source,
        message=message,
        message_short=message_short,
    )
