# Plan técnico — Spec 001 (Comparador de cuotas / % de pago)

## Estructura de módulos
- `betting/storage.py`  → cargar y validar el JSON de entrada (RF-11, RF-12).
- `betting/core.py`     → lógica pura sin IO: mejor cuota, % de pago,
  normalización de nombres, detección de repetidos, marcado de incompletos y
  ordenación (RF-1..RF-10, RF-13..RF-17).
- `betting/cli.py`      → argparse, subcomando `compare`, render de la tabla
  legible y de la salida JSON reutilizable, mensajes en español y códigos de
  salida (RF-11, RF-12, RF-18).
- `betting/__main__.py` → permite `python -m betting`.
- `tests/`              → pytest, uno o más tests por RF.

## Modelo de datos — JSON de entrada
Esto es lo que se le pide a Claude-navegador que genere:

```
{
  "version": 1,
  "partidos": [
    {
      "partido": "Real Madrid vs Barça",
      "cuotas": [
        { "casa": "Bet365", "1": 2.10, "X": 3.30, "2": 3.50 },
        { "casa": "Codere", "1": 2.05, "X": 3.40, "2": 3.60 }
      ]
    }
  ]
}
```

- Cada resultado es una de las claves `"1"`, `"X"`, `"2"`. Una casa puede omitir
  claves: la clave ausente (o `null`) es un hueco (RF-7).
- Las cuotas se cargan con `json.load(..., parse_float=Decimal)`: los números
  del JSON entran como `Decimal`, nunca como `float` (constitución nº 8).
- Cuota válida = `Decimal` > 1. Cualquier otro valor (`0`, negativo, ≤ 1, texto
  tipo `"N/A"`) se descarta como hueco y se avisa (RF-8).

## Prompt para Claude-navegador
Instrucción lista para pegar. Parte de que ya hay un **grupo de pestañas**
abierto, una por casa, cada una con la página del evento ya cargada. Solo se
rellena `{{PARTIDOS}}` si se quieren partidos concretos. Está diseñada para que
la respuesta sea directamente el JSON de entrada de arriba.

```
Eres un asistente que recopila cuotas de apuestas 1X2. Tu única tarea es
devolver un archivo JSON con las cuotas, sin ningún texto adicional.

Trabaja EXCLUSIVAMENTE con las pestañas ya abiertas en el grupo de pestañas
actual. Cada pestaña es una casa de apuestas con su página ya cargada en el
evento correspondiente. NO navegues a otras URLs, NO uses buscadores y NO abras
pestañas nuevas: limítate a hacer scroll dentro de cada pestaña para localizar
los partidos y leer sus cuotas 1X2. El nombre de la casa es el de la casa de
apuestas de esa pestaña.

Partidos a extraer:
{{PARTIDOS}}
(Si esta lista está vacía, extrae todos los partidos visibles al hacer scroll en
cada pestaña. Ejemplo de partido: Real Madrid vs Barça.)

Para cada partido y cada pestaña, lee las cuotas del mercado 1X2 (resultado al
final del tiempo reglamentario): "1" = gana el equipo local, "X" = empate,
"2" = gana el equipo visitante.

Devuelve EXCLUSIVAMENTE un JSON con esta estructura exacta:

{
  "version": 1,
  "partidos": [
    {
      "partido": "Real Madrid vs Barça",
      "cuotas": [
        { "casa": "Bet365", "1": 2.10, "X": 3.30, "2": 3.50 },
        { "casa": "Codere", "1": 2.05, "X": 3.40, "2": 3.60 }
      ]
    }
  ]
}

Reglas:
- Cuotas en formato decimal europeo con punto como separador (2.10, no 2,10 ni
  fracciones). Toda cuota debe ser un número mayor que 1.
- El campo "partido" usa el formato "Local vs Visitante".
- Una sola entrada por casa dentro de cada partido; no repitas casas ni partidos.
- Solo el mercado 1X2 (tres resultados). Nada de hándicaps, más/menos goles,
  ambos marcan, etc.
- Si una casa (pestaña) no muestra la cuota de algún resultado, OMITE esa clave
  para esa casa; no inventes ni estimes valores.
- Si un partido de la lista no aparece en una pestaña tras hacer scroll, no lo
  incluyas para esa casa; no lo busques fuera de la pestaña.
- No añadas comentarios, explicaciones, ni vallas de código (```): responde
  únicamente con el JSON válido.
```

## Modelo de datos — JSON de salida (RF-18)
Emitido con `--json`; refleja exactamente lo que muestra la tabla:

```
{
  "version": 1,
  "partidos": [
    {
      "partido": "Real Madrid vs Barça",
      "payout": "95.41",          // string 2 decimales; null si incompleto
      "incompleto": false,
      "mejores": {
        "1": { "cuota": "2.10", "casas": ["Bet365"] },
        "X": { "cuota": "3.40", "casas": ["Codere"] },
        "2": { "cuota": "3.60", "casas": ["Codere"] }
      }
    }
  ]
}
```

- Cuotas y payout se serializan como **string** para no reintroducir `float`.
- En un partido incompleto, `payout` es `null` y los resultados sin cuota válida
  aparecen con `cuota: null, casas: []`.

## Algoritmo del % de pago (RF-2, RF-3, RF-14, RF-9)
1. Por cada resultado r ∈ {1, X, 2}: reunir las cuotas válidas de todas las
   casas; `mejor[r]` = la más alta; `casas[r]` = todas las casas que igualan esa
   cuota (empate → varias, RF-5).
2. Un partido es **incompleto** si algún resultado no tiene ninguna cuota válida
   (RF-9) **o** si tiene cuotas válidas de menos de dos casas distintas (RF-14).
3. Si es completo:
   `payout = 100 / (1/mejor_1 + 1/mejor_X + 1/mejor_2)`, todo en `Decimal`.
   Ejemplo: 2.10 / 3.40 / 3.60 → 100 / (0.47619 + 0.29412 + 0.27778) = **95.41 %**.
4. El redondeo a 2 decimales (`quantize`, ROUND_HALF_UP) ocurre solo al
   presentar; el core no redondea intermedios (constitución nº 8).

## Ordenación (RF-6, RF-10)
- Completos primero, por `payout` descendente.
- Incompletos después, al final; entre ellos, orden estable de entrada.

## Decisiones técnicas
- argparse (stdlib), sin typer/click → constitución nº 1.
- Normalización de nombres (RF-13): clave = `nombre.strip().casefold()` para
  agrupar y detectar repetidos; se conserva el nombre original tal como llegó
  para mostrarlo. Los espacios **interiores** no se tocan.
- Repetidos como error (RF-15, RF-16): al indexar por clave normalizada, si una
  casa se repite dentro de un partido, o un partido se repite en el archivo, se
  aborta con mensaje que los identifica y salida ≠ 0.
- `storage` solo lee; no escribe nada (esta spec no persiste estado).
- El comparador es neutro ante payout > 100 % (RF-17): no lo marca; solo ordena.

## Contrato CLI
- `python -m betting compare <archivo.json>` → tabla legible en stdout.
- `python -m betting compare <archivo.json> --json` → JSON reutilizable en
  stdout (sin la tabla), apto para encadenar con otras funcionalidades (RF-18).
- Resultados y tabla por **stdout**; errores y avisos de cuotas descartadas por
  **stderr**.
- Códigos de salida: `0` si todo fue bien (incluido archivo sin partidos, RF-12);
  `1` ante archivo inexistente/corrupto/estructura inesperada o repetidos
  (RF-11, RF-15, RF-16). Los avisos de RF-8 no cambian el código (sigue `0`).

## Estrategia de tests
- **core**: mejor cuota con empate (varias casas), payout con caso numérico
  verificado a mano, normalización de nombres, incompleto por resultado sin
  cuota, incompleto por menos de 2 casas, orden (completos desc + incompletos al
  final), descarte de cuota inválida.
- **storage**: `tmp_path` con archivo inexistente, JSON inválido, estructura
  inesperada, sin partidos, y comprobación de que `parse_float=Decimal` preserva
  la precisión (2.10 no se convierte en 2.1000000000000001).
- **duplicados**: casa repetida en un partido y partido repetido → error y
  salida ≠ 0.
- **CLI**: smoke test de la tabla, de `--json` (JSON parseable y coherente con
  la tabla) y de los códigos de salida.
