# SpecBet — app Flutter

🌐 **Web:** https://specbet.netlify.app/ (acceso privado — solo miembros del equipo)

Frontend gráfico multiplataforma de **SpecBet**: calculadora de decisiones de
apuestas deportivas 1X2 construida con **Spec-Driven Development (SDD)**. Es el
mismo dominio que la [CLI en Python](../bets/) (comparador, surebet, freebet,
bonos y multibono), con una interfaz visual. No apuesta ni consulta cuotas en
vivo: tú introduces las cuotas y la app hace los cálculos.

## Pantallas

| Pantalla | Qué hace |
|---|---|
| **Cuotas** | Fuente única de cuotas: importa un JSON (Formato A) y lo comparte con el resto de pantallas |
| **Comparador** | % de pago 1X2 y mejor cuota por resultado, partido a partido |
| **Surebet** | Reparte una inversión entre 1/X/2 sobre un arbitraje |
| **Freebet** | Dónde cubrir una freebet, su valor y % de conversión |
| **Bonus** | Apuesta de menor coste para cumplir el rollover de un bono |
| **Multibono** | Rollover coordinado de 2–3 bonos |

Además, un **filtro de promo** común ("ventaja de 2 goles") con selección de
casas, **tema claro/oscuro** y un aviso permanente de que las cuotas caducan con
un botón para marcarlas como verificadas.

## Cómo funciona

- **Una sola fuente de cuotas.** La pantalla *Cuotas* mantiene el conjunto de
  partidos que consumen todas las demás. Arranca con datos de ejemplo; puedes
  **pegar tu propio JSON en Formato A** (el mismo que la CLI, ver
  [README de `bets/`](../bets/README.md#formato-del-archivo-de-entrada)).
- **Cálculo con decimales exactos.** El dinero y las cuotas usan `Decimal`, nunca
  `double` (principio nº 8 de la constitución del proyecto).
- **Responsive.** Barra lateral en pantallas anchas (≥ 760 px) y navegación
  superior en móvil.

## Cómo ejecutar

Requiere el [SDK de Flutter](https://docs.flutter.dev/get-started/install)
(Dart SDK ≥ 3.11). Desde este directorio (`betting_app/`):

```bash
flutter pub get
flutter run            # pregunta por el dispositivo
flutter run -d chrome  # en el navegador
flutter run -d windows # escritorio Windows
```

Objetivos soportados: Android, iOS, web, Windows, macOS y Linux.

## Tests

```bash
flutter test
```

Cubren el dominio (`lib/core/`) con un archivo por módulo, más un test de widget.

## Estructura del proyecto

```
betting_app/
├── lib/
│   ├── main.dart              # Arranque; monta AppState + tema
│   ├── core/                  # Lógica pura (espejo de bets/betting/core.py)
│   │   ├── odds.dart          #   parseo de cuotas (Formato A) y modelo
│   │   ├── money.dart         #   dinero/cuotas con Decimal
│   │   ├── compare.dart · surebet.dart · freebet.dart
│   │   └── bonus.dart · multibono.dart · promo.dart
│   ├── state/
│   │   └── app_state.dart     # Estado compartido: ChangeNotifier + InheritedNotifier
│   └── ui/
│       ├── app_shell.dart     # Navegación (sidebar / top nav) y avisos
│       ├── theme.dart         # Tema claro/oscuro y paleta
│       ├── screens/           # Una pantalla por herramienta
│       └── widgets/           # bet_slip, promo_panel, metric_badge, form_bits…
├── test/
│   ├── core/                  # Un test por módulo de dominio
│   └── widget_test.dart
└── (android · ios · web · windows · macos · linux)  # scaffolding por plataforma
```

## Relación con la CLI y con SDD

`lib/core/` es un port de la lógica de [`bets/betting/`](../bets/betting/): mismos
cálculos, misma constitución, mismas especificaciones. El **qué** y el **porqué**
de cada funcionalidad están en las specs del proyecto,
[`bets/specs/`](../bets/specs/) (comparador → surebet → freebet → bonus → filtro
promo → multibono), redactadas antes de implementar. La app es una interfaz sobre
ese dominio ya especificado y probado.

## Stack

- **Flutter / Dart** (sin librería de estado: `ChangeNotifier` + `InheritedNotifier`).
- [`decimal`](https://pub.dev/packages/decimal) — aritmética exacta de dinero y cuotas.
- [`intl`](https://pub.dev/packages/intl) — formato de números y fechas en español.
