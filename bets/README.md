# betting-cli

Herramienta de apoyo a decisiones de apuestas deportivas, construida con
Spec-Driven Development (SDD). No apuesta ni obtiene cuotas: es una calculadora
que lee las cuotas de un archivo JSON y hace los cálculos.

## Requisitos
- Python 3.11+
- pytest (solo para desarrollo)

## Uso

Comparador de cuotas / % de pago de mercados 1X2:

```
python -m betting compare <archivo.json>
python -m betting compare <archivo.json> --json
```

- Sin `--json`: imprime una tabla, una fila por partido, ordenada de mayor a
  menor % de pago; los partidos incompletos van al final con `—`.
- Con `--json`: emite el mismo resultado como JSON reutilizable (cuotas y payout
  como string) para encadenar con otras herramientas.
- Los avisos (p. ej. cuotas inválidas ignoradas) salen por stderr; el resultado,
  por stdout.

### Formato del archivo de entrada

```json
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

`"1"` = gana el local, `"X"` = empate, `"2"` = gana el visitante. Si una casa no
ofrece un resultado, se omite esa clave. Hay un ejemplo en `ejemplos/partidos.json`
y un prompt listo para generar el JSON con un navegador en
`specs/001-comparador-cuotas/plan.md`.

## Desarrollo

```
pytest -q
```

La metodología y las reglas del proyecto están en `docs/constitution.md` y
`AGENTS.md`. Las funcionalidades se especifican en `specs/` antes de implementarse.
