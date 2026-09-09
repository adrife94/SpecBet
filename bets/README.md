# bets — CLI de SpecBet

CLI en Python para tomar decisiones de apuestas deportivas 1X2. Flujo completo:

```
scraper → partidos.json → betting (compare / surebet / freebet / bonus / multibonus)
```

Requiere Python 3.11+. Todos los comandos se ejecutan desde el directorio `bets/`.

---

## 1. Obtención de cuotas (`python -m scraper`)

El scraper abre páginas de casas de apuestas con Playwright y extrae las cuotas 1X2, guardándolas en un JSON que los comandos de análisis consumen.

### URLs configuradas

Las URLs de las páginas a scrapear se guardan en **`bets/urls.json`**:

```json
{
  "urls": [
    "https://www.sportium.es/apuestas/sports/soccer/competitions/45225",
    "https://m.apuestas.codere.es/deportesEs/#/EventoPage",
    "https://www.speedybet.es/betting#sports-hub/football/champions_league",
    "https://www.winamax.es/apuestas-deportivas/sports/1/800000542/151665",
    "https://canarias.retabet.es/deportes/futbol/europa/champions-league/10",
    "https://canarias.kirolbet.es/esp/Sport/Competicion/3"
  ]
}
```

Para cambiar de competición, edita este archivo con las URLs de la nueva competición y vuelve a lanzar el scraper.

### Uso

```bash
# Leer URLs de urls.json (comportamiento por defecto)
python -m scraper --output partidos.json

# Pasar URLs directamente (la casa se detecta por dominio)
python -m scraper --urls "https://www.sportium.es/..." "https://www.winamax.es/..." --output partidos.json

# Usar las URLs genéricas predefinidas por casa (fútbol general, no una competición concreta)
python -m scraper --casas sportium winamax retabet --output partidos.json

# Casas disponibles: sportium, codere, winamax, speedybet, retabet, kirolbet, 20bet, bet365

# Modo sin ventana (puede fallar en casas con anti-bot)
python -m scraper --headless --output partidos.json
```

### Notas por casa

| Casa | Observaciones |
|---|---|
| Sportium, Winamax, Speedybet, Retabet, Kirolbet | Funcionan sin sesión |
| Codere | Funciona sin sesión |
| 20bet | Requiere iniciar sesión en el navegador que se abre la primera vez |
| Bet365 | Detección de bot agresiva; puede devolver 0 partidos |

### Formato de salida (`partidos.json`)

```json
{
  "version": 1,
  "partidos": [
    {
      "partido": "Liverpool vs Atlético Madrid",
      "fecha": "2026-09-09T19:00",
      "cuotas": [
        { "casa": "Sportium",  "1": 1.72, "X": 4.0, "2": 4.33 },
        { "casa": "Winamax",   "1": 1.72, "X": 4.0, "2": 4.2  },
        { "casa": "Speedybet", "1": 1.76, "X": 4.1, "2": 4.6  }
      ]
    }
  ]
}
```

El scraper intenta consolidar partidos del mismo nombre entre casas. Si una casa escribe el nombre distinto (ej. "FC Barcelona" vs "Barcelona"), puede que aparezcan como entradas separadas — en ese caso, edita `partidos.json` manualmente o fusiona los datos antes de analizarlos.

---

## 2. Análisis de cuotas (`python -m betting`)

Todos los subcomandos leen el mismo formato JSON (Formato A, el que produce el scraper).

### `compare` — Comparador de cuotas

Muestra las mejores cuotas por resultado y el porcentaje de pago de cada mercado.

```bash
python -m betting compare partidos.json
python -m betting compare partidos.json --json          # salida JSON reutilizable
python -m betting compare partidos.json --promo Codere  # con filtro de promo
```

### `surebet` — Arbitraje 1X2

Calcula el reparto óptimo del stake para cubrir los tres resultados con beneficio garantizado.

```bash
python -m betting surebet partidos.json --inversion 100
python -m betting surebet partidos.json --inversion 100 --json
```

> Con `--promo`: lee directamente el Formato A (cuotas por casa) en vez de la salida de `compare --json`.

### `freebet` — Cobertura de freebets

Calcula la apuesta de cobertura para extraer el valor máximo de una freebet.

```bash
# Freebet única
python -m betting freebet partidos.json --casa Codere --importe 20

# Con restricciones
python -m betting freebet partidos.json --casa Codere --importe 20 \
  --min 1.5 --max 3.0 --fecha-limite 2026-09-10

# Lote de freebets desde un JSON
python -m betting freebet partidos.json --bonos bonos.json

# Con promo
python -m betting freebet partidos.json --casa Codere --importe 20 --promo Codere
```

Opciones adicionales: `--partido "Liverpool vs Atlético Madrid"`, `--resultado 1|X|2`.

### `bonus` — Rollover de bono

Encuentra la apuesta de menor coste para cumplir el requisito de rollover de un bono de depósito.

```bash
python -m betting bonus partidos.json --casa Sportium --importe 50 --min 1.8
python -m betting bonus partidos.json --casa Sportium --importe 50 --min 1.8 --fecha-limite 2026-09-10
```

### `multibonus` — Rollover coordinado de varios bonos

Coordina 2–3 bonos para que cada uno cubra un resultado distinto del mismo partido, minimizando la pérdida total.

```bash
# Definir bonos en línea (--bono se repite)
python -m betting multibonus partidos.json \
  --bono Codere:50:1.8 \
  --bono Sportium:30:2.0 \
  --bono Winamax:20:1.5

# Definir bonos en un JSON
python -m betting multibonus partidos.json --bonos bonos.json

# Excluir partidos a partir de una fecha (apalancamiento)
python -m betting multibonus partidos.json \
  --bono Codere:50:1.8 --bono Sportium:30:2.0 \
  --apalancamiento 2026-09-10
```

### `--promo` — Filtro de promociones

Disponible en `compare`, `surebet`, `freebet` y `bonus`. Indica las casas que tienen activa la promo "ventaja de 2 goles": posiciona las patas de ganar (1/2) en esas casas y muestra el coste frente al beneficio potencial (windfall).

```bash
python -m betting compare partidos.json --promo Codere,Sportium
```

---

## 3. Flujo típico

```bash
# 1. Obtener cuotas (abre ventanas de navegador)
python -m scraper --output partidos.json

# 2. Ver comparativa de cuotas
python -m betting compare partidos.json

# 3. Buscar surebets con 100 € de inversión
python -m betting surebet partidos.json --inversion 100

# 4. Cubrir una freebet de 25 € en Codere
python -m betting freebet partidos.json --casa Codere --importe 25
```

---

## 4. Tests

```bash
pytest -q
```
