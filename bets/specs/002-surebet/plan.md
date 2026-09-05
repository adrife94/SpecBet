# Plan técnico — Spec 002 (Surebet: reparto de stake)

## Estructura de módulos
- `betting/storage.py`  → añadir `cargar_comparacion(ruta)`: lee la **salida
  `compare --json`** (no el JSON crudo de partidos), valida su estructura y
  convierte las cuotas y el payout de string a `Decimal` (RF-13, RF-14).
- `betting/core.py`     → lógica pura del reparto: dado el conjunto de mejores
  cuotas de un partido y la inversión total, calcular importe por pata, retorno
  y beneficio garantizados; señalar surebet / pérdida / no calculable; ordenar
  (RF-1..RF-11).
- `betting/cli.py`      → subcomando `surebet`, argumento de inversión, render de
  la tabla legible y de la salida JSON reutilizable, mensajes en español, avisos
  y códigos de salida (RF-12, RF-13, RF-14, RF-15, RF-16).
- `betting/__main__.py` → ya despacha por subcomando; solo se registra `surebet`.
- `tests/`              → pytest, uno o más tests por RF.

## Modelo de datos — entrada (salida de `compare --json`, RF-1, RF-13)
Se consume exactamente lo que emite la spec 001 con `--json`:

```
{
  "version": 1,
  "partidos": [
    {
      "partido": "Real Madrid vs Barça",
      "payout": "101.50",         // string 2 decimales, o null si incompleto
      "incompleto": false,
      "mejores": {
        "1": { "cuota": "2.10", "casas": ["Bet365"] },
        "X": { "cuota": "3.60", "casas": ["Codere", "Winamax"] },
        "2": { "cuota": "4.20", "casas": ["Bet365"] }
      }
    }
  ]
}
```

- Las cuotas y el payout llegan como **string** y se reconvierten a `Decimal`
  (sin pasar por `float`), coherente con cómo los serializó la spec 001.
- Un partido con `"incompleto": true` trae `payout: null` y alguna `cuota: null`
  con `casas: []`: es un partido **no calculable** aquí (RF-9).
- El reparto recalcula la señal y el retorno desde las **cuotas** (exactas), no
  desde el `payout` ya redondeado; el `payout` solo se reutiliza para mostrar.

## Modelo de datos — salida JSON (RF-15)
Emitida con `--json`; refleja lo que muestra la tabla:

```
{
  "version": 1,
  "inversion": "100.00",
  "partidos": [
    {
      "partido": "Real Madrid vs Barça",
      "payout": "101.50",         // string 2 decimales; null si no calculable
      "surebet": true,            // payout > 100
      "no_calculable": false,
      "retorno": "101.50",        // igual en los tres resultados; null si no calc.
      "beneficio": "1.50",        // retorno - inversion; null si no calculable
      "patas": {
        "1": { "importe": "48.34", "cuota": "2.10", "casas": ["Bet365"] },
        "X": { "importe": "28.19", "cuota": "3.60", "casas": ["Codere", "Winamax"] },
        "2": { "importe": "24.17", "cuota": "4.20", "casas": ["Bet365"] }
      }
    }
  ]
}
```

- Importes, retorno, beneficio y cuotas se serializan como **string** para no
  reintroducir `float`.
- En un partido no calculable: `payout`, `retorno`, `beneficio` a `null` y
  `patas` a `null`.

## Algoritmo del reparto (RF-2, RF-3, RF-5)
Con las mejores cuotas `o1, oX, o2` (Decimal) e inversión total `T`:
1. `inv_sum = 1/o1 + 1/oX + 1/o2` (todo en `Decimal`, sin redondear).
2. Importe de cada pata: `importe_r = T · (1/o_r) / inv_sum`. La suma exacta de
   los tres importes es `T` (RF-3).
3. Retorno garantizado: `R = importe_r · o_r = T / inv_sum`, idéntico para los
   tres resultados (RF-2, RF-5).
4. Beneficio garantizado: `B = R − T`.
5. Señal: `inv_sum < 1` ⟺ `payout > 100` ⟺ `B > 0` → **surebet** (RF-6);
   `inv_sum ≥ 1` → **pérdida garantizada**, `B ≤ 0` (RF-7).
6. El redondeo a 2 decimales (`quantize`, ROUND_HALF_UP) ocurre solo al
   presentar; el core no redondea intermedios (constitución nº 8). Por eso la
   suma de importes **mostrados** puede desviarse ≤ 1 céntimo de `T` (RNF).

Ejemplo verificable a mano — `o = 2.10 / 3.60 / 4.20`, `T = 100`:
`inv_sum = 0.476190… + 0.277778… + 0.238095… = 0.992063…` → `R = 100.80`,
`B = 0.80`, importes `47.99 / 27.78 / 24.21` (aprox.), reparte 100 €.

## Señalización y orden (RF-6, RF-7, RF-9, RF-10)
- Calculables primero, por beneficio garantizado descendente (orden estable ante
  empates); no calculables después, en su orden de entrada.
- Cada fila indica su estado: `surebet` (B > 0), `pérdida` (B ≤ 0) o
  `no calculable` (partido incompleto en la entrada).

## Contrato CLI
- `python -m betting surebet <archivo.json> --inversion <importe>` → tabla
  legible en stdout (una fila por partido: importe/cuota/casas por resultado,
  retorno, beneficio y estado).
- `python -m betting surebet <archivo.json> --inversion <importe> --json` → JSON
  reutilizable en stdout, apto para encadenar con freebet/bonos (RF-15).
- `<archivo.json>` es la salida de `compare --json`. Resultados y tabla por
  **stdout**; errores y el recordatorio de verificar cuotas por **stderr**.
- `--inversion` es obligatorio; se parsea a `Decimal`. Valor no numérico o ≤ 0 →
  error en español y salida ≠ 0 (RF-12).
- Códigos de salida: `0` si todo fue bien (incluida entrada sin partidos, RF-14);
  `1` ante entrada inexistente/corrupta/ajena al comparador o inversión inválida
  (RF-12, RF-13).
- Tras el resultado, recordatorio por stderr de que las cuotas caducan y hay que
  verificarlas antes de apostar (RF-16, constitución nº 9).

## Decisiones técnicas
- argparse (stdlib), reutilizando el parser existente y añadiendo el subcomando
  `surebet` → constitución nº 1.
- La entrada es la salida del comparador, **no** el JSON crudo de partidos: se
  añade `cargar_comparacion` en `storage` en vez de reutilizar `cargar`, porque
  la estructura (con `mejores`, `payout` como string) es distinta.
- El core del reparto es puro (sin IO) y no imprime: la CLI formatea y redondea.
- Todo el cálculo en `Decimal`; el redondeo (`quantize`, ROUND_HALF_UP) vive en
  la capa de presentación, igual que en la spec 001.
- Empate de casas (RF-8): se conserva la lista `casas` de cada pata tal cual
  llega del comparador; el importe de la pata no se divide.

## Estrategia de tests
- **storage**: `cargar_comparacion` con `tmp_path` — archivo inexistente, JSON
  inválido, estructura que no es la del comparador (sin `mejores`/`payout`),
  entrada sin partidos, y comprobación de que las cuotas string se reconvierten a
  `Decimal` con su precisión.
- **core**: reparto con caso numérico verificado a mano (suma = inversión,
  retorno igual en 1/X/2), beneficio positivo con payout > 100 (surebet),
  beneficio ≤ 0 con payout ≤ 100 (pérdida), partido no calculable (incompleto),
  empate de casas conservado en la pata, y orden (calculables por beneficio desc
  + no calculables al final).
- **CLI**: smoke test de la tabla, de `--json` (JSON parseable y coherente con la
  tabla, incluida una pata con varias casas y un partido no calculable), de la
  inversión inválida (salida ≠ 0), de entrada ajena/corrupta (salida ≠ 0) y de
  entrada sin partidos (mensaje y salida 0).
