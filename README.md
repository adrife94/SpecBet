# SpecBet

Calculadora de decisiones de apuestas deportivas 1X2 —comparador de cuotas,
surebets, freebets y bonos— construida con **Spec-Driven Development (SDD)**.
No apuesta ni obtiene cuotas: lee las cuotas de un archivo JSON y hace los
cálculos.

El mismo dominio, en dos frontends:

- **CLI en Python** → [`bets/`](./bets/)
- **App Flutter multiplataforma** → [`betting_app/`](./betting_app/)

## Herramientas

| Herramienta | Qué hace |
|---|---|
| **compare** | Comparador de cuotas y % de pago de mercados 1X2 |
| **surebet** | Arbitraje 1X2: reparto óptimo del stake |
| **freebet** | Cobertura y valor de una o varias freebets |
| **bonus** | Apuesta de menor coste para completar el rollover de un bono |
| **multibonus** | Rollover coordinado de 2–3 bonos |
| **--promo** | Filtro global de promociones (p. ej. "ventaja de 2 goles") |

## Estructura

```
SpecBet/
├── bets/            # CLI en Python (núcleo del proyecto, hecho con SDD)
│   ├── betting/     # Código: core, cli, storage
│   ├── specs/       # Una especificación por funcionalidad (001–006)
│   ├── tests/       # Tests (pytest)
│   ├── docs/        # constitution.md — principios del proyecto
│   └── ejemplos/    # JSON de cuotas de ejemplo
├── betting_app/     # App Flutter (mismo dominio, frontend gráfico)
├── samples/         # Plantillas del curso de SDD del que partió el repo
└── habits-cli/      # Proyecto de práctica del curso
```

## CLI (Python)

Requiere Python 3.11+. Desde `bets/`:

```
python -m betting compare ejemplos/partidos.json
python -m betting surebet ejemplos/partidos.json
pytest -q
```

Los detalles de cada comando y el formato del JSON de entrada están en el
[README de `bets/`](./bets/README.md).

## App Flutter

Desde `betting_app/`:

```
flutter pub get
flutter run
```

Objetivos disponibles: Android, iOS, web, Windows, macOS y Linux.

## Metodología SDD

Cada funcionalidad se especifica en `bets/specs/` **antes** de implementarse,
siguiendo el flujo: Constitución → Spec → Clarificación → Plan → Tareas →
Implementación (una tarea cada vez, tests primero) → Validación → Cambio
(primero la spec, luego el código). Las reglas del proyecto viven en
`bets/docs/constitution.md` y `bets/AGENTS.md`.

## Origen

SpecBet nació como práctica de un curso de Spec-Driven Development; por eso el
repositorio conserva el material del curso en `samples/` y `habits-cli/`.

## Licencia

Consulta el archivo [`LICENSE`](./LICENSE).
