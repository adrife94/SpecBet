# Tareas — Spec 005 (Filtro de promo "ventaja de 2 goles")

- [x] T1. `core`: filtro y posicionamiento — `FiltroPromo` +
      `construir_filtro_promo` (lista no vacía RF-3, normalización RF-5);
      `PataPromo` y el cálculo por resultado de ganar de la mejor cuota **entre las
      casas de la lista** y de la mejor cuota **sin restricción** (referencia); las
      tres opciones por partido (asegurar 1, 2 y ambos) con el aviso de windfalls
      acumulables; y los helpers de coste `s·(ref−promo)` (0 si ya es de la lista)
      y windfall `s·cuota`. La X nunca se restringe; si ninguna casa de la lista
      cotiza una pata, se omite esa opción y se avisa. (RF-1, RF-3, RF-5, RF-6,
      RF-7, RF-8, RF-9, RF-10, RF-11, RF-12, RF-13, RF-14, RF-15, RF-17)
      Hecho cuando: tests del caso numérico verificado (coste y windfall), coste 0
      cuando la mejor cuota ya es de la lista, X no restringida, pata no asegurable
      → aviso, las tres opciones juntas con el aviso de acumulación, y lista vacía →
      error, en verde.

- [x] T2. `cli`: `compare --promo CASA[,CASA...]` — sin importes: calcula el % de
      pago con las patas aseguradas de cada opción y muestra el coste relativo como
      caída de payout, nombrando la casa de referencia; sin windfall en euros;
      `--json` con el bloque `promo`; recordatorio y avisos por stderr; con
      `--promo` desactivado el comando es idéntico a antes. (RF-2, RF-4, RF-16,
      RF-18, RF-22, RF-23)
      Hecho cuando: tests de tabla con coste relativo y casa de referencia, caso
      coste 0, `--json` parseable con `promo`, lista vacía → salida ≠ 0, y
      desactivado idéntico a antes, en verde.

- [x] T3. `cli`: `surebet --promo` sobre **Formato A** — con `--promo` lee el JSON
      de cuotas por casa (no el resumen de `compare --json`), calcula las mejores
      cuotas, y por cada opción rehace el reparto con la cuota asegurada en 1 y/o 2,
      mostrando coste y windfall en euros; `--json` con el bloque `promo`. (RF-19,
      RF-22)
      Hecho cuando: tests de reparto con la cuota asegurada, coste y windfall
      correctos, y `--json` con `promo`, en verde.

- [x] T4. `cli`: `freebet --promo` — cuando una cobertura de un resultado de ganar
      (1 o 2) se asegura, su cuota se elige entre las casas de la lista (excluyendo
      la casa del bono, constitución nº 10), con su coste y windfall; no toca la
      pata gratis. (RF-20, RF-22)
      Hecho cuando: tests de que la cobertura de la pata de ganar sale de una casa
      de la lista distinta a la del bono, con coste y windfall, en verde.

- [x] T5. `cli`: `bonus --promo` — igual que freebet: las coberturas de resultados
      de ganar aseguradas se eligen entre las casas de la lista (excluyendo la del
      bono), con coste y windfall; no toca la pata anclada. (RF-21, RF-22)
      Hecho cuando: tests de que la cobertura de la pata de ganar sale de una casa
      de la lista distinta a la del bono, con coste y windfall, en verde.

- [x] T6. Validación final: `validacion.md` con cada RF trazado a su(s) test(s) +
      demo manual (compare con caída de payout y casa de referencia; un caso coste
      0; surebet/freebet/bonus con windfall en euros; asegurar 1 vs 2 vs ambos; un
      partido sin casa de la lista en una pata → aviso; y `--json`). (Todos)
      Hecho cuando: `pytest -q` todo en verde y demo manual OK.
