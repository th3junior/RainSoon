# RainSoon

Rain alerts for **Home Assistant** using **[Open-Meteo](https://open-meteo.com/)** — free, no API key, built for **Alexa**, dashboards, and automations.

**Languages:** English · [Português](README.pt-BR.md) · [Español](README.es.md)

[![HACS](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/th3junior/RainSoon)

## What it does

RainSoon scans **hourly** Open-Meteo data for your location and tells you:

- **When** rain is likely to start (minutes / hours).
- **Whether** it meets **your** thresholds (probability + intensity).
- **Ready-to-speak** text in **English, Portuguese, or Spanish** (`message` / `message_short` attributes).
- **Current weather** and **period stats** (total rain, peak wind, etc.) as extra sensors.

## Install (HACS)

1. **HACS** → **Custom repositories** → add `https://github.com/th3junior/RainSoon` → category **Integration**.
2. Install **RainSoon** → **restart** Home Assistant.
3. **Settings → Devices & services → Add integration → RainSoon**

### Setup wizard

| Step | What you choose |
|------|-----------------|
| **1. Location** | Home Assistant home coordinates or pick on the map. |
| **2. Language** | **Integration language** — Alexa messages, alert labels, weather descriptions, and **sensor friendly names**. Independent of the HA UI language. |
| **3. Profile** | **Balanced** (recommended), **Heavy rain only**, **Early warning**, or **Custom** thresholds. |

Change anything later: **RainSoon → Configure / Options** (language, profile, forecast period, thresholds, update interval).

## Forecast period (important)

This is **not** a physical window at home. It is **how many hours forward from now** RainSoon analyzes (default **12 h**, often **12–24 h**).

- **`binary_sensor.*_chuva_prevista`** (Rain expected) turns **on** only if **some hour** in that range passes your probability **and** rain intensity limits.
- Sensors named **“in forecast period”** (total / heaviest rain, peak wind) describe **that same hour range**.

## Alert profiles

| Profile | Period | Min. probability | Min. rain |
|---------|--------|------------------|-----------|
| **Balanced** (default) | 12 h | 50% | 0.1 mm/h |
| **Heavy rain only** | 12 h | 70% | 0.5 mm/h |
| **Early warning** | 24 h | 40% | 0.05 mm/h |
| **Custom** | You set | You set | You set |

## Main entities

Entity IDs use the prefix `rainsoon` (example: `sensor.rainsoon_proxima_chuva`).

| Entity | Role |
|--------|------|
| **`sensor.*_proxima_chuva`** | Minutes until the **first hour that triggers your alert**; attributes **`message`**, **`message_short`**, **`rain_expected`**, **`lookahead_hours`**. |
| **`binary_sensor.*_chuva_prevista`** | **On** = rain expected in the period **with your thresholds**. |
| **`binary_sensor.*_chuva_agora`** | **On** = raining at the location **now** (Open-Meteo “current”). |
| **`sensor.*_estado_alerta`** | Plain text: no alert / rain later / approaching / soon. |
| **`sensor.*_max_probabilidade`** | **Highest** hourly rain **chance in the period**, **ignoring** your thresholds (diagnostic). |
| **`sensor.*_proxima_probabilidade`** | Probability at the **first alert hour** (unknown if no alert). |
| **`sensor.*_precipitacao_max_janela`** | Heaviest rain (mm/h) in the period. |
| **`sensor.*_precipitacao_total_janela`** | Total rain (mm) summed over the period. |

### “Unknown” on some sensors

If **`chuva_prevista`** is **off**, sensors like **Next rain** (minutes) or **Next probability** may show **unknown** — there is no “next alert” under your rules. That is normal. Use **`message`** / **`message_short`** on **`proxima_chuva`** for voice summaries (including **no rain**).

### Max probability vs rain expected

Example: you set **99%** probability threshold. Open-Meteo may show **40%** as the **max in 12 h**, but **Rain expected** stays **off**. The **`message`** then explains: no rain for your settings, and may mention the highest chance in those hours.

## Alexa and voice automations

Messages follow the **integration language** (not the HA UI language).

| Situation | Example (`message_short`, English) |
|-----------|--------------------------------------|
| Rain alert | *Attention, rain is expected in 2 hours…* |
| No rain | *For the next 12 hours, no rain is expected.* |

Portuguese (no rain): *Nas próximas 12 horas, não há chuva prevista.*

```yaml
action:
  - service: notify.alexa_media
    data:
      message: "{{ state_attr('sensor.rainsoon_proxima_chuva', 'message_short') }}"
      target: media_player.echo_living_room
      data:
        type: announce
```

**Morning briefing** (rain or clear): use `message_short` without requiring `chuva_prevista` to be on — see [`docs/automations-alexa.yaml`](docs/automations-alexa.yaml).

## Upgrade from `rain_alert` (2.x)

RainSoon **3.x** uses domain **`rainsoon`** (folder `custom_components/rainsoon`).

1. Remove the old **Rain Alert** integration.
2. Delete `custom_components/rain_alert` if it still exists.
3. Update via HACS → restart → add **RainSoon** again.
4. Update automations to `sensor.rainsoon_*` / `binary_sensor.rainsoon_*`.

## Development

```bash
pip install pytest homeassistant
pytest
```

Optional: `python scripts/rainsoon_check.py` — compare live data with Open-Meteo.

## License

MIT — see [LICENSE](LICENSE).
