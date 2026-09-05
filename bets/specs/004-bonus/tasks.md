# Tareas — Spec 004 (Bonus: apuesta de menor coste para el rollover)

- [x] T1. `core`: `ConfigBonus` + `construir_config_bonus` — validar importe > 0,
      cuota mínima > 1 y casa indicada; normalizar a `Decimal`/`datetime`; fecha
      límite opcional. (RF-18, RF-19, RF-20)
      Hecho cuando: tests de importe ≤ 0, cuota mínima ≤ 1, casa ausente, fecha
      inválida y de conversión a `Decimal` en verde.

- [x] T2. `core`: coste de una opción — anclar importe a cuota `a`, cubrir los
      otros dos a `b`/`c` igualando el retorno, y `coste = (S+s_b+s_c) − S·a`,
      todo en `Decimal`. (RF-3, RF-4, RF-5, RF-7)
      Hecho cuando: test del caso numérico verificado (mismo retorno en los tres
      resultados y coste; incluido un coste negativo) en verde.

- [x] T3. `core`: generación de opciones por partido — una por resultado ≥ cuota
      mínima, cobertura en casa distinta (empate determinista), resultado bajo la
      mínima omitido, no cubrible → descarte con motivo, casa del bono ausente →
      descarte del partido. (RF-2, RF-6, RF-11, RF-12, RF-13)
      Hecho cuando: tests de una opción por resultado, bajo mínima omitido, no
      cubrible, cobertura excluye la casa del bono y casa ausente en verde.

- [x] T4. `core`: plazo y orden — `evaluar_bonus` que descarta fuera de plazo,
      avisa de sin fecha con límite, ignora fechas sin límite, y ordena todas las
      opciones por coste ascendente (negativos incluidos). (RF-9, RF-10, RF-14,
      RF-15, RF-16, RF-17)
      Hecho cuando: tests de fuera de plazo, aviso sin fecha, sin límite y de orden
      por coste (con un negativo) en verde.

- [x] T5. `cli`: subcomando `bonus <cuotas> --casa --importe --min [--fecha-limite]
      [--json]` que renderiza las opciones ordenadas (resultado anclado con su
      cuota, importe, coberturas y coste) y los descartes; `--json` reutilizable;
      validación (importe/cuota mínima/casa inválidos, archivo corrupto → salida
      ≠ 0; sin partidos y sin opciones → salida 0); avisos y recordatorio por
      stderr. (RF-1, RF-8, RF-21, RF-22, RF-23, RF-24, RF-25, RF-26, RF-27)
      Hecho cuando: tests de tabla, `--json`, importe/casa inválidos (≠ 0), archivo
      corrupto (≠ 0), sin partidos (0), sin opciones (0) y avisos en verde.

- [x] T6. Validación final: `validacion.md` con cada RF trazado a su(s) test(s) +
      ejemplo y demo manual (opciones ordenadas por coste con cuota anclada, un
      resultado bajo la mínima y otro no cubrible, casa del bono ausente, fecha
      límite dejando fuera un partido y avisando de uno sin fecha, y `--json`).
      (Todos)
      Hecho cuando: `pytest -q` todo en verde y demo manual OK.
