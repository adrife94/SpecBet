# Plan técnico — Spec 003 (Freebet: cobertura y valor)

## Estructura de módulos
- `betting/storage.py`  → reutilizar `cargar` (Formato A, mismo JSON que
  `compare`) para las cuotas; añadir `cargar_bonos(ruta)` para el JSON de bonos
  del lote (RF-19, RF-28). La `fecha` opcional del partido ya viaja en el dict
  que devuelve `cargar` (no hace falta tocar la validación existente).
- `betting/core.py`     → lógica pura del freebet: conversión de una colocación
  (cobertura + valor extraído), elección del resultado, rango de cuota, plazo,
  evaluación por partido, orden, recomendada, lote y colisiones (RF-1..RF-15,
  RF-23..RF-34). Reutiliza `normalizar` y `verificar_duplicados` de la spec 001.
- `betting/cli.py`      → subcomando `freebet`, opciones de un bono o `--bonos`
  para el lote, render de la tabla (listado por partido con valor y % de
  conversión), `--json`, avisos y códigos de salida (RF-16..RF-22, RF-26, RF-31).
- `tests/`              → pytest, uno o más tests por RF.

## Modelo de datos — cuotas (Formato A, extendido con `fecha`)
Mismo JSON que `compare`, con una `fecha` **opcional** por partido:

```
{
  "version": 1,
  "partidos": [
    {
      "partido": "Madrid vs Barça",
      "fecha": "2026-09-10",              // opcional, ISO 8601 (date o datetime)
      "cuotas": [
        { "casa": "Luckia",  "1": 3.60, "X": 3.30, "2": 2.10 },
        { "casa": "Bet365",  "1": 3.50, "X": 3.40, "2": 2.05 },
        { "casa": "Winamax", "1": 3.55, "X": 3.25, "2": 2.08 }
      ]
    }
  ]
}
```

- La `fecha` ausente no impide el cálculo (RF-23); `compare` y `surebet` la
  ignoran. Se carga como string y se interpreta con `datetime.fromisoformat`.

## Modelo de datos — bonos del lote (`--bonos`)
Cargado con `parse_float=Decimal`. `casa` e `importe` obligatorios; el resto
opcional:

```
{
  "version": 1,
  "bonos": [
    { "casa": "Luckia",   "importe": 10, "fecha_limite": "2026-09-12",
      "min": 1.5, "max": 3.5, "partido": "Madrid vs Barça", "resultado": "1" },
    { "casa": "Sportium", "importe": 100 }
  ]
}
```

- Un solo bono puede darse por flags en vez de archivo (ver Contrato CLI).
- `min`/`max` = rango de cuota de la pata gratis; `partido`/`resultado` = fijar
  la jugada; `fecha_limite` = plazo de esa freebet.

## Dataclasses del core
- `Bono(casa, importe, fecha_limite=None, cuota_min=None, cuota_max=None,
  partido=None, resultado=None)` — entrada normalizada (importe/cuotas `Decimal`,
  fechas `datetime`).
- `Pata(tipo, resultado, importe, cuota, casa)` — una apuesta: `tipo` es
  `"gratis"` o `"cobertura"`.
- `Jugada(partido, resultado_gratis, patas, valor_extraido, conversion)` — la
  colocación de la freebet en un partido y su valor (`conversion` = valor/importe).
- `EvalPartido(partido, fecha, jugable, motivo, jugada, aviso_sin_fecha)` — un
  partido evaluado para un bono (jugada o motivo de no jugable).
- `ResultadoBono(bono, partidos, recomendada, valor_extraido, sin_plan)` — el
  listado ordenado de un bono y su recomendada.
- `ResultadoLote(resultados, valor_total, conversion_total, colisiones)`.

## Algoritmo de conversión de una freebet (RF-2, RF-3, RF-11)
Pata gratis en el resultado A a cuota `a` (casa del bono), freebet `F`. Los otros
dos resultados B y C se cubren con dinero real a sus mejores cuotas `b`, `c`
entre las casas distintas de la del bono. Igualando el beneficio neto en los tres
resultados (stake gratis no retornado):

1. Retorno común de cobertura: `R = F·(a−1)`.
2. Importe de cada cobertura: `s_B = R/b`, `s_C = R/c`.
3. Valor extraído (beneficio garantizado, igual gane quien gane):
   `V = R − (s_B + s_C) = F·(a−1)·(1 − 1/b − 1/c)`.
4. % de conversión: `V / F = (a−1)·(1 − 1/b − 1/c)` (RF-4).

Todo en `Decimal`, sin redondear; el redondeo a 2 decimales solo al presentar
(constitución nº 8). Caso verificable a mano — `a=3.60`, `b=3.40`, `c=2.10`,
`F=10`: `R=26.00`; `1/3.40+1/2.10 = 0.294117…+0.476190… = 0.770308…`;
`V = 26·(1 − 0.770308…) = 26·0.229691… ≈ 5.97 €` → conversión ≈ 59.72 %.

## Elección del resultado y restricciones (RF-6..RF-13, RF-24..RF-27)
- Un resultado A es **admisible** para la pata gratis si: la casa del bono ofrece
  A con cuota válida (> 1) y dentro del rango `[min, max]` si se indicó (RF-9), y
  los otros dos resultados son **cubribles** (cada uno con al menos una casa
  distinta de la del bono y cuota válida) (RF-11, RF-13).
- Cobertura de cada resultado: mejor cuota entre las casas distintas de la del
  bono; ante empate, la primera por orden de entrada (RF-11, RF-12). Las dos
  coberturas pueden caer en la misma casa (RF-12); nunca en la del bono (RF-2).
- Sin resultado fijado: se elige el admisible con mayor valor extraído (RF-6).
  Con resultado fijado: solo ese; si su cuota queda fuera de rango o no es
  cubrible, la jugada no se propone y se informa del motivo (RF-7, RF-10).
- Plazo: con `fecha_limite` y `fecha` de partido posterior → fuera de plazo, no
  jugable (RF-24, RF-25); con `fecha_limite` y partido sin `fecha` → se evalúa
  igual pero con aviso (RF-26); sin `fecha_limite` → se ignoran las fechas
  (RF-27). `fecha_partido ≤ fecha_limite` se compara como `datetime` (date-only
  = medianoche; sin zonas horarias).

## Orden, recomendada y lote (RF-14, RF-15, RF-28..RF-34)
- Por bono: una fila por partido con el valor extraído de su mejor jugada,
  ordenadas de mayor a menor valor; los no jugables (casa ausente, fuera de
  plazo, sin cobertura, todo fuera de rango) al final con su motivo (RF-14,
  RF-15). La primera fila jugable es la **recomendada** (RF-33). Se detallan las
  patas de cada partido, no solo de la recomendada (RF-34).
- Lote: cada bono se evalúa independiente aplicando lo anterior (RF-28, RF-29).
  `valor_total` = suma del valor extraído recomendado de cada bono; el bono sin
  jugada válida cuenta 0 y se marca sin plan (RF-30, RF-32). `conversion_total` =
  `valor_total / Σ importes`.
- Colisión (RF-31): si las jugadas recomendadas de dos bonos comparten una pata
  con el mismo (partido, resultado, casa), se avisa para consolidar; es
  informativo, no altera el cálculo.

## Contrato CLI
- Un bono por flags:
  `python -m betting freebet <cuotas.json> --casa CASA --importe N
   [--fecha-limite F] [--min M] [--max X] [--partido P] [--resultado 1|X|2]
   [--json]`
- Lote por archivo:
  `python -m betting freebet <cuotas.json> --bonos <bonos.json> [--json]`
- `--bonos` y los flags de un bono son mutuamente excluyentes; sin `--casa` ni
  `--bonos` → error (RF-18).
- Tabla/listado por **stdout**; avisos (plazo, sin fecha, colisión) y el
  recordatorio de verificar cuotas por **stderr** (RF-22, RF-26, RF-31).
- Códigos de salida: `0` si todo fue bien (incluido archivo sin partidos, RF-20);
  `1` ante importe ≤ 0 / no numérico (RF-17), casa no indicada (RF-18), archivo
  inexistente/corrupto/estructura inesperada/repetidos (RF-19), resultado fijado
  inválido, o fecha no interpretable.

## Modelo de datos — salida JSON (RF-21)
```
{
  "version": 1,
  "valor_total": "5.97",
  "conversion_total": "59.72",
  "bonos": [
    {
      "casa": "Luckia", "importe": "10.00",
      "sin_plan": false,
      "recomendada": "Madrid vs Barça",
      "partidos": [
        {
          "partido": "Madrid vs Barça", "fecha": "2026-09-10",
          "jugable": true, "motivo": null, "aviso_sin_fecha": false,
          "valor_extraido": "5.97", "conversion": "59.72",
          "patas": [
            {"tipo": "gratis",    "resultado": "1", "importe": "10.00", "cuota": "3.60", "casa": "Luckia"},
            {"tipo": "cobertura", "resultado": "X", "importe": "7.65",  "cuota": "3.40", "casa": "Bet365"},
            {"tipo": "cobertura", "resultado": "2", "importe": "12.38", "cuota": "2.10", "casa": "Winamax"}
          ]
        }
      ]
    }
  ],
  "colisiones": []
}
```
- Importes, cuotas, valor y % como **string** (sin `float`). Partido no jugable:
  `jugada`/patas ausentes o `patas: []`, `valor_extraido`/`conversion` a `null` y
  `motivo` con el texto.

## Decisiones técnicas
- argparse (stdlib), añadiendo el subcomando `freebet` → constitución nº 1.
- Reutiliza `storage.cargar`, `core.normalizar` y `core.verificar_duplicados` de
  la 001: la entrada de cuotas es el mismo Formato A con las mismas reglas de
  duplicados (RF-19).
- Fechas con `datetime.fromisoformat` (stdlib), comparación cronológica directa;
  sin zonas horarias (spec).
- Core puro sin IO; el redondeo (`quantize`, ROUND_HALF_UP) vive en la CLI.

## Estrategia de tests
- **storage**: `cargar_bonos` con `tmp_path` — inexistente, JSON inválido, sin
  `bonos`, bono sin `casa`/`importe`; `importe`/`min`/`max` a `Decimal`.
- **core (conversión)**: caso numérico verificado a mano (patas que dejan el
  mismo neto en los tres resultados, valor y % de conversión).
- **core (elección/restricciones)**: auto elige el de mayor valor; resultado
  fijado; cuota fuera de rango no se propone; cobertura excluye la casa del bono;
  resultado no cubrible; empate de cobertura determinista.
- **core (partido/plazo)**: casa ausente → no jugable; fuera de plazo; sin fecha
  con límite → aviso pero se evalúa; orden por valor y no jugables al final;
  recomendada = primera.
- **core (lote)**: dos bonos independientes, valor y % total; bono sin plan no
  tumba el lote; colisión detectada.
- **CLI**: un bono por flags (tabla con valor y % de conversión); `--bonos`
  (lote con total); `--json` parseable y coherente; importe inválido / casa no
  indicada / archivo corrupto → salida ≠ 0; sin partidos → salida 0; avisos y
  recordatorio por stderr.
