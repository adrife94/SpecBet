# AGENTS.md — betting-cli

## Proyecto
CLI en Python de apoyo a la toma de decisiones en apuestas deportivas: comparar
cuotas entre casas de apuestas, detectar surebets (combinaciones con arbitraje
garantizado), calcular el reparto óptimo para extraer valor de una freebet, y
planificar la apuesta más barata para cumplir el rollover de un bono. Núcleo
puro (`betting/core.py`) + capa CLI (`betting/cli.py`). Persistencia en JSON
local (`betting/storage.py`) para casas, cuotas y bonos registrados.

## Comandos
- Ejecutar: `python -m betting <comando>`
- Tests: `pytest -q`

Comandos previstos (definir y congelar en `specs/` antes de implementar cada uno):
- `compare` — compara cuotas de un partido entre varias casas y calcula el % de pago (payout)
- `surebet` — detecta combinaciones 1X2 con arbitraje garantizado entre casas
- `freebet` — calcula el reparto de cobertura que extrae el máximo valor de una freebet
- `bonus` — calcula la apuesta de menor coste para cumplir un rollover (mínimo margen)

## Estilo
- Python 3.11+, type hints en todas las funciones públicas.
- Solo biblioteca estándar (pytest únicamente para tests) — nada de scraping ni
  librerías HTTP en el núcleo; la entrada de cuotas es manual o vía JSON/CSV.
- Identificadores en inglés; mensajes de usuario en español.
- Todo cálculo de cuotas/probabilidades vive en `core.py`, puro (sin IO) y testeable.
- Cálculos monetarios con `Decimal`, nunca `float`, para evitar errores de
  redondeo al trabajar con dinero real.

## Reglas
- Lee `docs/constitution.md` y la spec activa en `specs/` antes de tocar código.
- No añadas dependencias ni cambies el formato del JSON sin actualizar antes la spec.
- No modifiques archivos dentro de `specs/` salvo petición explícita.
- El proyecto no ejecuta apuestas ni interactúa con casas de apuestas reales:
  nada de login automático, scraping de cuotas en vivo, ni colocación de
  apuestas. Es una calculadora de decisión — las cuotas se introducen a mano
  o se cargan desde JSON/CSV.

## Al terminar cualquier tarea
- Ejecuta `pytest -q` y confirma en tu respuesta que todo pasa.