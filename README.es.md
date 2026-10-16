# RainSoon

[English](README.md) · [Português](README.pt-BR.md) · **Español**

Alertas de lluvia en **Home Assistant** con **[Open-Meteo](https://open-meteo.com/)** — gratis, sin API key, listo para **Alexa**, paneles y automatizaciones.

## Qué hace

- Analiza la previsión **horaria** de tu ubicación.
- Avisa cuando la lluvia cumple **tus umbrales** (probabilidad + mm/h).
- Textos para voz en **español, inglés o portugués** (`message` / `message_short`).
- Sensores del tiempo **ahora** y del **período de previsión**.

## Instalación (HACS)

1. HACS → repositorio personalizado → `https://github.com/th3junior/RainSoon` → instalar → reiniciar HA.
2. **Ajustes → Dispositivos y servicios → Añadir integración → RainSoon**
   - **Ubicación**
   - **Idioma** (mensajes Alexa y nombres de sensores; independiente del idioma de la UI de HA)
   - Perfil **Equilibrado**

Cambios posteriores: **RainSoon → Opciones**.

## Período de previsión

**No es una ventana física.** Son **cuántas horas hacia adelante** se analizan (recomendado **12–24 h**).

| Sensor | Significado |
|--------|-------------|
| **`binary_sensor.*_chuva_prevista`** | Lluvia que cumple **tus umbrales** en ese período |
| **Lluvia total / mayor en el período** | Suma o pico dentro del mismo rango de horas |
| **`sensor.*_max_probabilidade`** | Máxima probabilidad horaria **sin** aplicar umbrales (informativo) |

Si no hay alerta, algunos sensores pueden mostrar **desconocido**; usa **`message`** / **`message_short`** en **`proxima_chuva`**.

Sin lluvia (ejemplo): *En las próximas 12 horas, no se espera lluvia.*

## Alexa

Automatizaciones: [`docs/automations-alexa.yaml`](docs/automations-alexa.yaml).

## Dominio `rainsoon`

Si usabas `rain_alert`, elimina la integración antigua, actualiza por HACS y vuelve a añadir **RainSoon**.

## Licencia

MIT — [LICENSE](LICENSE).
