# Validación — Spec 001 (Comparador de cuotas / % de pago)

Trazabilidad de cada requisito funcional a su(s) test(s). Todos en verde.

| RF | Qué exige | Test(s) |
|----|-----------|---------|
| RF-1 | Tabla con una fila por partido | `test_cli_compare::test_tabla_basica` |
| RF-2 | Mejor cuota = la más alta | `test_core_mejores::test_mejor_cuota_es_la_mas_alta` |
| RF-3 | % de pago = 100/Σ(1/cuota), 2 decimales | `test_core_payout::test_caso_verificado_95_41`, `test_payout_exacto_100_sin_margen` |
| RF-4 | Mostrar mejor cuota y su casa | `test_core_mejores::test_mejor_cuota_es_la_mas_alta`, `test_cli_compare::test_tabla_basica` |
| RF-5 | Empate en mejor cuota → todas las casas | `test_core_mejores::test_empate_lista_todas_las_casas_en_orden`, `test_cli_compare::test_empate_muestra_ambas_casas`, `test_cli_json::test_json_empate_lista_ambas_casas` |
| RF-6 | Orden por % de pago descendente | `test_core_orden::test_orden_completos_desc_luego_incompletos` |
| RF-7 | Hueco por casa se ignora | `test_core_mejores::test_hueco_por_casa_se_ignora`, `test_clave_nula_es_hueco_sin_aviso` |
| RF-8 | Cuota inválida descartada con aviso | `test_core_mejores::test_cuota_invalida_se_descarta_con_aviso`, `test_cli_compare::test_cuota_invalida_avisa_por_stderr_y_sigue` |
| RF-9 | Resultado sin cuota → incompleto | `test_core_incompleto::test_incompleto_si_falta_un_resultado_en_todas_las_casas` |
| RF-10 | Incompletos al final | `test_core_orden::test_orden_completos_desc_luego_incompletos`, `test_cli_compare::test_incompleto_va_al_final_con_guion` |
| RF-11 | Archivo inválido → error, salida ≠ 0 | `test_storage` (5 casos), `test_cli_compare::test_archivo_corrupto_error_y_salida_1` |
| RF-12 | Archivo sin partidos → mensaje, salida 0 | `test_storage::test_archivo_valido_sin_partidos_devuelve_lista_vacia`, `test_cli_compare::test_archivo_vacio_mensaje_y_salida_0` |
| RF-13 | Nombres normalizados (caja/espacios) | `test_core_duplicados::test_normalizar_*` |
| RF-14 | Menos de 2 casas → incompleto | `test_core_incompleto::test_incompleto_con_una_sola_casa_aunque_tenga_los_tres` |
| RF-15 | Casa repetida en un partido → error | `test_core_duplicados::test_casa_duplicada_en_un_partido` |
| RF-16 | Partido repetido → error | `test_core_duplicados::test_partido_duplicado_distinta_caja_y_espacios`, `test_cli_compare::test_partido_duplicado_error_y_salida_1` |
| RF-17 | Neutro ante % de pago > 100 % | `test_core_orden::test_surebet_no_recibe_marca_especial_solo_se_ordena` |
| RF-18 | Salida `--json` reutilizable | `test_cli_json` (5 tests) |

## Requisitos no funcionales
- **Decimal, no float**: `test_storage::test_cuotas_se_cargan_como_decimal` y
  `test_core_payout::test_payout_no_se_redondea_en_el_core` (redondeo solo al
  presentar).
- **Español / UTF-8**: mensajes y tabla en español; salida forzada a UTF-8 en la
  CLI (acentos y `—` sin romper en consolas Windows).
- **Sin red**: la única entrada es el archivo JSON; no hay IO de red en el código.

## Demo manual (archivo `ejemplos/partidos.json`)
- `python -m betting compare ejemplos/partidos.json` → tabla ordenada de mayor a
  menor % de pago, con el partido de una sola casa (incompleto) al final con `—`,
  y aviso por stderr de la cuota `"N/A"` descartada.
- `python -m betting compare ejemplos/partidos.json --json` → mismo resultado en
  JSON reutilizable (payout/cuotas como string, `incompleto`, `casas` en lista).

## Estado
47 tests en verde con `pytest -q`. Los 18 RF tienen test asociado.
