# SpecBet — CLI

Calculadora de decisiones de apuestas deportivas 1X2 construida con
**Spec-Driven Development (SDD)**. No apuesta ni obtiene cuotas: lee las cuotas
de un archivo JSON y hace los cálculos. Este directorio es la CLI en Python; hay
además una app Flutter multiplataforma en [`../betting_app/`](../betting_app/).

## Comandos

```
compare     ejemplos/partidos.json                  → tabla de % de pago 1X2 y mejor cuota por resultado
surebet     comparacion.json --inversion 100        → reparto de una inversión sobre un arbitraje 1X2
freebet     cuotas.json --casa Luckia --importe 10  → dónde cubrir una freebet, su valor y % de conversión
bonus       cuotas.json --casa Luckia --importe 50 --min 1.5   → apuesta de menor coste para el rollover
multibonus  cuotas.json --bono Luckia:100:1.5 --bono Bet365:50:1.8   → rollover coordinado de 2-3 bonos
--promo     Bet365,Winamax   (flag común)           → posiciona patas de ganar en casas con promo
```

## Requisitos

- Python 3.11+
- pytest (solo para desarrollo)

## Uso

Todos los comandos se ejecutan desde este directorio (`bets/`). Sin `--json`
imprimen una tabla legible; con `--json` emiten el mismo resultado como JSON
reutilizable (importes y cuotas como string) para encadenar herramientas. Los
avisos salen por `stderr`; el resultado, por `stdout`.

### `compare` — comparador de cuotas

```bash
python -m betting compare ejemplos/partidos.json
python -m betting compare ejemplos/partidos.json --json
```

Una fila por partido, ordenada de mayor a menor % de pago; los partidos
incompletos van al final con `—`.

### `surebet` — reparto sobre un arbitraje 1X2

Consume la salida de `compare --json`:

```bash
python -m betting compare ejemplos/partidos-surebet.json --json > comparacion.json
python -m betting surebet comparacion.json --inversion 100
```

Reparte la inversión entre 1/X/2 y marca si el partido es `surebet` o `pérdida`.

### `freebet` — cobertura y valor de freebets

```bash
python -m betting freebet ejemplos/cuotas-freebet.json --casa Luckia --importe 10
python -m betting freebet ejemplos/cuotas-freebet.json --bonos ejemplos/bonos.json
```

Para uno o varios bonos: dónde poner la pata gratis, cómo cubrirla, el valor
extraído y el % de conversión. Filtros opcionales: `--min`/`--max` (cuota de la
pata gratis), `--fecha-limite`, `--partido`, `--resultado`.

### `bonus` — apuesta de menor coste para el rollover

```bash
python -m betting bonus ejemplos/cuotas-bonus.json --casa Luckia --importe 50 --min 1.5
```

Lista las opciones de menor a mayor coste para cumplir el rollover de un bono
(cuota mínima `--min`; `--fecha-limite` opcional).

### `multibonus` — rollover coordinado de varios bonos

```bash
python -m betting multibonus ejemplos/cuotas-multibono.json \
    --bono Luckia:100:1.5 --bono Bet365:50:1.8
```

Coordina 2 o 3 bonos (`--bono CASA:IMPORTE:MIN`, repetible, o `--bonos ARCHIVO`),
cada uno entero en un resultado y rellenando con dinero real, ordenado por % de
pérdida. `--apalancamiento FECHA` descarta los partidos posteriores.

### `--promo` — filtro de promociones

Flag común a `compare`, `surebet`, `freebet` y `bonus`. Recibe las casas que
ofrecen la promo "ventaja de 2 goles" y posiciona en ellas las patas de ganar,
mostrando su coste y su *windfall*:

```bash
python -m betting compare ejemplos/cuotas-promo.json --promo Bet365,Winamax
```

## Formato del archivo de entrada

```json
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

`"1"` = gana el local, `"X"` = empate, `"2"` = gana el visitante. Si una casa no
ofrece un resultado, se omite esa clave. `"fecha"` (ISO 8601) es opcional y solo
la usan los comandos con plazo (`freebet`, `bonus`, `multibonus`). Hay ejemplos
listos en [`ejemplos/`](./ejemplos/).

## Estructura del proyecto

```
bets/
├── AGENTS.md              # Contexto e instrucciones para el agente
├── docs/
│   └── constitution.md    # Principios innegociables del proyecto
├── specs/                 # Una especificación por funcionalidad (001–006)
│   └── NNN-.../           #   spec.md · plan.md · tasks.md · validacion.md
├── betting/
│   ├── __main__.py        # python -m betting
│   ├── cli.py             # Interfaz: parser y formato de salida
│   ├── core.py            # Lógica pura (cálculos)
│   └── storage.py         # Carga y validación de los JSON
├── ejemplos/              # JSON de cuotas y bonos de ejemplo
└── tests/                 # pytest (un archivo por funcionalidad)
```

## Desarrollo

```bash
pytest -q
```

## Construido con SDD

Cada funcionalidad se especificó **antes** de escribirse, y cada paso del flujo
dejó su artefacto en `specs/`. El flujo por funcionalidad es: Constitución →
Spec → Clarificación → Plan → Tareas → Implementación (una tarea cada vez, tests
primero) → Validación → Cambio (primero la spec, luego el código). Las reglas del
proyecto viven en [`docs/constitution.md`](./docs/constitution.md) y
[`AGENTS.md`](./AGENTS.md).

| # | Funcionalidad | Comando | Artefactos |
|---|---|---|---|
| 001 | Comparador de cuotas 1X2 | `compare` | [spec](./specs/001-comparador-cuotas/spec.md) · [plan](./specs/001-comparador-cuotas/plan.md) · [tasks](./specs/001-comparador-cuotas/tasks.md) · [validación](./specs/001-comparador-cuotas/validacion.md) |
| 002 | Reparto sobre arbitraje | `surebet` | [spec](./specs/002-surebet/spec.md) · [plan](./specs/002-surebet/plan.md) · [tasks](./specs/002-surebet/tasks.md) · [validación](./specs/002-surebet/validacion.md) |
| 003 | Cobertura y valor de freebets | `freebet` | [spec](./specs/003-freebet/spec.md) · [plan](./specs/003-freebet/plan.md) · [tasks](./specs/003-freebet/tasks.md) · [validación](./specs/003-freebet/validacion.md) |
| 004 | Rollover de un bono | `bonus` | [spec](./specs/004-bonus/spec.md) · [plan](./specs/004-bonus/plan.md) · [tasks](./specs/004-bonus/tasks.md) · [validación](./specs/004-bonus/validacion.md) |
| 005 | Filtro de promociones | `--promo` | [spec](./specs/005-filtro-promo/spec.md) · [plan](./specs/005-filtro-promo/plan.md) · [tasks](./specs/005-filtro-promo/tasks.md) · [validación](./specs/005-filtro-promo/validacion.md) |
| 006 | Rollover coordinado | `multibonus` | [spec](./specs/006-multibono/spec.md) · [plan](./specs/006-multibono/plan.md) · [tasks](./specs/006-multibono/tasks.md) · [validación](./specs/006-multibono/validacion.md) |
