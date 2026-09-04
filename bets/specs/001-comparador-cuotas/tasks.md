# Tareas — Spec 001 (Comparador de cuotas / % de pago)

- [x] T1. Esqueleto del proyecto: paquete `betting/`, carpeta `tests/`, pytest
      configurado, `__main__.py` que despacha el subcomando `compare`. (RF: —)
      Hecho cuando: `pytest -q` corre (0 tests) sin errores y
      `python -m betting compare` muestra ayuda de uso.

- [x] T2. `storage.py`: cargar el JSON de entrada con `parse_float=Decimal`;
      validar estructura; archivo inexistente/no-JSON/estructura inesperada →
      error propio con salida ≠ 0; archivo válido sin partidos → estructura
      vacía sin error. (RF-11, RF-12)
      Hecho cuando: tests de inexistente, JSON inválido, estructura inesperada,
      sin partidos, y de que `2.10` se carga como `Decimal` (no `float`) en verde.

- [x] T3. `core`: normalización de nombres (`strip().casefold()`, conservando el
      original) y detección de repetidos → casa repetida en un partido y partido
      repetido en el archivo abortan con error. (RF-13, RF-15, RF-16)
      Hecho cuando: tests de normalización, casa duplicada y partido duplicado
      (con distinta caja/espacios) en verde.

- [x] T4. `core`: mejor cuota por resultado. Valida cuota > 1, ignora huecos por
      casa, descarta cuotas inválidas con aviso y devuelve todas las casas en
      caso de empate. (RF-2, RF-4, RF-5, RF-7, RF-8)
      Hecho cuando: tests de mejor cuota, empate (varias casas), hueco por casa
      y cuota inválida descartada en verde.

- [x] T5. `core`: marcado de partido incompleto — algún resultado sin cuota
      válida en ninguna casa, o menos de dos casas distintas. (RF-9, RF-14)
      Hecho cuando: tests de incompleto por resultado ausente y por una sola
      casa en verde.

- [x] T6. `core`: cálculo del % de pago con `Decimal`, redondeo a 2 decimales
      solo al presentar. (RF-3)
      Hecho cuando: test del caso numérico verificado (2.10/3.40/3.60 → 95.41 %)
      y de un partido incompleto sin payout en verde.

- [x] T7. `core`: ordenación — completos por payout descendente, incompletos al
      final; sin destacar los > 100 %. (RF-6, RF-10, RF-17)
      Hecho cuando: test de orden mixto (completos desc + incompletos al final)
      y de que un > 100 % no recibe marca especial en verde.

- [x] T8. `cli`: comando `compare <archivo.json>` que renderiza la tabla legible
      (2 decimales, casas empatadas en la celda, incompletos al final), mensajes
      en español, avisos/errores por stderr y códigos de salida. (RF-1, RF-8,
      RF-11, RF-12)
      Hecho cuando: smoke tests de tabla, de archivo vacío (salida 0) y de
      archivo corrupto (salida ≠ 0) en verde.

- [x] T9. `cli`: opción `--json` que emite la salida reutilizable (cuotas y
      payout como string, `incompleto`, `casas` como lista). (RF-18)
      Hecho cuando: test que parsea el JSON de salida y comprueba que coincide
      con la tabla (incluido un partido incompleto) en verde.

- [x] T10. Validación final: checklist de la spec (cada RF con test asociado) +
      demo manual sobre un JSON de ejemplo (tabla ordenada, un incompleto al
      final, aviso de cuota descartada, `--json`). (Todos)
      Hecho cuando: `pytest -q` todo en verde y demo manual OK.
