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
      "fecha": "2026-09-10",
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
- La `fecha` de inicio del partido es **opcional** (ISO 8601, a nivel de partido):
  `compare` y `surebet` la ignoran; `freebet`, `bonus` y `multibonus` la usan para
  el plazo (`--fecha-limite` / `--apalancamiento`). Si no se recoge, esos comandos
  avisan y no filtran por plazo.
- Las cuotas se cargan con `json.load(..., parse_float=Decimal)`: los números
  del JSON entran como `Decimal`, nunca como `float` (constitución nº 8).
- Cuota válida = `Decimal` > 1. Cualquier otro valor (`0`, negativo, ≤ 1, texto
  tipo `"N/A"`) se descarta como hueco y se avisa (RF-8).

## Prompt para Claude-navegador
Instrucción lista para pegar **en el chat de Claude-navegador** (no en un campo de
la página). Parte de que ya hay un **grupo de pestañas** abierto, una por casa,
cada una con la página del evento ya cargada. Solo se rellena `{{PARTIDOS}}` si se
quieren partidos concretos. Está redactada en **primera persona, como petición del
usuario, a propósito**: el estilo "eres un asistente que… / devuelve solo JSON"
dispara el anti-inyección de Claude-navegador, que rechaza instrucciones con forma
de reasignación de rol. La respuesta es el JSON de entrada de arriba dentro de un
bloque de código (puede llevar alguna frase alrededor; se copia el bloque).

```
Tengo varias pestañas abiertas; cada una es una casa de apuestas con un evento ya
cargado. ¿Puedes leer las cuotas del mercado 1X2 (1 = local, X = empate, 2 =
visitante, al final del tiempo reglamentario) de esas pestañas y pasármelas en JSON?

Trabaja solo con las pestañas que ya tengo abiertas: no navegues a otras URLs, no
busques ni abras pestañas nuevas; solo haz scroll para localizar los partidos.
Desplázate hasta el final de cada pestaña, repitiendo el scroll hasta que no
aparezcan partidos nuevos (muchas casas los cargan a medida que bajas). El nombre
de la casa es el de cada pestaña.

Partidos: {{PARTIDOS}}
(si lo dejo vacío, coge todos los que veas al hacer scroll; por ejemplo,
Real Madrid vs Barça).

Devuélvemelo en un bloque de código con esta estructura:

{
  "version": 1,
  "partidos": [
    {
      "partido": "Real Madrid vs Barça",
      "fecha": "2026-09-10",
      "cuotas": [
        { "casa": "Bet365", "1": 2.10, "X": 3.30, "2": 3.50 },
        { "casa": "Codere", "1": 2.05, "X": 3.40, "2": 3.60 }
      ]
    }
  ]
}

Preferencias de formato:
- Cuotas en decimal europeo con punto como separador (2.10, no 2,10 ni
  fracciones), siempre mayores que 1.
- El campo "partido" usa el formato "Local vs Visitante".
- Incluye la fecha (y la hora, si es visible) de inicio del partido en el campo
  "fecha", en formato ISO 8601 (por ejemplo "2026-09-10" o "2026-09-10T21:00").
  Es un único valor por partido, el mismo en todas las casas. Si la fecha no es
  visible en la pestaña, omite la clave "fecha"; no la inventes.
- Una sola entrada por casa dentro de cada partido; sin repetir casas ni partidos.
- Solo el mercado 1X2 (tres resultados); nada de hándicaps, más/menos goles,
  ambos marcan, etc.
- Si una casa no muestra la cuota de algún resultado, omite esa clave para esa
  casa; no inventes ni estimes valores.
- Si un partido no aparece en una pestaña tras hacer scroll, no lo incluyas para
  esa casa; no lo busques fuera de la pestaña.
- Si en alguna pestaña no pudiste leer todos los partidos, dilo en una línea
  después del bloque de código: qué casa y hasta qué partido o jornada llegaste.
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
