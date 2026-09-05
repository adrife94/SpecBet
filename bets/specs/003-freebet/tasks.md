# Tareas — Spec 003 (Freebet: cobertura y valor)

- [x] T1. `storage.cargar_bonos` + modelo `Bono`: cargar el JSON de bonos con
      `parse_float=Decimal`, validar estructura (raíz objeto, `bonos` lista, cada
      bono con `casa` e `importe`); construir `Bono` normalizando importe/min/max
      a `Decimal`, `fecha_limite` a `datetime` y validando `resultado` ∈ {1,X,2}
      e importe > 0. La `fecha` opcional del partido viaja ya en `cargar`.
      (RF-17, RF-18, RF-19, RF-28)
      Hecho cuando: tests de inexistente, JSON inválido, sin `bonos`, bono sin
      casa/importe, importe ≤ 0, resultado inválido y de conversión a `Decimal`
      en verde.

- [x] T2. `core`: conversión de una colocación — dada la cuota gratis, el
      importe y las mejores cuotas de cobertura, calcular importes de cobertura,
      valor extraído y % de conversión, todo en `Decimal`. (RF-2, RF-3, RF-4,
      RF-11)
      Hecho cuando: test del caso numérico verificado (mismo neto en 1/X/2, valor
      y % de conversión) en verde.

- [x] T3. `core`: elección del resultado y restricciones — admisible por rango de
      cuota, cobertura en casas distintas de la del bono (empate determinista),
      resultado no cubrible, auto elige el de mayor valor y modo con resultado
      fijado. (RF-6, RF-7, RF-9, RF-10, RF-12, RF-13)
      Hecho cuando: tests de auto-mejor, resultado fijado, fuera de rango no
      propuesto, cobertura excluye la casa del bono y no cubrible en verde.

- [x] T4. `core`: evaluación por partido y plazo — casa del bono ausente → no
      jugable; fuera de plazo; sin fecha con límite → aviso; orden por valor
      extraído con no jugables al final; recomendada = primera. (RF-14, RF-15,
      RF-24, RF-25, RF-26, RF-27, RF-33, RF-34)
      Hecho cuando: tests de casa ausente, fuera de plazo, aviso sin fecha, orden
      + recomendada en verde.

- [x] T5. `core`: lote de bonos — cada bono independiente, valor total y % de
      conversión total, bono sin plan cuenta 0 y se marca, colisión de patas
      entre recomendadas. (RF-28, RF-29, RF-30, RF-31, RF-32)
      Hecho cuando: tests de dos bonos con total, bono sin plan y colisión
      detectada en verde.

- [x] T6. `cli`: subcomando `freebet <cuotas> --casa --importe [...]` (un bono)
      que renderiza el listado por partido (valor, % de conversión, patas,
      estado/recomendada), mensajes en español, salida por stdout. (RF-1, RF-5,
      RF-21 tabla)
      Hecho cuando: smoke test de la tabla de un bono (listado ordenado con valor
      y % de conversión) en verde.

- [x] T7. `cli`: `--bonos` (lote con valor total y % total), `--json`
      reutilizable, avisos de plazo/sin fecha/colisión y recordatorio por stderr;
      validación (importe ≤ 0, casa no indicada, archivo corrupto/repetido,
      resultado/fecha inválidos → salida ≠ 0; sin partidos → salida 0). (RF-16,
      RF-17, RF-18, RF-19, RF-20, RF-22, RF-30, RF-31)
      Hecho cuando: tests de lote, `--json`, importe inválido, casa no indicada,
      archivo corrupto (salida ≠ 0), sin partidos (salida 0) y avisos en verde.

- [x] T8. Validación final: `validacion.md` con cada RF trazado a su(s) test(s) +
      ejemplos y demo manual (modo auto, resultado fijado, casa ausente, fecha
      límite dejando un partido fuera de plazo y avisando de uno sin fecha, lote
      de dos bonos con valor total, y `--json`). (Todos)
      Hecho cuando: `pytest -q` todo en verde y demo manual OK.
