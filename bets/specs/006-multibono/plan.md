# Plan técnico — Spec 006 (Multibono: rollover coordinado)

## Estructura de módulos
- `betting/storage.py`  → se reutiliza `cargar` (Formato A, mismo JSON que
  `compare`; la `fecha` opcional ya viaja en el dict) y `cargar_bonos` de la spec
  003 para el archivo de bonos (`casa`, `importe` y `min` por bono; el resto de
  campos se ignoran aquí). No hace falta loader nuevo.
- `betting/core.py`     → lógica pura del multibono: normalización de la lista de
  bonos, asignación bono→resultado de menor pérdida, retorno objetivo (techo),
  relleno con dinero real, métricas (pérdida €/%, dinero real, neto), plazo y orden
  (RF-1..RF-28, RF-33, RF-34). Reutiliza `normalizar`, `verificar_duplicados`,
  `_entrada_de_casa`, `_a_cuota_valida` y `_parse_fecha`; generaliza la búsqueda de
  mejor cobertura a "excluyendo un conjunto de casas".
- `betting/cli.py`      → subcomando `multibonus`, bonos por flag repetible o por
  `--bonos`, `--apalancamiento`, render de la tabla, `--json`, avisos y códigos de
  salida (RF-2..RF-6, RF-29..RF-32).
- `tests/`              → pytest, uno o más tests por RF.

## Reutilización (conceptual)
El multibono es el bonus (004) con **varias patas ancladas a la vez**: en vez de
anclar un importe y cubrir los otros dos resultados con dinero real, se anclan 2 o
3 bonos —uno por resultado— y solo se **rellena con dinero real lo que falte** para
igualar el retorno. Diferencias con 004:
- El retorno objetivo no es `S·a` de una pata, sino el **techo** `R = máx(importe·cuota)`
  entre las patas de bono (RF-12).
- Se elige la **asignación** bono→resultado de menor pérdida (RF-9); en 004 no hay
  asignación (una sola pata).
- El relleno/cobertura excluye **todas** las casas de bono, no solo una
  (constitución nº 10, generalizada).
- La métrica de orden es la **pérdida** (€ y % sobre el bono), con el **dinero real**
  como dato secundario (RF-18..RF-23), no el `coste` de una pata.

## Dataclasses del core
- `Bono(casa, importe, cuota_minima)` — entrada normalizada (importe/cuota en
  `Decimal`).
- `ConfigMulti(bonos: list[Bono], fecha_apalancamiento=None)` — 2 o 3 bonos, casas
  distintas; fecha en `datetime`.
- `Pata(tipo, resultado, importe, cuota, casa)` — `tipo` es `"bono"` o `"relleno"`.
- `Opcion(partido, R, patas, dinero_real, perdida, perdida_pct, neto)` — la
  colocación elegida de un partido, sin redondear.
- `Descarte(partido, motivo)` — partido no propuesto y por qué.
- `ResultadoMulti(config, opciones, descartes, avisos_sin_fecha)`.

## Algoritmo de una opción (por partido y asignación) (RF-7, RF-12..RF-21)
Dada una asignación de los bonos a resultados distintos, con cada bono `i` de
importe `S_i` anclado a un resultado de cuota `a_i` en su casa:
1. Retorno de cada pata de bono: `B_i = S_i · a_i`.
2. Techo: `R = máx(B_i)` sobre las patas de bono (RF-12). La pata que marca el techo
   no lleva relleno.
3. Relleno de cada resultado por debajo de `R`:
   - Pata de bono con `B_i < R`: falta `R − B_i`; se apuesta dinero real a la mejor
     cuota `q` de ese resultado en una casa **distinta de todas las de bono**,
     `s = (R − B_i)/q` (RF-13, RF-15).
   - Resultado sin bono (caso de 2 bonos): se cubre entero, `s = R/q` (RF-14).
4. Dinero real: `real = Σ s`. Total apostado: `T = Σ S_i + real`.
5. Pérdida: `perdida = T − R` (RF-18). % sobre el bono: `perdida_pct =
   perdida / Σ S_i · 100` (RF-19). Neto: `neto = R − real` (RF-21).

Todo en `Decimal`, sin redondear; el redondeo a 2 decimales solo al presentar
(constitución nº 8).

**Caso verificable a mano** — 3 bonos de `100`; mejores cuotas del partido `1=1.50`
(Luckia), `X=4.00` (Bet365), `2=6.00` (Winamax); relleno disponible en casas
distintas a `1.50` y `4.00`:
- `B = 150, 400, 600` → `R = 600`.
- Relleno `1`: `(600−150)/1.50 = 300`; relleno `X`: `(600−400)/4.00 = 50`; `2`: 0.
- `real = 350`; `T = 300 + 350 = 650`; `perdida = 650 − 600 = 50 €`;
  `perdida_pct = 50/300 = 16.67 %`; `neto = 600 − 350 = 250`.

**Contraste de orden** — mismos 3 bonos en un partido `2.60/2.60/2.60`:
`B = 260,260,260` → `R = 260`, sin relleno; `perdida = 300 − 260 = 40 € (13.33 %)`,
`real = 0`, `neto = 260`. Pierde **menos** que el partido anterior pese a peor
payout, así que se ordena **por encima** (RF-22, RF-23).

## Elección de la asignación (RF-8..RF-11)
Para cada partido se prueban las asignaciones **válidas** y se elige la de **menor
pérdida** (RF-9). Una asignación es válida si:
- Cada bono se ancla en un resultado distinto (RF-7, RF-10) y la cuota de ese
  resultado en su casa es `≥` su `cuota_minima` (RF-8, constitución nº 11).
- Todo resultado que requiera dinero real tiene al menos una casa **distinta de las
  de bono** con cuota válida (si no, esa asignación no sirve; RF-16).

Con 3 bonos son ≤ 6 permutaciones; con 2 bonos, elegir 2 de los 3 resultados y su
orden (≤ 6 combinaciones) dejando el tercero a dinero real (RF-11). Con importes
iguales varias permutaciones empatan; se toma la primera de menor pérdida
(determinista por orden 1, X, 2). Si **ninguna** asignación es válida → descarte del
partido con motivo (RF-16, RF-17).

## Relleno con dinero real (RF-15, RF-16)
- `_mejor_cuota_excluyendo(entradas, resultado, casas_excluidas)` → mejor cuota
  válida del resultado entre las casas que no son de bono; ante empate, la primera
  por orden de entrada. Es `_mejor_cobertura` (004) generalizada a excluir un
  **conjunto** de casas en vez de una.
- Si un resultado a rellenar no tiene ninguna casa válida fuera de las de bono, la
  asignación se descarta; si arrastra a todo el partido, `Descarte` con motivo.

## Plazo (RF-25..RF-28)
- `fecha_apalancamiento` actúa como fecha límite: partido con `fecha` **en esa fecha
  o posterior** → descarte "fuera de plazo" (RF-26); el rollover debe cerrarse antes.
- Con `fecha_apalancamiento` y partido sin `fecha` → se evalúa igual y se añade a
  `avisos_sin_fecha` (RF-27). Sin `fecha_apalancamiento` → se ignoran las fechas y
  se recuerda cerrar el rollover antes del apalancamiento (RF-28).
- Comparación como `datetime` (date-only = medianoche), sin zonas horarias.

## Orden y agregado (RF-22, RF-24, RF-33, RF-34)
- Todas las opciones válidas de todos los partidos se aplanan y se ordenan por
  `perdida` ascendente (RF-22); las de pérdida negativa (arbitraje) entran en el
  mismo orden por su valor (RF-24).
- Archivo sin partidos → `opciones` vacías, salida 0 (RF-33). Ningún partido con
  opción válida → `opciones` vacías + descartes, salida 0 (RF-34).

## Contrato CLI
- Bonos por flag repetible:
  `python -m betting multibonus <cuotas.json> --bono CASA:IMPORTE:MIN
   --bono CASA:IMPORTE:MIN [--bono CASA:IMPORTE:MIN] [--apalancamiento FECHA] [--json]`
- Bonos por archivo (reutiliza el JSON de bonos de la 003):
  `python -m betting multibonus <cuotas.json> --bonos <bonos.json>
   [--apalancamiento FECHA] [--json]`
- `--bono` y `--bonos` son mutuamente excluyentes; deben resultar **2 o 3** bonos
  (RF-2), con casas distintas (RF-4), importe > 0 y `MIN` > 1 (RF-3).
- Tabla/opciones por **stdout**; avisos (plazo, sin fecha) y el recordatorio de
  verificar cuotas por **stderr** (RF-27, RF-32).
- Códigos de salida: `0` si todo fue bien (incluido archivo sin partidos, RF-33, y
  sin opciones válidas, RF-34); `1` ante menos de 2 o más de 3 bonos (RF-2),
  importe ≤ 0 o `MIN` ≤ 1 (RF-3), casas de bono repetidas (RF-4), archivo
  inexistente/corrupto/estructura inesperada/repetidos (RF-5) o fecha no
  interpretable.

## Modelo de datos — salida JSON (RF-30)
```
{
  "version": 1,
  "bonos": [
    {"casa": "Luckia",  "importe": "100.00", "cuota_minima": "1.50"},
    {"casa": "Bet365",  "importe": "100.00", "cuota_minima": "1.50"},
    {"casa": "Winamax", "importe": "100.00", "cuota_minima": "1.50"}
  ],
  "opciones": [
    {
      "partido": "A vs B",
      "R": "600.00", "dinero_real": "350.00",
      "perdida": "50.00", "perdida_pct": "16.67", "neto": "250.00",
      "patas": [
        {"tipo": "bono",    "resultado": "1", "importe": "100.00", "cuota": "1.50", "casa": "Luckia"},
        {"tipo": "relleno", "resultado": "1", "importe": "300.00", "cuota": "1.50", "casa": "Codere"},
        {"tipo": "bono",    "resultado": "X", "importe": "100.00", "cuota": "4.00", "casa": "Bet365"},
        {"tipo": "relleno", "resultado": "X", "importe": "50.00",  "cuota": "4.00", "casa": "Pokerstars"},
        {"tipo": "bono",    "resultado": "2", "importe": "100.00", "cuota": "6.00", "casa": "Winamax"}
      ]
    }
  ],
  "descartes": [
    {"partido": "C vs D", "motivo": "La casa 'Winamax' no participa en el partido"}
  ]
}
```
- Importes, cuotas, R, pérdida, % y neto como **string** (sin `float`).

## Decisiones técnicas
- argparse (stdlib), añadiendo el subcomando `multibonus` → constitución nº 1.
- Reutiliza `storage.cargar`, `storage.cargar_bonos`, `core.normalizar`,
  `core.verificar_duplicados`, `_entrada_de_casa`, `_a_cuota_valida` y `_parse_fecha`;
  generaliza `_mejor_cobertura` a `_mejor_cuota_excluyendo(casas)`.
- Núcleo puro sin IO; el redondeo (`quantize`, ROUND_HALF_UP) vive en la CLI.
- La asignación es fuerza bruta sobre ≤ 6 combinaciones: simple y sin dependencias
  (constitución nº 1).

## Estrategia de tests
- **core (opción, 3 bonos)**: caso numérico verificado a mano (relleno que iguala R
  en los tres resultados; pérdida €/%, dinero real y neto); incluye un partido con
  pérdida negativa (arbitraje) mostrado con pérdida negativa.
- **core (opción, 2 bonos)**: dos bonos anclados y el tercer resultado cubierto solo
  con dinero real hasta R.
- **core (asignación)**: con bonos de importes distintos, se elige la permutación de
  menor pérdida; empate determinista por orden 1, X, 2.
- **core (relleno/exclusión)**: el relleno excluye todas las casas de bono; empate
  de cuota → primera por orden; resultado no rellenable fuera de las casas de bono →
  descarte con motivo; casa de bono ausente del partido → descarte con motivo.
- **core (plazo/orden)**: partido en/after apalancamiento descartado; sin fecha con
  apalancamiento → aviso pero se evalúa; sin apalancamiento se ignoran fechas;
  opciones ordenadas por pérdida ascendente (el parejo mal pagado por encima del
  desequilibrado más caro y viceversa, según pérdida).
- **config**: menos de 2 o más de 3 bonos, importe ≤ 0, cuota mínima ≤ 1, casas de
  bono repetidas, fecha inválida → error.
- **CLI**: tabla de opciones ordenadas con las patas de bono y de relleno; `--bono`
  repetible y `--bonos` archivo; `--json` parseable y coherente; entradas inválidas
  → salida ≠ 0; archivo corrupto → ≠ 0; sin partidos y sin opciones → salida 0;
  avisos y recordatorio por stderr.
