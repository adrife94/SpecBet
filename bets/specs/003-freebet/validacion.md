# Validación — Spec 003 (Freebet: cobertura y valor)

Trazabilidad de cada requisito funcional a su(s) test(s). Todos en verde.

| RF | Qué exige | Test(s) |
|----|-----------|---------|
| RF-1 | Calcula por partido con la casa del bono | `test_cli_freebet::test_tabla_un_bono_listado_con_valor_y_conversion`, `test_core_freebet_partido::test_orden_por_valor_y_recomendada_primera` |
| RF-2 | Cobertura con mismo neto gane quien gane | `test_core_freebet::test_conversion_verificada_neto_igual_en_los_tres` |
| RF-3 | Igualación del beneficio (retorno común) | `test_core_freebet::test_conversion_verificada_neto_igual_en_los_tres` |
| RF-4 | Valor extraído en € y % de conversión | `test_core_freebet::test_conversion_verificada_neto_igual_en_los_tres`, `test_cli_freebet::test_json_parseable_y_coherente` |
| RF-5 | Muestra resultado/importe/cuota/casa por pata | `test_core_freebet::test_patas_una_gratis_y_dos_cobertura_en_orden`, `test_cli_freebet::test_json_parseable_y_coherente` |
| RF-6 | Auto elige el de mayor valor | `test_core_freebet_seleccion::test_auto_elige_el_resultado_de_mayor_valor` |
| RF-7 | Resultado fijado usa solo ese | `test_core_freebet_seleccion::test_resultado_fijado_usa_solo_ese` |
| RF-8 | Partido fijado calcula solo ese | `test_core_freebet_partido::test_partido_fijado_evalua_solo_ese` |
| RF-9 | Rango de cuota en la pata gratis | `test_core_freebet_seleccion::test_rango_maximo_descarta_resultados_fuera_de_rango` |
| RF-10 | Fijado fuera de rango no se propone | `test_core_freebet_seleccion::test_resultado_fijado_fuera_de_rango_no_se_propone` |
| RF-11 | Cobertura a la mejor cuota en casa distinta | `test_core_freebet_seleccion::test_cobertura_excluye_la_casa_del_bono` |
| RF-12 | 1–2 casas de cobertura, nunca la del bono | `test_core_freebet_seleccion::test_cobertura_excluye_la_casa_del_bono` |
| RF-13 | Resultado no cubrible no da jugada | `test_core_freebet_seleccion::test_resultado_no_cubrible_no_da_jugada` |
| RF-14 | Casa del bono ausente → no jugable | `test_core_freebet_partido::test_casa_del_bono_ausente_no_jugable`, `test_cli_freebet::test_tabla_un_bono_listado_con_valor_y_conversion` |
| RF-15 | Listado por valor desc, no jugables al final | `test_core_freebet_partido::test_orden_por_valor_y_recomendada_primera` |
| RF-16 | Nombre de casa del bono normalizado | `test_core_freebet_seleccion::test_casa_del_bono_normalizada_por_caja_y_espacios` |
| RF-17 | Importe ≤ 0 → error, salida ≠ 0 | `test_storage_bonos::test_importe_no_positivo_es_error`, `test_cli_freebet::test_importe_invalido_error_y_salida_1` |
| RF-18 | Sin casa ni bonos → error, salida ≠ 0 | `test_cli_freebet::test_sin_casa_ni_bonos_error_y_salida_1` |
| RF-19 | Archivo inválido/repetidos → error ≠ 0 | `test_cli_freebet::test_archivo_corrupto_error_y_salida_1`, `test_storage` (estructura), `test_core_duplicados` (repetidos, reutilizado) |
| RF-20 | Sin partidos → mensaje, salida 0 | `test_cli_freebet::test_sin_partidos_mensaje_y_salida_0` |
| RF-21 | Salida `--json` reutilizable | `test_cli_freebet::test_json_parseable_y_coherente` |
| RF-22 | Recordatorio de verificar cuotas | `test_cli_freebet::test_recordatorio_de_cuotas_por_stderr` |
| RF-23 | `fecha` opcional; su ausencia no rompe | `test_core_freebet_partido::test_sin_limite_ignora_fechas` |
| RF-24 | Con límite, solo partidos ≤ límite | `test_core_freebet_partido::test_dentro_de_plazo_es_jugable` |
| RF-25 | Partido posterior al límite → fuera de plazo | `test_core_freebet_partido::test_fuera_de_plazo_no_jugable`, `test_cli_freebet::test_fuera_de_plazo_marca_no_jugable` |
| RF-26 | Con límite y sin fecha → aviso pero se evalúa | `test_core_freebet_partido::test_sin_fecha_con_limite_avisa_pero_se_evalua`, `test_cli_freebet::test_aviso_sin_fecha_por_stderr` |
| RF-27 | Sin límite → ignora fechas | `test_core_freebet_partido::test_sin_limite_ignora_fechas` |
| RF-28 | Uno o varios bonos en un lote | `test_core_freebet_lote::test_valor_total_y_conversion_total`, `test_cli_freebet::test_lote_dos_bonos_valor_total` |
| RF-29 | Cada bono independiente | `test_core_freebet_lote::test_valor_total_y_conversion_total` |
| RF-30 | Valor total + % de conversión total | `test_core_freebet_lote::test_valor_total_y_conversion_total`, `test_cli_freebet::test_lote_dos_bonos_valor_total` |
| RF-31 | Aviso de colisión entre bonos | `test_core_freebet_lote::test_colision_detectada_entre_recomendadas`, `test_cli_freebet::test_colision_entre_dos_bonos_avisa` |
| RF-32 | Bono sin plan cuenta 0 y no tumba el lote | `test_core_freebet_lote::test_bono_sin_plan_cuenta_cero_y_no_tumba_el_lote` |
| RF-33 | Recomendada = primera del listado | `test_core_freebet_partido::test_orden_por_valor_y_recomendada_primera` |
| RF-34 | Detalla patas de cada partido | `test_cli_freebet::test_json_parseable_y_coherente` (patas por partido), `test_core_freebet::test_patas_una_gratis_y_dos_cobertura_en_orden` |

## Requisitos no funcionales
- **Decimal, no float**: importe/min/max se cargan como `Decimal`
  (`test_storage_bonos::test_importe_y_rango_se_cargan_como_decimal`); el reparto
  opera en `Decimal` y solo se redondea a 2 decimales al presentar.
- **Fechas ISO 8601 sin zonas horarias**: `datetime.fromisoformat`; comparación
  cronológica directa (`test_core_freebet_partido` de plazo).
- **Español / UTF-8**: mensajes, tabla, avisos y recordatorio en español; salida
  forzada a UTF-8 en la CLI.
- **Sin red**: la única entrada son los archivos de cuotas y de bonos y los
  parámetros del bono.

## Demo manual (encadenando cuotas → freebet)
Ejemplos: `ejemplos/cuotas-freebet.json` (con `fecha` y una casa ausente) y
`ejemplos/bonos.json` (lote de dos bonos).

1. Auto: `python -m betting freebet ejemplos/cuotas-freebet.json --casa Luckia --importe 10`
   → recomienda "Real Madrid vs Barça" (valor 6.37 €, conversión 63.71 %),
   detalla las patas de cada partido, "Atlético vs Valencia" sin fecha y
   "Cádiz vs Elche" no jugable (Luckia no participa).
2. Manual: `… --partido "Sevilla vs Betis" --resultado 1` → calcula solo ese
   partido.
3. Lote: `python -m betting freebet ejemplos/cuotas-freebet.json --bonos ejemplos/bonos.json`
   → Luckia (límite 2026-09-15 deja "Sevilla vs Betis" fuera de plazo; avisa de
   "Atlético vs Valencia" sin fecha) + Sportium; valor total 68.85 €
   (conversión total 62.59 %) y avisos de colisión en Bet365.
4. `--json` → mismo resultado en JSON reutilizable (importes/valor/% como string;
   `patas` a `null` en los no jugables).

## Estado
114 tests en verde con `pytest -q` (43 nuevos de la spec 003). Los 34 RF tienen
test asociado.
