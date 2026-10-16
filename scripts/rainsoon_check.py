#!/usr/bin/env python3
"""
RainSoon — verificador Open-Meteo (mesma lógica do Home Assistant).

Exemplo:
  python scripts/rainsoon_check.py -23.283776 -47.677852
  python scripts/rainsoon_check.py -23.28 -47.67 --lookahead 12 --prob 50 --mm 0.1
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "custom_components"))

from rainsoon.open_meteo import (  # noqa: E402
    HOURLY_VARS,
    forecast_fetch_hours,
    normalize_open_meteo,
)
from rainsoon.payload import build_rainsoon_data  # noqa: E402
from rainsoon.rain_logic import compute_rain_outlook  # noqa: E402
from rainsoon.weather_provider import HourlyForecastSlot  # noqa: E402

API = "https://api.open-meteo.com/v1/forecast"

# ANSI (Windows 10+ terminal OK)
R = "\033[0m"
B = "\033[1m"
D = "\033[2m"
RED = "\033[31m"
GRN = "\033[32m"
YEL = "\033[33m"
BLU = "\033[34m"
CYN = "\033[36m"
MAG = "\033[35m"


def _supports_color() -> bool:
    return sys.stdout.isatty() and "--no-color" not in sys.argv


def c(text: str, code: str) -> str:
    if not _supports_color():
        return text
    return f"{code}{text}{R}"


def fetch(lat: float, lon: float, lookahead: int) -> dict:
    hours = forecast_fetch_hours(lookahead)
    params = urllib.parse.urlencode(
        {
            "latitude": lat,
            "longitude": lon,
            "hourly": HOURLY_VARS,
            "current": "temperature_2m,relative_humidity_2m,precipitation,weather_code,cloud_cover,wind_speed_10m",
            "forecast_hours": hours,
            "timezone": "auto",
        }
    )
    with urllib.request.urlopen(f"{API}?{params}", timeout=45) as resp:
        return json.loads(resp.read().decode())


def slot_mm(slot: HourlyForecastSlot) -> float:
    if slot.precipitation_mm is None:
        return 0.0
    return float(slot.precipitation_mm)


def slot_matches(
    slot: HourlyForecastSlot, prob_t: float, mm_t: float
) -> tuple[bool, str]:
    prob = slot.precipitation_probability
    if prob is None or prob < prob_t:
        return False, f"prob {prob}% < {prob_t}%"
    mm = slot_mm(slot)
    if mm < mm_t:
        return False, f"mm {mm:.2f} < {mm_t}"
    return True, "OK"


def analyze_row(
    slot: HourlyForecastSlot,
    now: datetime,
    window_end: datetime,
    prob_t: float,
    mm_t: float,
    first_hit_time: datetime | None,
) -> dict:
    t = slot.time
    if t.tzinfo is None:
        t = t.replace(tzinfo=now.tzinfo or timezone.utc)
    past = t < now
    in_window = not past and t <= window_end
    match, reason = slot_matches(slot, prob_t, mm_t)
    flags: list[str] = []
    if past:
        flags.append("passado")
    if in_window:
        flags.append("janela")
    if match and in_window:
        flags.append("ALERTA")
    if first_hit_time and t == first_hit_time:
        flags.append("1ª chuva")
    return {
        "time": t,
        "prob": slot.precipitation_probability,
        "mm": slot_mm(slot),
        "code": slot.weather_code,
        "past": past,
        "in_window": in_window,
        "match": match and in_window,
        "reason": reason,
        "flags": flags,
    }


def print_header(title: str) -> None:
    w = 72
    bar = "=" * w
    print(c(bar, BLU))
    print(c(f" {title}", B + CYN))
    print(c(bar, BLU))


def print_table(rows: list[dict]) -> None:
    hdr = (
        f"{'Hora':<17} {'Prob':>5} {'mm/h':>6} {'Cod':>4}  "
        f"{'Janela':^6} {'Alerta':^7}  Notas"
    )
    print(c(hdr, B))
    print(c("-" * len(hdr), D))
    for row in rows:
        t_str = row["time"].strftime("%d/%m %H:%M")
        prob = row["prob"] if row["prob"] is not None else "-"
        mm = f"{row['mm']:.2f}"
        code = row["code"] if row["code"] is not None else "-"
        win = c("sim", GRN) if row["in_window"] else c(".", D)
        if row["match"]:
            alert = c("SIM", GRN + B)
        elif row["in_window"] and row["prob"] and row["prob"] >= 30:
            alert = c("~", YEL)
        else:
            alert = c(".", D)
        notes = ", ".join(row["flags"]) or row["reason"]
        line = f"{t_str:<17} {prob!s:>5} {mm:>6} {code!s:>4}  {win:^14}  {notes}"
        if "1ª chuva" in row["flags"]:
            line = c(line, MAG + B)
        elif row["past"]:
            line = c(line, D)
        print(line)


def print_ha_panel(outlook, lookahead: int, prob_t: float, mm_t: float) -> None:
    print()
    print(c(">> Valores esperados no Home Assistant (RainSoon)", B + YEL))
    print(c("-" * 50, D))
    items = [
        ("binary_sensor.chuva_prevista", "Ligado" if outlook.rain_expected else "Desligado"),
        (
            "sensor.proxima_chuva",
            f"{outlook.minutes_until} min"
            if outlook.minutes_until is not None
            else "Desconhecido",
        ),
        (
            "sensor.proxima_probabilidade",
            f"{outlook.next_probability}%"
            if outlook.next_probability is not None
            else "Desconhecido",
        ),
        (
            "sensor.max_probabilidade",
            f"{outlook.max_probability}%"
            if outlook.max_probability is not None
            else "Desconhecido",
        ),
        ("atributo message", outlook.message),
    ]
    for name, val in items:
        print(f"  {c(name, CYN):<32} {val}")
    print()
    print(c("  Config (atributos no sensor proxima_chuva):", D))
    print(f"    lookahead_hours ........ {lookahead}")
    print(f"    probability_threshold .. {prob_t}%")
    print(f"    precipitation_threshold_mm {mm_t}")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:
            pass

    p = argparse.ArgumentParser(
        description="RainSoon — conferência Open-Meteo vs lógica HA",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p.add_argument("latitude", type=float, help="Latitude (ex. -23.283776)")
    p.add_argument("longitude", type=float, help="Longitude (ex. -47.677852)")
    p.add_argument("--lookahead", type=int, default=12, help="Janela (horas)")
    p.add_argument("--prob", type=float, default=50, help="Limiar probabilidade %")
    p.add_argument("--mm", type=float, default=0.1, help="Limiar mm/h")
    p.add_argument(
        "--tz",
        default="America/Sao_Paulo",
        help="Fuso para 'agora' (alinhado ao HA)",
    )
    p.add_argument("--json", action="store_true", help="Saída JSON (automação/debug)")
    p.add_argument("--no-color", action="store_true", help="Sem cores ANSI")
    args = p.parse_args()

    fetch_h = forecast_fetch_hours(args.lookahead)
    data = fetch(args.latitude, args.longitude, args.lookahead)
    forecast = normalize_open_meteo(data)
    now = datetime.now(tz=ZoneInfo(args.tz))
    window_end = now + timedelta(hours=args.lookahead)

    outlook = compute_rain_outlook(
        forecast,
        now=now,
        lookahead_hours=args.lookahead,
        probability_threshold=args.prob,
        precipitation_threshold_mm=args.mm,
    )

    if args.json:
        print(
            json.dumps(
                {
                    "latitude": args.latitude,
                    "longitude": args.longitude,
                    "now": now.isoformat(),
                    "window_end": window_end.isoformat(),
                    "api_forecast_hours": fetch_h,
                    "outlook": {
                        "rain_expected": outlook.rain_expected,
                        "minutes_until": outlook.minutes_until,
                        "next_probability": outlook.next_probability,
                        "max_probability": outlook.max_probability,
                        "forecast_time": outlook.forecast_time.isoformat()
                        if outlook.forecast_time
                        else None,
                        "message": outlook.message,
                    },
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return

    print_header("RainSoon | Open-Meteo Check")
    print(f"  Coordenadas .... {args.latitude}, {args.longitude}")
    print(f"  Agora .......... {now.strftime('%Y-%m-%d %H:%M %Z')}")
    print(f"  Janela ......... {args.lookahead} h (até {window_end.strftime('%d/%m %H:%M')})")
    print(f"  API fetch ...... {fetch_h} h horários (buffer ≥ janela)")
    print(f"  Limiares ....... prob ≥ {args.prob}%  |  precip ≥ {args.mm} mm/h")
    print()
    print(
        c(
            "  Legenda: Janela = dentro das próximas N h · ALERTA = passa nos limiares · "
            "1ª chuva = primeiro slot que dispara o RainSoon",
            D,
        )
    )
    print()

    rows = []
    for slot in forecast.slots:
        rows.append(
            analyze_row(
                slot,
                now,
                window_end,
                args.prob,
                args.mm,
                outlook.forecast_time,
            )
        )
    print_table(rows)
    print_ha_panel(outlook, args.lookahead, args.prob, args.mm)
    print()
    print(c("  URL (navegador):", D))
    q = urllib.parse.urlencode(
        {
            "latitude": args.latitude,
            "longitude": args.longitude,
            "hourly": "precipitation_probability,precipitation,rain,weather_code",
            "forecast_hours": min(48, fetch_h),
            "timezone": "auto",
        }
    )
    print(f"  {API}?{q}")
    print()


if __name__ == "__main__":
    main()
