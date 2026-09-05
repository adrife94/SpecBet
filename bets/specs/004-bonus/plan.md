# Plan técnico — Spec 004 (Bonus: apuesta de menor coste para el rollover)

## Estructura de módulos
- `betting/storage.py`  → se reutiliza `cargar` (Formato A, mismo JSON que
  `compare`; la `fecha` opcional ya viaja en el dict). No hace falta loader nuevo.
- `betting/core.py`     → lógica pura del bonus: config del bono, generación de
  opciones por partido/resultado, cobertura en casas distintas, coste, plazo y
  orden (RF-1..RF-24). Reutiliza `normalizar`, `verificar_duplicados`,
  `_entrada_de_casa`, `_mejor_cobertura`, `_a_cuota_valida` y `_parse_fecha`.
- `betting/cli.py`      → subcomando `bonus`, opciones del bono, render de la
  tabla, `--json`, avisos y códigos de salida (RF-18..RF-27).
- `tests/`              → pytest, uno o más tests por RF.

## Reutilización (conceptual)
El bonus es el "modo pata fija" del surebet: se **ancla** un importe en la casa
del bono a un resultado y se **reparte la cobertura** en los otros dos. La
diferencia con surebet (002) es que aquí la pata anclada es fija (no se busca la
mejor cuota) y el resultado suele ser un **coste** (margen negativo), no un
beneficio. La cobertura y la exclusión de la casa del bono son las de freebet
(003).

## Dataclasses del core
- `ConfigBonus(casa, importe, cuota_minima, fecha_limite=None)` — entrada
  normalizada (importe/cuota en `Decimal`, fecha en `datetime`).
- `Cobertura(resultado, importe, cuota, casa)` — una pata de cobertura.
- `Opcion(partido, resultado, importe, cuota, casa, coberturas, coste)` — anclar
  en un resultado de un partido, con su cobertura y su coste (sin redondear).
- `Descarte(partido, resultado, motivo)` — opción/partido no propuesto y por qué
  (`resultado` es `None` cuando el descarte es de todo el partido).
- `ResultadoBonus(config, opciones, descartes, avisos_sin_fecha)`.

## Algoritmo del coste de una opción (RF-3, RF-5, RF-7)
Con el importe `S` anclado en la casa del bono a un resultado de cuota `a`, y los
otros dos resultados cubiertos a sus mejores cuotas `b`, `c` en casas distintas:
1. Retorno garantizado: `R = S·a` (se cubre para igualarlo en los tres
   resultados, RF-5).
2. Importe de cada cobertura: `s_b = R/b`, `s_c = R/c` (cada una devuelve `R`).
3. Coste: `coste = (S + s_b + s_c) − R`, en euros (RF-7). Normalmente positivo
   (pequeña pérdida); negativo si el conjunto es un arbitraje (RF-10).

Todo en `Decimal`, sin redondear; el redondeo a 2 decimales solo al presentar.
Caso verificable a mano — `S=100`, `a=2.10`, `b=4.20`, `c=3.60`:
`R=210`; `s_b=50`, `s_c=58.33…`; `coste = (100+50+58.33…) − 210 = −1.66…` €
(arbitraje leve, coste negativo). Con `b=3.80`, `c=3.40`:
`s_b=55.26…`, `s_c=61.76…`; `coste = 217.02… − 210 = 7.02 €`.

## Generación de opciones por partido (RF-2, RF-11, RF-12, RF-13)
Para cada partido en el que participa la casa del bono (si no, descarte de todo
el partido, RF-13):
- Por cada resultado con cuota válida en la casa del bono ≥ cuota mínima (RF-2,
  RF-11; los que no llegan al mínimo se omiten sin ruido):
  - Cobertura de los otros dos resultados con `_mejor_cobertura` (mejor cuota en
    casa distinta; empate → primera por orden, RF-6). Si alguno no es cubrible →
    descarte de esa opción con motivo (RF-12).
  - Si es cubrible → se calcula la `Opcion` con su coste.

## Plazo (RF-14..RF-17)
- Con `fecha_limite` y `fecha` de partido posterior → descarte del partido "fuera
  de plazo" (RF-15). Con `fecha_limite` y partido sin `fecha` → se evalúa igual y
  se añade a `avisos_sin_fecha` (RF-16). Sin `fecha_limite` → se ignoran las
  fechas (RF-17). Comparación como `datetime` (date-only = medianoche), sin zonas.

## Orden y agregado (RF-9, RF-10)
- Todas las opciones válidas de todos los partidos se aplanan y se ordenan por
  `coste` ascendente (RF-9); las de coste negativo (arbitraje) entran en el mismo
  orden por su coste (RF-10).

## Contrato CLI
- `python -m betting bonus <cuotas.json> --casa CASA --importe N --min CUOTA
   [--fecha-limite FECHA] [--json]`
- `--min` es la cuota mínima exigida por el rollover; `--importe` es lo que
  apuestas en la casa del bono cada apuesta.
- Tabla/opciones por **stdout**; avisos (sin fecha) y recordatorio por **stderr**.
- Códigos de salida: `0` si todo fue bien (incluido archivo sin partidos, RF-22,
  y sin opciones válidas, RF-23); `1` ante importe ≤ 0 (RF-18), cuota mínima ≤ 1
  (RF-19), casa no indicada (RF-20) o archivo inexistente/corrupto/repetidos
  (RF-21).

## Modelo de datos — salida JSON (RF-25)
```
{
  "version": 1,
  "casa": "Luckia",
  "importe": "100.00",
  "cuota_minima": "1.50",
  "opciones": [
    {
      "partido": "A vs B", "resultado": "2", "cuota": "2.10",
      "importe": "100.00", "casa": "Luckia", "coste": "7.02",
      "cobertura": [
        {"resultado": "1", "importe": "55.26", "cuota": "3.80", "casa": "Bet365"},
        {"resultado": "X", "importe": "61.76", "cuota": "3.40", "casa": "Winamax"}
      ]
    }
  ],
  "descartes": [
    {"partido": "C vs D", "resultado": null, "motivo": "La casa 'Luckia' no participa..."},
    {"partido": "A vs B", "resultado": "1", "motivo": "no cubrible en casa distinta"}
  ]
}
```
- Importes, cuotas y coste como **string** (sin `float`).

## Decisiones técnicas
- argparse (stdlib), añadiendo el subcomando `bonus` → constitución nº 1.
- Reutiliza `storage.cargar`, `core.normalizar`, `core.verificar_duplicados` y los
  helpers de cobertura/fecha de la spec 003.
- Core puro; el redondeo (`quantize`, ROUND_HALF_UP) vive en la CLI.

## Estrategia de tests
- **core (coste)**: caso numérico verificado a mano (coberturas que igualan el
  retorno en los tres resultados y su coste; incluido un caso de coste negativo).
- **core (opciones)**: una opción por resultado ≥ mínima; resultado bajo la mínima
  se omite; resultado no cubrible → descarte con motivo; cobertura excluye la casa
  del bono; casa del bono ausente → descarte del partido.
- **core (plazo/orden)**: fuera de plazo descartado; sin fecha con límite → aviso;
  sin límite ignora fechas; opciones ordenadas por coste ascendente.
- **config**: importe ≤ 0, cuota mínima ≤ 1, casa ausente, fecha inválida → error.
- **CLI**: tabla de opciones ordenadas con cuota anclada; `--json` parseable y
  coherente; importe/cuota mínima/casa inválidos → salida ≠ 0; archivo corrupto →
  ≠ 0; sin partidos y sin opciones → salida 0; avisos y recordatorio por stderr.
