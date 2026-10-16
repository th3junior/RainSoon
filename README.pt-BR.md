# RainSoon

[English](README.md) · **Português** · [Español](README.es.md)

Alertas de chuva no **Home Assistant** com **[Open-Meteo](https://open-meteo.com/)** — gratuito, sem API key, pensado para **Alexa**, painéis e automações.

## O que faz

- Previsão **horária** para o local configurado.
- Alerta quando a chuva **atinge seus limiares** (probabilidade + mm/h).
- Textos prontos para falar em **português, inglês ou espanhol** (atributos `message` / `message_short`).
- Sensores de clima **agora** e estatísticas do **período analisado**.

## Instalação (HACS)

1. HACS → repositório customizado → `https://github.com/th3junior/RainSoon` → instalar **RainSoon** → reiniciar o HA.
2. **Configurações → Dispositivos e serviços → Adicionar integração → RainSoon**
   - **Localização** (casa ou mapa).
   - **Idioma** — mensagens Alexa, nomes dos sensores e descrições do tempo (**não** depende do idioma da interface do HA).
   - **Perfil** → **Equilibrado** (recomendado).

Depois: **RainSoon → Opções** para mudar idioma, período, limiares ou intervalo de atualização.

## Período analisado

**Não é janela física.** São **quantas horas à frente** (a partir de agora) o RainSoon analisa (recomendado **12–24 h**).

- **`binary_sensor.*_chuva_prevista`** liga só se **alguma hora** nesse intervalo passar nos seus limiares.
- Sensores **“no período”** (chuva acumulada, maior intensidade, pico de vento) usam **o mesmo intervalo**.

## Perfis de alerta

| Perfil | Período | Prob. mín. | Chuva mín. |
|--------|---------|------------|------------|
| **Equilibrado** | 12 h | 50% | 0,1 mm/h |
| **Só chuva relevante** | 12 h | 70% | 0,5 mm/h |
| **Alerta cedo** | 24 h | 40% | 0,05 mm/h |
| **Personalizado** | Você define | — | — |

## Entidades principais

Exemplo: `sensor.rainsoon_proxima_chuva`.

| Entidade | Uso |
|----------|-----|
| **`sensor.*_proxima_chuva`** | Minutos até a **primeira hora de alerta**; **`message`**, **`message_short`**, **`rain_expected`**, **`lookahead_hours`**. |
| **`binary_sensor.*_chuva_prevista`** | Chuva prevista **nos seus limiares**. |
| **`binary_sensor.*_chuva_agora`** | Chuva **agora** no local. |
| **`sensor.*_max_probabilidade`** | **Maior** probabilidade de chuva **em qualquer hora** do período (**sem** aplicar limiar — informativo). |
| **`sensor.*_proxima_probabilidade`** | Probabilidade na **primeira hora de alerta** (desconhecido se não houver alerta). |

### “Desconhecido” em alguns sensores

Com **`chuva_prevista`** desligado, **Próxima chuva** (minutos) e **Probabilidade da próxima chuva** podem ficar **desconhecidos** — não há “próximo alerta”. Use **`message`** / **`message_short`** em **`proxima_chuva`** na Alexa (inclusive **sem chuva**).

### Probabilidade máxima vs chuva prevista

Com limiar em **99%**, a **máxima no período** pode ser **40%** e **`chuva_prevista`** continua **desligado**. A **`message`** explica: sem chuva nos seus critérios e cita as **próximas N horas**.

Exemplo sem chuva: *Nas próximas 12 horas, não há chuva prevista.*

## Alexa

```yaml
action:
  - service: notify.alexa_media
    data:
      message: "{{ state_attr('sensor.rainsoon_proxima_chuva', 'message_short') }}"
      target: media_player.echo_sala
```

Resumo da manhã (com ou sem chuva): [`docs/automations-alexa.yaml`](docs/automations-alexa.yaml).

## Migração de `rain_alert`

Domínio atual: **`rainsoon`**. Remova a integração/pasta antiga `rain_alert`, atualize pelo HACS, readicione o RainSoon e ajuste automações para `rainsoon_*`.

## Desenvolvimento

```bash
pip install pytest homeassistant
pytest
```

## Licença

MIT — [LICENSE](LICENSE).
