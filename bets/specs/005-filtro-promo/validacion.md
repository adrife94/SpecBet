# Validación — Spec 005 (Filtro de promo "ventaja de 2 goles")

Trazabilidad de cada requisito funcional a su(s) test(s). Todos en verde.

| RF | Qué exige | Test(s) |
|----|-----------|---------|
| RF-1 | Recibe una lista de casas con promo | `test_core_promo::test_construir_filtro_normaliza_y_valida` (y `--promo` en las CLI) |
| RF-2 | Filtro desactivado → comportamiento idéntico | `test_cli_compare_promo::test_sin_promo_identico_a_antes`, `::test_sin_promo_json_no_lleva_promo`, `test_cli_surebet_promo::test_sin_promo_sigue_leyendo_el_resumen_de_compare`, `test_cli_freebet_promo::test_sin_promo_identico`, `test_cli_bonus_promo::test_sin_promo_identico` |
| RF-3 | Lista vacía → error, salida ≠ 0 | `test_core_promo::test_lista_vacia_es_error`, `::test_lista_solo_espacios_es_error`, `test_cli_compare_promo::test_lista_vacia_es_error` (y surebet/freebet/bonus análogos) |
| RF-4 | Tres opciones por partido, cada una con coste (y windfall) | `test_core_promo::test_tres_opciones_juntas_con_aviso_de_acumulacion`, `test_cli_compare_promo::test_promo_tabla_coste_referencia_y_tres_opciones` |
| RF-5 | Nombres de casa case-insensitive / sin espacios | `test_core_promo::test_construir_filtro_normaliza_y_valida` |
| RF-6 | Mejor cuota de la pata asegurada solo entre las casas de la lista | `test_core_promo::test_posicion_coste_y_windfall_verificados_a_mano` |
| RF-7 | La X nunca se restringe | `test_core_promo::test_la_x_nunca_se_restringe` |
| RF-8 | La pata asegurada usa la mejor cuota entre las casas de la lista | `test_core_promo::test_posicion_coste_y_windfall_verificados_a_mano` |
| RF-9 | Ambas patas → casas de la lista en 1 y 2 | `test_core_promo::test_tres_opciones_juntas_con_aviso_de_acumulacion` (asegurar_ambos, 2 patas) |
| RF-10 | Ninguna casa de la lista cotiza una pata → no se asegura y avisa | `test_core_promo::test_pata_no_asegurable_devuelve_none`, `::test_pata_no_asegurable_omite_opcion_y_avisa` |
| RF-11 | Coste relativo = retorno perdido frente a la mejor cuota sin restricción | `test_core_promo::test_posicion_coste_y_windfall_verificados_a_mano`, `test_cli_compare_promo::test_promo_json_incluye_bloque_y_coste`, `test_cli_surebet_promo::test_promo_json_reparto_asegurado` |
| RF-12 | Nombra la casa de referencia | `test_core_promo` (`casa_referencia`), `test_cli_compare_promo` (Winamax), `test_cli_freebet_promo`/`bonus` (`casa_referencia`) |
| RF-13 | Mejor cuota ya de la lista → coste 0 | `test_core_promo::test_coste_cero_cuando_la_mejor_cuota_ya_es_de_la_promo`, `test_cli_compare_promo::test_promo_json_incluye_bloque_y_coste` (C vs D) |
| RF-14 | Windfall = importe apostado en la pata × cuota | `test_core_promo::test_posicion_coste_y_windfall_verificados_a_mano`, `test_cli_surebet_promo`/`freebet`/`bonus` (windfall en JSON) |
| RF-15 | Los windfalls de las dos patas pueden acumularse (aviso) | `test_core_promo::test_tres_opciones_juntas_con_aviso_de_acumulacion`, `test_cli_compare_promo`/`freebet`/`bonus` (acumul) |
| RF-16 | En compare (sin importes) solo % de pago, sin windfall en euros | `test_cli_compare_promo::test_promo_sin_windfall_en_compare` |
| RF-17 | Muestra las tres opciones juntas | `test_core_promo::test_tres_opciones_juntas_con_aviso_de_acumulacion`, `test_cli_compare_promo::test_promo_tabla_coste_referencia_y_tres_opciones` |
| RF-18 | compare: % de pago con las patas aseguradas + coste relativo | `test_cli_compare_promo::test_promo_tabla_coste_referencia_y_tres_opciones`, `::test_promo_json_incluye_bloque_y_coste` |
| RF-19 | surebet: reparto con las patas aseguradas + coste + windfall | `test_cli_surebet_promo::test_promo_tabla_con_coste_y_windfall`, `::test_promo_json_reparto_asegurado` |
| RF-20 | freebet: coberturas de ganar aseguradas entre las casas de la lista | `test_cli_freebet_promo::test_promo_tabla_coberturas_de_ganar`, `::test_promo_json_coste_y_windfall`, `::test_promo_excluye_la_casa_del_bono` |
| RF-21 | bonus: coberturas de ganar aseguradas entre las casas de la lista | `test_cli_bonus_promo::test_promo_tabla_coberturas_de_ganar`, `::test_promo_json_opcion_anclada_en_x`, `::test_promo_excluye_la_casa_del_bono` |
| RF-22 | JSON con casa, coste (con casa de referencia) y windfall por pata asegurada | `test_cli_compare_promo::test_promo_json_incluye_bloque_y_coste`, `test_cli_surebet_promo`/`freebet`/`bonus` (bloque `promo` en JSON) |
| RF-23 | Recordatorio de verificar cuotas | `test_cli_compare_promo::test_recordatorio_con_promo_por_stderr` (y los recordatorios existentes de surebet/freebet/bonus) |

## Requisitos no funcionales
- **Formato A (detalle por casa)**: el filtro necesita las cuotas por casa; `surebet`
  con `--promo` lee Formato A en vez del resumen de `compare --json`
  (`test_cli_surebet_promo`).
- **Decimal, no float**: coste, windfall y payout se calculan en `Decimal` (helpers
  `coste_promo`, `windfall_promo`, `payout_de_cuotas`, `payout_asegurado`); el
  redondeo a 2 decimales ocurre solo al presentar (constitución nº 8).
- **Casa distinta en coberturas**: en freebet/bonus el relleno de promo excluye la
  casa del bono (`posicion_promo_cobertura`; tests de exclusión, constitución nº 10).
- **Español / UTF-8**: bloque de promo, avisos y recordatorio en español.
- **Sin red**: la lista de casas es entrada del usuario (`--promo`).

## Demo manual (`ejemplos/cuotas-promo.json`)
Casa con promo: Bet365.

1. `python -m betting compare ejemplos/cuotas-promo.json --promo Bet365`
   - **Real Madrid vs Barça**: asegurar 1 baja el payout de 98.42 % a 96.17 %
     (**coste 2.25 pp**), 1 @2.00 Bet365 **vs** 2.10 Winamax (casa de referencia
     nombrada); las tres opciones juntas y el aviso de windfalls acumulables.
   - **Sevilla vs Betis**: asegurar 1 → **coste 0.00 pp** porque Bet365 (2.60) ya es
     la mejor cuota del "1" (seguro gratis, RF-13).
2. `python -m betting bonus ejemplos/cuotas-promo.json --casa Codere --importe 100 --min 1.5 --promo Bet365`
   - Bloque de promo con las coberturas de ganar posicionadas en Bet365: p. ej.
     "Real Madrid — anclado en X → cobertura 1: 172.50 € @2.00 Bet365 (ref 2.10
     Winamax), **coste 17.25 €, windfall 345.00 €**", con el aviso de acumulación;
     y un caso de **coste 0.00 €** (Sevilla, cobertura 1 @2.60 Bet365, ya la mejor).
3. `… --json` en cualquiera de los comandos → bloque `promo` reutilizable con casa,
   cuota, casa/cuota de referencia, coste y windfall (donde aplique).
4. `surebet ejemplos/cuotas-promo.json --inversion 100 --promo Bet365` → reparto con
   la cuota asegurada y su coste y windfall en euros.

## Estado
213 tests en verde con `pytest -q` (30 nuevos de la spec 005). Los 23 RF tienen
test asociado.
