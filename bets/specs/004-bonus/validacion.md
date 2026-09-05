# Validación — Spec 004 (Bonus: apuesta de menor coste para el rollover)

Trazabilidad de cada requisito funcional a su(s) test(s). Todos en verde.

| RF | Qué exige | Test(s) |
|----|-----------|---------|
| RF-1 | Calcula opciones por partido con la casa del bono | `test_cli_bonus::test_tabla_opciones_ordenadas_con_cuota_anclada`, `test_core_bonus_opciones::test_una_opcion_por_resultado_por_encima_de_la_minima` |
| RF-2 | Una opción por resultado ≥ cuota mínima | `test_core_bonus_opciones::test_una_opcion_por_resultado_por_encima_de_la_minima` |
| RF-3 | Ancla el importe en la casa del bono | `test_core_bonus_coste::test_coste_verificado_mismo_retorno_en_los_tres` |
| RF-4 | Cubre los otros dos con dinero normal en casa distinta | `test_core_bonus_opciones::test_cobertura_excluye_la_casa_del_bono` |
| RF-5 | Retorno igual gane quien gane | `test_core_bonus_coste::test_coste_verificado_mismo_retorno_en_los_tres` |
| RF-6 | Cobertura a la mejor cuota en casa distinta (empate determinista) | `test_core_bonus_opciones::test_cobertura_excluye_la_casa_del_bono` |
| RF-7 | Coste = apostado − retorno, en euros | `test_core_bonus_coste::test_coste_verificado_mismo_retorno_en_los_tres` |
| RF-8 | Muestra resultado anclado, cuota, importe y coberturas | `test_cli_bonus::test_tabla_opciones_ordenadas_con_cuota_anclada`, `test_cli_bonus::test_json_parseable_y_coherente` |
| RF-9 | Ordena las opciones por coste ascendente | `test_core_bonus_plazo_orden::test_opciones_ordenadas_por_coste_ascendente`, `test_cli_bonus::test_json_parseable_y_coherente` |
| RF-10 | Coste negativo (arbitraje) se muestra sin trato especial | `test_core_bonus_coste::test_coste_negativo_cuando_hay_arbitraje` |
| RF-11 | Resultado bajo la cuota mínima se omite | `test_core_bonus_opciones::test_resultado_bajo_la_cuota_minima_se_omite` |
| RF-12 | Resultado no cubrible → descarte con motivo | `test_core_bonus_opciones::test_resultado_no_cubrible_genera_descarte` |
| RF-13 | Casa del bono ausente → descarte del partido | `test_core_bonus_opciones::test_casa_del_bono_ausente_descarta_el_partido` |
| RF-14 | `fecha` opcional; su ausencia no impide el cálculo | `test_core_bonus_plazo_orden::test_sin_limite_ignora_fechas` |
| RF-15 | Con límite, descarta partidos posteriores | `test_core_bonus_plazo_orden::test_fuera_de_plazo_descarta_el_partido`, `test_cli_bonus::test_fuera_de_plazo_aparece_en_descartes` |
| RF-16 | Con límite y sin fecha → aviso pero se evalúa | `test_core_bonus_plazo_orden::test_sin_fecha_con_limite_avisa_pero_evalua`, `test_cli_bonus::test_aviso_sin_fecha_por_stderr` |
| RF-17 | Sin límite → ignora fechas | `test_core_bonus_plazo_orden::test_sin_limite_ignora_fechas` |
| RF-18 | Importe ≤ 0 → error, salida ≠ 0 | `test_core_bonus_config::test_importe_no_positivo_es_error`, `test_cli_bonus::test_importe_invalido_error_y_salida_1` |
| RF-19 | Cuota mínima ≤ 1 → error, salida ≠ 0 | `test_core_bonus_config::test_cuota_minima_no_mayor_que_1_es_error`, `test_cli_bonus::test_cuota_minima_invalida_error_y_salida_1` |
| RF-20 | Casa del bono no indicada → error, salida ≠ 0 | `test_core_bonus_config::test_casa_no_indicada_es_error`, `test_cli_bonus::test_casa_no_indicada_error_y_salida_1` |
| RF-21 | Archivo inválido/repetidos → error, salida ≠ 0 | `test_cli_bonus::test_archivo_corrupto_error_y_salida_1`, `test_storage` y `test_core_duplicados` (reutilizados) |
| RF-22 | Sin partidos → mensaje, salida 0 | `test_cli_bonus::test_sin_partidos_mensaje_y_salida_0` |
| RF-23 | Sin opciones válidas → mensaje, salida 0 | `test_cli_bonus::test_sin_opciones_validas_mensaje_y_salida_0` |
| RF-24 | Nombre de casa del bono normalizado | reutiliza `core.normalizar` (spec 001, `test_core_duplicados::test_normalizar_*`); `_entrada_de_casa` compara normalizado |
| RF-25 | Salida `--json` reutilizable | `test_cli_bonus::test_json_parseable_y_coherente` |
| RF-26 | Importes/cuotas/coste a 2 decimales | `test_cli_bonus::test_json_parseable_y_coherente` |
| RF-27 | Recordatorio de verificar cuotas | `test_cli_bonus::test_recordatorio_de_cuotas_por_stderr` |

## Requisitos no funcionales
- **Decimal, no float**: importe y cuota mínima se normalizan a `Decimal`
  (`test_core_bonus_config`); coberturas y coste operan en `Decimal` y solo se
  redondean a 2 decimales al presentar.
- **Fechas ISO 8601 sin zonas horarias**: `datetime.fromisoformat`; comparación
  cronológica directa (`test_core_bonus_plazo_orden`).
- **Español / UTF-8**: mensajes, tabla, avisos y recordatorio en español.
- **Sin red**: la única entrada son el archivo y los parámetros del bono.

## Demo manual (`ejemplos/cuotas-bonus.json`)
Bono de Luckia de 100 €, cuota mínima 1.50:

1. `python -m betting bonus ejemplos/cuotas-bonus.json --casa Luckia --importe 100 --min 1.5`
   → opciones ordenadas por coste: Sevilla vs Betis (anclar 2 @2.60, coste 9.12 €),
   Real Madrid vs Barça (anclar 1 @2.10, 10.10 €) y (anclar X @3.30, 20.32 €), con
   la cuota anclada visible. Descartados: Sevilla /1 y /X (el "2" no se puede
   cubrir en casa distinta), Cádiz vs Elche (Luckia no participa). El "2" de Real
   Madrid (1.30) se omite por estar bajo la cuota mínima.
2. `… --fecha-limite 2026-09-15` → Sevilla vs Betis (2026-09-20) sale como fuera
   de plazo y Cádiz vs Elche (sin fecha) avisa por stderr.
3. `… --json` → mismo resultado en JSON reutilizable (importes, cuotas y coste
   como string; opciones ordenadas por coste y lista de descartes).

## Estado
141 tests en verde con `pytest -q` (27 nuevos de la spec 004). Los 27 RF tienen
test asociado.
