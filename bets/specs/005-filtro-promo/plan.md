# Plan técnico — Spec 005 (Filtro de promo "ventaja de 2 goles")

## Estructura de módulos
- `betting/core.py`  → bloque nuevo "Spec 005: filtro de promo". Lógica pura: el
  filtro (`FiltroPromo`), el posicionamiento de una pata de ganar en las casas de
  la promo (coste relativo y casa de referencia), las tres opciones de
  posicionamiento por partido (asegurar 1, 2, ambos) y el windfall donde haya
  importes. Reutiliza `normalizar`, `_a_cuota_valida` y `_entrada_de_casa`.
- `betting/cli.py`   → flag global `--promo CASA[,CASA...]` en `compare`, `surebet`,
  `freebet` y `bonus`; render del bloque de promo (coste, casa de referencia y
  windfall) en tabla y `--json`; avisos y recordatorio.
- `tests/`           → pytest, uno o más tests por RF.

## Reutilización (conceptual)
El filtro **no reimplementa** cada comando: es una capa que, sobre el **detalle por
casa** (Formato A), recalcula la mejor cuota de las **patas de ganar** (resultados
1 y/o 2) restringiéndola a las casas de la promo, y expone dos magnitudes
deterministas: **coste relativo** (retorno perdido frente a la mejor casa sin
restricción) y **windfall** (pago extra si salta la ventaja de 2 goles). La X nunca
se restringe (RF-7). No calcula probabilidades (fuera de alcance).

## Dataclasses del core
- `FiltroPromo(casas: frozenset[str])` — claves normalizadas de las casas con
  promo. Construido por `construir_filtro_promo(casas: list[str])`, que valida que
  la lista no sea vacía (RF-3) y normaliza (RF-5).
- `PataPromo(resultado, casa, cuota, casa_referencia, cuota_referencia)` — una pata
  de ganar asegurada: la mejor casa **de la lista** para ese resultado (`casa`,
  `cuota`) y la mejor casa **sin restricción** de referencia (`casa_referencia`,
  `cuota_referencia`). Cuotas en `Decimal`. El coste y el windfall en euros se
  derivan de aquí cuando hay importe (no se guardan en la pata).
- `OpcionPromo(nombre, patas)` — una de las tres opciones ("asegurar 1", "asegurar
  2", "asegurar ambos") con sus `PataPromo` (una o dos).
- `PromoPartido(partido, opciones, avisos)` — las tres opciones de un partido y los
  avisos (p. ej. ninguna casa de la lista cotiza una pata, RF-10).

## Algoritmo del posicionamiento (RF-6..RF-13)
Para un resultado de ganar `r ∈ {1, 2}` en un partido (detalle por casa):
1. `cuota, casa` = mejor cuota de `r` **entre las casas de la lista** que la
   ofrecen (empate → primera por orden de entrada). Si ninguna la ofrece → no se
   puede asegurar esa pata: se omite de las opciones que la requieran y se añade un
   aviso (RF-10).
2. `cuota_referencia, casa_referencia` = mejor cuota de `r` **entre todas** las
   casas (sin restricción).
3. Con eso se arma la `PataPromo`. El **coste relativo** se calcula al presentar:
   - con importe `s` en esa pata: `coste = s · (cuota_referencia − cuota)` (RF-11);
   - la casa de referencia se nombra siempre (RF-12);
   - si `cuota == cuota_referencia` (la mejor cuota ya es de la lista) → `coste = 0`
     (RF-13, seguro sin coste).
4. **Windfall** (RF-14, donde haya importe): `windfall = s · cuota` (lo que
   cobrarías de la casa con promo si salta la ventaja de 2 goles, además de la
   cobertura del resultado real).

Las tres opciones por partido (RF-4, RF-17): "asegurar 1" (solo pata 1), "asegurar
2" (solo pata 2) y "asegurar ambos" (patas 1 y 2). En "asegurar ambos" se avisa de
que los dos windfalls **pueden acumularse** (doble remontada que acaba en empate,
RF-15).

Todo en `Decimal`, sin redondear; el redondeo a 2 decimales solo al presentar
(constitución nº 8).

**Caso verificable a mano** — resultado "1": mejor cuota entre casas de promo `2.00`
(Bet365), mejor cuota sin restricción `2.10` (Winamax); importe en la pata `50 €`:
- `coste = 50 · (2.10 − 2.00) = 5.00 €` (referencia: Winamax).
- `windfall = 50 · 2.00 = 100.00 €`.
Si la mejor cuota de "1" ya fuera de una casa de promo (`2.10` en Bet365) →
`coste = 0` (seguro gratis) y `windfall = 50 · 2.10 = 105.00 €`.

## Integración por comando

### compare (RF-16, RF-18) — sin importes
- Sobre el Formato A, además del payout normal, calcula el payout **con las patas
  aseguradas** (sustituyendo la mejor cuota de 1 y/o 2 por la de la casa de promo)
  para cada una de las tres opciones. El **coste relativo** se expresa como la
  caída de % de pago (payout normal − payout asegurado), nombrando la casa de
  referencia de cada pata. Sin windfall en euros (RF-16).

### surebet (RF-19) — con importes
- Con `--promo`, surebet parte del **Formato A** (detalle por casa), no del resumen
  de `compare --json` (el filtro necesita el detalle; RNF). Calcula las mejores
  cuotas él mismo (reutiliza `mejores_de_partido`) y, por cada opción de promo,
  rehace el reparto usando la cuota asegurada en 1 y/o 2. Muestra el coste (con la
  cuota de reparto de esa pata como importe `s`) y el windfall `s · cuota`.

### freebet (RF-20) y bonus (RF-21) — con importes
- El filtro solo posiciona las **coberturas de los resultados de ganar** (1 y/o 2)
  que el sistema elige; **no** toca la pata gratis (freebet) ni la anclada (bonus),
  aunque caigan en una casa de la lista (fuera de alcance). Cuando una cobertura de
  1 o 2 se asegura, su cuota se elige **entre las casas de la lista** (en vez de la
  mejor en casa distinta), respetando además la regla de casa distinta a la del
  bono (constitución nº 10). Coste y windfall se calculan sobre el importe de esa
  cobertura.

## Activación y comportamiento base (RF-1, RF-2)
- `--promo` desactivado → los cuatro comandos se comportan **exactamente** igual que
  hoy (ninguna rama nueva en el cálculo base).
- `--promo` activado con lista vacía → error y salida ≠ 0 (RF-3).

## Contrato CLI
- Flag global en los cuatro subcomandos:
  `--promo CASA[,CASA...]` (lista separada por comas; una o varias casas).
- Ejemplos:
  - `python -m betting compare cuotas.json --promo "Bet365,20Bet"`
  - `python -m betting surebet cuotas.json --inversion 100 --promo Bet365`
    (con `--promo`, `surebet` lee Formato A, no la salida de `compare --json`).
  - `python -m betting freebet cuotas.json --casa Luckia --importe 10 --promo Bet365`
- El bloque de promo va por **stdout** junto al resultado; los avisos (RF-10, RF-15)
  y el recordatorio (RF-23) por **stderr**.
- Códigos de salida: `0` normal; `1` si `--promo` se da con lista vacía (RF-3) o por
  los errores ya existentes de cada comando.

## Modelo de datos — salida JSON (RF-22)
Por cada partido, junto a su resultado normal, un bloque `promo` con las tres
opciones; cada pata asegurada lleva casa, cuota, casa y cuota de referencia, coste
(y windfall donde aplique), todo como **string**:
```
"promo": {
  "asegurar_1": {
    "patas": [
      {"resultado": "1", "casa": "Bet365", "cuota": "2.00",
       "casa_referencia": "Winamax", "cuota_referencia": "2.10",
       "coste": "5.00", "windfall": "100.00"}
    ]
  },
  "asegurar_2": { "patas": [ ... ] },
  "asegurar_ambos": { "patas": [ ..., ... ], "aviso": "los windfalls pueden acumularse" }
}
```
- En `compare` (sin importes): `coste` como caída de % de pago y sin `windfall`.

## Decisiones técnicas
- El filtro exige **Formato A** (detalle por casa). `compare`, `freebet` y `bonus`
  ya lo usan; `surebet` con `--promo` cambia su entrada a Formato A (documentado en
  el `-h`). Sin `--promo`, `surebet` sigue leyendo la salida de `compare --json`.
- `--promo` se parsea separando por comas y `strip`; lista vacía o solo espacios →
  error (RF-3).
- Núcleo puro sin IO; el redondeo (`quantize`, ROUND_HALF_UP) vive en la CLI.
- Sin dependencias nuevas (constitución nº 1).

## Estrategia de tests
- **core (posición/coste)**: caso numérico verificado a mano (coste = s·(ref−promo)
  y windfall = s·cuota); caso coste 0 cuando la mejor cuota ya es de la lista
  (RF-13); pata no asegurable → aviso y sin opción (RF-10); la X nunca se restringe
  (RF-7).
- **core (tres opciones)**: asegurar 1, asegurar 2 y asegurar ambos se generan
  juntas; en "ambos" el aviso de acumulación (RF-4, RF-15, RF-17).
- **core (filtro)**: lista vacía → error (RF-3); normalización de nombres (RF-5).
- **compare**: `--promo` baja el % de pago y muestra el coste relativo nombrando la
  casa de referencia; caso coste 0; sin `--promo` idéntico a antes (RF-2, RF-16,
  RF-18).
- **surebet**: `--promo` sobre Formato A reparte con la cuota asegurada y muestra
  coste y windfall (RF-19).
- **freebet/bonus**: `--promo` elige la cobertura de la pata de ganar entre las
  casas de la lista, excluyendo la del bono, con coste y windfall (RF-20, RF-21).
- **CLI**: `--json` con el bloque `promo` parseable; lista vacía → salida ≠ 0;
  avisos y recordatorio por stderr (RF-22, RF-23).
