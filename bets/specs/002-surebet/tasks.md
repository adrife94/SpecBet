# Tareas — Spec 002 (Surebet: reparto de stake)

- [x] T1. `storage.cargar_comparacion`: cargar la salida de `compare --json`;
      validar estructura (raíz objeto, `partidos` lista, cada partido con
      `mejores`/`payout`/`incompleto`); reconvertir cuotas y payout de string a
      `Decimal`; inexistente/no-JSON/estructura ajena → `ErrorDatos` (salida ≠ 0);
      entrada válida sin partidos → lista vacía. (RF-13, RF-14)
      Hecho cuando: tests de inexistente, JSON inválido, estructura ajena al
      comparador, sin partidos, y de que `"2.10"` vuelve a `Decimal` en verde.

- [x] T2. `core`: cálculo del reparto de un partido calculable — importe por pata
      `T·(1/o_r)/Σ(1/o)`, retorno `T/Σ(1/o)` y beneficio `retorno − T`, todo en
      `Decimal` sin redondear. (RF-1, RF-2, RF-3, RF-5)
      Hecho cuando: test del caso numérico verificado (importes suman la
      inversión y retorno igual en 1/X/2) en verde.

- [x] T3. `core`: señalización — `surebet` (beneficio > 0, payout > 100),
      `pérdida` (beneficio ≤ 0, payout ≤ 100) y `no calculable` (partido
      incompleto en la entrada, sin reparto). (RF-6, RF-7, RF-9)
      Hecho cuando: tests de surebet con beneficio +, de pérdida con beneficio ≤ 0
      (incluido payout = 100 → beneficio 0) y de partido incompleto no calculable
      en verde.

- [x] T4. `core`: conservar el empate de casas en cada pata (lista `casas` tal
      cual, sin dividir el importe) y ordenar — calculables por beneficio
      descendente, no calculables al final. (RF-8, RF-10)
      Hecho cuando: test de que una pata con varias casas conserva la lista y de
      orden mixto (calculables desc + no calculables al final) en verde.

- [x] T5. `cli`: subcomando `surebet <archivo> --inversion <importe>` que
      renderiza la tabla legible (importe/cuota/casas por resultado, retorno,
      beneficio, estado; 2 decimales), mensajes en español, salida por stdout.
      (RF-4, RF-11)
      Hecho cuando: smoke test de la tabla (con un surebet y una pérdida) en verde.

- [x] T6. `cli`: validación de la inversión (`Decimal` > 0; no numérica o ≤ 0 →
      error y salida ≠ 0), entrada ajena/corrupta → error y salida ≠ 0, entrada
      sin partidos → mensaje y salida 0, y recordatorio por stderr de verificar
      cuotas antes de apostar. (RF-12, RF-13, RF-14, RF-16)
      Hecho cuando: tests de inversión inválida (salida ≠ 0), entrada corrupta
      (salida ≠ 0), entrada sin partidos (salida 0) y del recordatorio en verde.

- [x] T7. `cli`: opción `--json` que emite la salida reutilizable (importes,
      retorno, beneficio y cuotas como string; `surebet`, `no_calculable`,
      `casas` como lista; `patas`/retorno/beneficio a `null` si no calculable).
      (RF-15)
      Hecho cuando: test que parsea el JSON de salida y comprueba que coincide con
      la tabla (incluida una pata con varias casas y un partido no calculable) en
      verde.

- [x] T8. Validación final: `validacion.md` con cada RF trazado a su(s) test(s) +
      demo manual encadenando `compare --json | surebet` sobre el JSON de ejemplo
      (un surebet con reparto que suma la inversión, una pérdida señalada, un no
      calculable al final, y `--json`). (Todos)
      Hecho cuando: `pytest -q` todo en verde y demo manual OK.
