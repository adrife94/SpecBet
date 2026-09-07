# Validación — Spec 006 (Multibono: rollover coordinado)

Trazabilidad de cada requisito funcional a su(s) test(s). Todos en verde.

| RF | Qué exige | Test(s) |
|----|-----------|---------|
| RF-1 | Calcula, por partido, la mejor opción de reparto | `test_cli_multibono::test_tabla_con_patas_y_descartes`, `test_core_multibono_plazo_orden::test_orden_por_perdida_ascendente_con_negativo` |
| RF-2 | Admite 2 o 3 bonos; menos/más → error, salida ≠ 0 | `test_core_multibono_config::test_menos_de_dos_bonos_es_error`, `::test_mas_de_tres_bonos_es_error`, `test_cli_multibono::test_menos_de_dos_bonos_error_y_salida_1`, `::test_mas_de_tres_bonos_error_y_salida_1` |
| RF-3 | Importe > 0 y cuota mínima > 1 → error si no | `test_core_multibono_config::test_importe_no_positivo_es_error`, `::test_cuota_minima_no_mayor_que_1_es_error` |
| RF-4 | Casas de bono distintas entre sí → error si no | `test_core_multibono_config::test_casas_repetidas_es_error` |
| RF-5 | Archivo inválido/repetidos → error, salida ≠ 0 | `test_cli_multibono::test_archivo_corrupto_error_y_salida_1`; reutiliza `storage` y `test_core_duplicados` |
| RF-6 | Nombres de casa normalizados (mayús./espacios) | `test_core_multibono_config::test_casas_repetidas_es_error` (` luckia ` = `Luckia`); `test_core_multibono_asignacion::test_mejor_cuota_excluyendo_ignora_casas_de_bono` |
| RF-7 | Cada bono entero en un resultado distinto | `test_core_multibono_opcion::test_tres_bonos_caso_verificado_a_mano`, `test_core_multibono_asignacion::test_empate_de_perdida_es_determinista_por_orden_de_permutacion` |
| RF-8 | Solo ancla si la cuota ≥ cuota mínima | `test_core_multibono_asignacion::test_bono_por_debajo_de_la_minima_en_todo_el_partido_es_descarte` |
| RF-9 | Elige la asignación de menor pérdida (empate determinista) | `test_core_multibono_asignacion::test_elige_la_asignacion_de_menor_perdida_con_importes_distintos`, `::test_empate_de_perdida_es_determinista_por_orden_de_permutacion` |
| RF-10 | Con 3 bonos, uno en cada resultado (1, X, 2) | `test_core_multibono_opcion::test_tres_bonos_caso_verificado_a_mano` |
| RF-11 | Con 2 bonos, el tercer resultado va solo con dinero real | `test_core_multibono_opcion::test_dos_bonos_tercer_resultado_solo_con_dinero_real`, `test_core_multibono_asignacion::test_dos_bonos_dejan_un_resultado_solo_con_dinero_real` |
| RF-12 | Retorno objetivo R = techo del mayor bono | `test_core_multibono_opcion::test_tres_bonos_caso_verificado_a_mano` (R = 600) |
| RF-13 | Relleno de cada resultado por debajo de R | `test_core_multibono_opcion::test_tres_bonos_caso_verificado_a_mano` |
| RF-14 | Resultado sin bono cubierto entero hasta R | `test_core_multibono_opcion::test_dos_bonos_tercer_resultado_solo_con_dinero_real` |
| RF-15 | Relleno en casa distinta a todas las de bono, mejor cuota (empate determinista) | `test_core_multibono_asignacion::test_mejor_cuota_excluyendo_ignora_casas_de_bono`, `::test_el_relleno_excluye_todas_las_casas_de_bono` |
| RF-16 | Resultado no rellenable → descarte con motivo | `test_core_multibono_asignacion::test_resultado_no_rellenable_es_descarte`, `::test_mejor_cuota_excluyendo_sin_casa_valida_es_none` |
| RF-17 | Casa de bono ausente → descarte con motivo | `test_core_multibono_asignacion::test_casa_de_bono_ausente_es_descarte`, `test_core_multibono_plazo_orden::test_ninguna_opcion_valida_devuelve_solo_descartes` |
| RF-18 | Pérdida = (bonos + dinero real) − R, en euros | `test_core_multibono_opcion::test_tres_bonos_caso_verificado_a_mano` (pérdida = 50) |
| RF-19 | Pérdida en % sobre el total de bono | `test_core_multibono_opcion::test_tres_bonos_caso_verificado_a_mano` (50/300) |
| RF-20 | Dinero real total a desplegar | `test_core_multibono_opcion::test_tres_bonos_caso_verificado_a_mano` (350) |
| RF-21 | Retorno garantizado R y neto = R − dinero real | `test_core_multibono_opcion::test_tres_bonos_caso_verificado_a_mano` (neto = 250), `::test_perdida_negativa_es_arbitraje` |
| RF-22 | Ordena por pérdida ascendente | `test_core_multibono_plazo_orden::test_orden_por_perdida_ascendente_con_negativo`, `test_cli_multibono::test_json_parseable_y_coherente` |
| RF-23 | Muestra el dinero real; ordena por pérdida (parejo ≠ poca pérdida) | `test_core_multibono_plazo_orden::test_orden_por_perdida_ascendente_con_negativo` (parejo 40 € por encima del deseq. 50 €), `test_cli_multibono::test_tabla_con_patas_y_descartes` |
| RF-24 | Pérdida negativa (arbitraje) se muestra sin trato especial | `test_core_multibono_opcion::test_perdida_negativa_es_arbitraje`, `test_core_multibono_plazo_orden::test_orden_por_perdida_ascendente_con_negativo` |
| RF-25 | `fecha` opcional; su ausencia no impide el cálculo | `test_core_multibono_plazo_orden::test_partido_sin_fecha_con_apalancamiento_se_evalua_con_aviso`, `::test_sin_apalancamiento_se_ignoran_las_fechas` |
| RF-26 | Descarta partidos en la fecha del apalancamiento o después | `test_core_multibono_plazo_orden::test_fuera_de_plazo_en_esa_fecha_o_despues_se_descarta`, `test_cli_multibono::test_apalancamiento_fuera_de_plazo` |
| RF-27 | Con apalancamiento y sin fecha → aviso pero se evalúa | `test_core_multibono_plazo_orden::test_partido_sin_fecha_con_apalancamiento_se_evalua_con_aviso`, `test_cli_multibono::test_aviso_sin_fecha_por_stderr` |
| RF-28 | Sin apalancamiento → ignora las fechas | `test_core_multibono_plazo_orden::test_sin_apalancamiento_se_ignoran_las_fechas` |
| RF-29 | Muestra partido, patas (bono/relleno), R, real, pérdida €/%, neto | `test_cli_multibono::test_tabla_con_patas_y_descartes` |
| RF-30 | Salida `--json` reutilizable | `test_cli_multibono::test_json_parseable_y_coherente` |
| RF-31 | Importes/cuotas/%/pérdida a 2 decimales | `test_cli_multibono::test_json_parseable_y_coherente` |
| RF-32 | Recordatorio de verificar cuotas | `test_cli_multibono::test_recordatorio_de_cuotas_por_stderr` |
| RF-33 | Sin partidos → mensaje, salida 0 | `test_cli_multibono::test_sin_partidos_mensaje_y_salida_0`, `test_core_multibono_plazo_orden::test_sin_partidos_devuelve_listas_vacias` |
| RF-34 | Sin opciones válidas → mensaje, salida 0 | `test_cli_multibono::test_sin_opciones_validas_mensaje_y_salida_0`, `test_core_multibono_plazo_orden::test_ninguna_opcion_valida_devuelve_solo_descartes` |

## Requisitos no funcionales
- **Decimal, no float**: importes y cuotas se normalizan a `Decimal`
  (`test_core_multibono_config`); R, relleno, pérdida y neto operan en `Decimal` y
  solo se redondean a 2 decimales al presentar (`_eur` en la CLI).
- **Formato A (detalle por casa)**: la entrada es el mismo JSON que `compare`; el
  reparto y el relleno eligen casas concretas.
- **Fechas ISO 8601 sin zonas horarias**: `datetime.fromisoformat`, comparación
  cronológica directa (`test_core_multibono_plazo_orden`).
- **Español / UTF-8**: cabecera, tabla, descartes, avisos y recordatorio en español.
- **Sin red**: la única entrada son el archivo de cuotas, los bonos y la fecha de
  apalancamiento opcional.

## Demo manual (`ejemplos/cuotas-multibono.json`)
Tres bonos de 100 € (Luckia, Bet365, Winamax), cuota mínima 1.50:

1. `python -m betting multibonus ejemplos/cuotas-multibono.json --bono Luckia:100:1.5 --bono Bet365:100:1.5 --bono Winamax:100:1.5`
   - **(a)** Real Madrid vs Barça (casi 3/3/3): **pérdida −1.44 € (−0.48 %)**, dinero
     real 8.56 €, retorno 310 € — poca inversión real y hasta beneficio.
   - **(b)** Sevilla vs Betis (2.60/2.60/2.60): **pérdida 40 € (13.33 %)** con **0 € de
     dinero real**, y aun así queda **por debajo** de Real Madrid: se ordena por
     pérdida, no por lo parejo ni por evitar dinero real.
   - **(d)** Descartados: Cádiz vs Elche (falta Winamax) y Valencia vs Villarreal
     (el "1", a cuota 1.50, no se puede rellenar fuera de las casas de bono).
2. `… --apalancamiento 2026-09-15` → **(e)** Sevilla vs Betis (2026-09-20) sale como
   fuera de plazo y Cádiz vs Elche (sin fecha) avisa por stderr.
3. `… --bono Luckia:100:2.0 --bono Bet365:100:2.0` (solo 2 bonos) → **(c)** el tercer
   resultado se cubre solo con dinero real; además Winamax, al no ser ya casa de
   bono, pasa a estar disponible para el relleno (Valencia vs Villarreal deja de
   descartarse). La pérdida en % se calcula sobre 200 € de bono (Sevilla → 20 %).
4. `… --json` → **(f)** mismo resultado en JSON reutilizable (importes, cuotas, R,
   pérdida, % y neto como string; opciones ordenadas por pérdida y lista de descartes).

## Estado
183 tests en verde con `pytest -q` (42 nuevos de la spec 006). Los 34 RF tienen
test asociado.
