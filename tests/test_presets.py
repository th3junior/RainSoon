"""Preset configuration tests."""

from rainsoon.const import (
    CONF_LOOKAHEAD_HOURS,
    CONF_PRESET,
    CONF_PROBABILITY_THRESHOLD,
    PRESET_HEAVY,
    PRESET_RECOMMENDED,
    PRESET_SENSITIVE,
)
from rainsoon.presets import apply_preset, preset_summary


def test_apply_preset_recommended():
    data = apply_preset(PRESET_RECOMMENDED)
    assert data[CONF_LOOKAHEAD_HOURS] == 12
    assert data[CONF_PROBABILITY_THRESHOLD] == 50
    assert data[CONF_PRESET] == PRESET_RECOMMENDED


def test_apply_preset_heavy_and_sensitive():
    heavy = apply_preset(PRESET_HEAVY)
    sensitive = apply_preset(PRESET_SENSITIVE)
    assert heavy[CONF_PROBABILITY_THRESHOLD] > sensitive[CONF_PROBABILITY_THRESHOLD]
    assert sensitive[CONF_LOOKAHEAD_HOURS] > heavy[CONF_LOOKAHEAD_HOURS]


def test_preset_summary():
    assert "12" in preset_summary(PRESET_RECOMMENDED)
