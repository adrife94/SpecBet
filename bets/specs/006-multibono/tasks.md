# Tareas — Spec 006 (Multibono: rollover coordinado)

- [x] T1. `core`: `Bono` + `ConfigMulti` + `construir_config_multi` — reutilizar
      `storage.cargar_bonos` (003) y validar que resulten 2 o 3 bonos, con casas
      distintas, importe > 0 y cuota mínima > 1; normalizar a `Decimal`/`datetime`;
      fecha de apalancamiento opcional. (RF-2, RF-3, RF-4)
      Hecho cuando: tests de menos de 2 o más de 3 bonos, importe ≤ 0, cuota mínima
      ≤ 1, casas repetidas, fecha inválida y de conversión a `Decimal` en verde.

- [x] T2. `core`: opción de un partido dada una asignación — techo
      `R = máx(Sᵢ·aᵢ)`, relleno de cada resultado por debajo de `R` con dinero real
      (`s = (R−Bᵢ)/q`) y del resultado sin bono en el caso de 2 bonos, y métricas
      `perdida = T−R`, `perdida_pct`, `dinero_real` y `neto`, todo en `Decimal`.
      (RF-12, RF-13, RF-14, RF-15, RF-18, RF-19, RF-20, RF-21)
      Hecho cuando: test del caso numérico verificado a mano (relleno que iguala `R`
      en los tres resultados; pérdida €/%, dinero real y neto), un caso de 2 bonos
      con el tercer resultado solo con dinero real y un caso de pérdida negativa
      (arbitraje) en verde.

- [x] T3. `core`: elección de asignación + relleno/exclusión — probar las
      permutaciones válidas (cuota anclada ≥ cuota mínima; resultados rellenables en
      casa distinta de todas las de bono) y elegir la de menor pérdida (empate
      determinista por orden 1, X, 2); `_mejor_cuota_excluyendo(casas)`; descartes
      por casa de bono ausente y por resultado no rellenable. (RF-6, RF-7, RF-8,
      RF-9, RF-10, RF-11, RF-16, RF-17)
      Hecho cuando: tests de asignación de menor pérdida con importes distintos,
      empate determinista, relleno que excluye todas las casas de bono, resultado no
      rellenable → descarte con motivo, casa de bono ausente → descarte, y caso de
      2 bonos en verde.

- [x] T4. `core`: plazo y orden — `evaluar_multibono` que descarta partidos en o
      después del apalancamiento, avisa de los sin fecha cuando hay apalancamiento,
      ignora las fechas sin apalancamiento, y ordena todas las opciones por pérdida
      ascendente (negativos incluidos); archivo sin partidos y sin opciones válidas.
      (RF-22, RF-23, RF-24, RF-25, RF-26, RF-27, RF-28, RF-33, RF-34)
      Hecho cuando: tests de fuera de plazo, aviso sin fecha, sin apalancamiento,
      orden por pérdida (con un negativo y con un partido parejo mal pagado ordenado
      por encima de otro desequilibrado más caro), sin partidos y sin opciones en
      verde.

- [x] T5. `cli`: subcomando `multibonus <cuotas> --bono CASA:IMPORTE:MIN` (repetible)
      o `--bonos <archivo>` `[--apalancamiento FECHA] [--json]` que renderiza las
      opciones ordenadas (patas de bono y de relleno, `R`, dinero real, pérdida €/%
      y neto) y los descartes; `--json` reutilizable; validación (entradas inválidas
      y archivo corrupto → salida ≠ 0; sin partidos y sin opciones → salida 0);
      avisos y recordatorio por stderr. (RF-1, RF-5, RF-29, RF-30, RF-31, RF-32)
      Hecho cuando: tests de tabla, `--bono` repetible y `--bonos` archivo, `--json`,
      entradas inválidas (≠ 0), archivo corrupto (≠ 0), sin partidos (0), sin
      opciones (0) y avisos en verde.

- [x] T6. Validación final: `validacion.md` con cada RF trazado a su(s) test(s) +
      demo manual (3 bonos casi 3/3/3 con poco o ningún dinero real; un partido
      parejo mal pagado ordenado por encima de otro más caro; 2 bonos con el tercer
      resultado solo con dinero real; un partido descartado por casa de bono ausente
      y otro por resultado no rellenable; una fecha de apalancamiento que deja fuera
      un partido posterior y avisa de uno sin fecha; y `--json`). (Todos)
      Hecho cuando: `pytest -q` todo en verde y demo manual OK.
