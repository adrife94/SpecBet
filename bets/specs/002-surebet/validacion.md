# Validación — Spec 002 (Surebet: reparto de stake)

Trazabilidad de cada requisito funcional a su(s) test(s). Todos en verde.

| RF | Qué exige | Test(s) |
|----|-----------|---------|
| RF-1 | Reparto por partido desde la salida de compare + inversión | `test_core_surebet::test_reparto_verificado_suma_inversion_y_retorno_igual`, `test_cli_surebet::test_tabla_muestra_reparto_estado_e_importes` |
| RF-2 | Retorno igual gane quien gane | `test_core_surebet::test_reparto_verificado_suma_inversion_y_retorno_igual` (cada importe·cuota = 100.80) |
| RF-3 | Los tres importes suman la inversión | `test_core_surebet::test_reparto_verificado_suma_inversion_y_retorno_igual` (suma = 100.00) |
| RF-4 | Mostrar importe, cuota y casa por resultado | `test_cli_surebet::test_tabla_muestra_reparto_estado_e_importes`, `test_cli_surebet::test_json_parseable_coherente_y_ordenado` |
| RF-5 | Retorno y beneficio garantizados por partido | `test_core_surebet::test_reparto_verificado_suma_inversion_y_retorno_igual`, `test_core_surebet::test_surebet_beneficio_positivo` |
| RF-6 | Payout > 100 → surebet, beneficio > 0 | `test_core_surebet::test_surebet_beneficio_positivo` |
| RF-7 | Payout ≤ 100 → pérdida, beneficio ≤ 0 | `test_core_surebet::test_perdida_beneficio_negativo`, `test_core_surebet::test_payout_exacto_100_beneficio_cero_no_es_surebet` |
| RF-8 | Empate de casas listado, importe íntegro (no dividido) | `test_core_surebet::test_empate_de_casas_conserva_la_lista_sin_dividir_importe`, `test_cli_surebet::test_json_parseable_coherente_y_ordenado` |
| RF-9 | Partido incompleto → no calculable, sin reparto | `test_core_surebet::test_incompleto_no_es_calculable`, `test_cli_surebet::test_json_partido_no_calculable_lleva_nulls` |
| RF-10 | Orden por beneficio desc, no calculables al final | `test_core_surebet::test_orden_calculables_por_beneficio_desc_y_no_calculables_al_final`, `test_cli_surebet::test_json_parseable_coherente_y_ordenado` |
| RF-11 | Importes/retorno/beneficio a 2 decimales | `test_cli_surebet::test_tabla_muestra_reparto_estado_e_importes`, `test_cli_surebet::test_json_parseable_coherente_y_ordenado` |
| RF-12 | Inversión no válida (≤ 0 / no numérica) → error, salida ≠ 0 | `test_cli_surebet::test_inversion_invalida_error_y_salida_1` (0, -5, "abc") |
| RF-13 | Entrada inexistente/corrupta/ajena al comparador → error, salida ≠ 0 | `test_storage_comparacion` (inexistente, JSON inválido, estructura ajena, falta `mejores`), `test_cli_surebet::test_entrada_corrupta_error_y_salida_1` |
| RF-14 | Entrada sin partidos → mensaje, salida 0 | `test_storage_comparacion::test_entrada_sin_partidos_devuelve_lista_vacia`, `test_cli_surebet::test_entrada_sin_partidos_mensaje_y_salida_0` |
| RF-15 | Salida `--json` reutilizable | `test_cli_surebet::test_json_parseable_coherente_y_ordenado`, `::test_json_partido_no_calculable_lleva_nulls`, `::test_json_stdout_limpio_recordatorio_en_stderr` |
| RF-16 | Recordatorio de verificar cuotas antes de apostar | `test_cli_surebet::test_recordatorio_de_verificar_cuotas_por_stderr`, `::test_json_stdout_limpio_recordatorio_en_stderr` |

## Requisitos no funcionales
- **Decimal, no float**: cuotas y payout se reconvierten a `Decimal` al cargar
  (`test_storage_comparacion::test_cuotas_y_payout_se_reconvierten_a_decimal`); el
  reparto opera en `Decimal` y solo se redondea a 2 decimales al presentar.
- **Suma ≤ 1 céntimo de desviación**: consecuencia del redondeo de presentación;
  visible en la demo (Sevilla vs Betis: 38.73 + 29.65 + 31.63 = 100.01). El
  reparto interno es exacto (`test_..._suma_inversion_y_retorno_igual` sobre los
  importes sin redondear).
- **Español / UTF-8**: mensajes, tabla y recordatorio en español; salida forzada
  a UTF-8 en la CLI (acentos y `—` sin romper en consolas Windows).
- **Sin red**: la única entrada es la salida de compare y la inversión; sin IO de
  red.

## Demo manual (encadenando compare → surebet)
Ejemplo con arbitraje: `ejemplos/partidos-surebet.json`.

1. `python -m betting compare ejemplos/partidos-surebet.json --json > ejemplos/comparacion-surebet.json`
2. `python -m betting surebet ejemplos/comparacion-surebet.json --inversion 100`

Salida observada:
- **Arbitraje FC vs United** → `surebet`, % pago 100.80, retorno 100.80,
  beneficio +0.80; reparto 48.00 (Bet365, 2.10) / 28.00 (Codere, 3.60) /
  24.00 (Codere, 4.20), suma 100.00.
- **Sevilla vs Betis** → `pérdida`, beneficio -5.12 (importes que reparten 100 €).
- **Atlético vs Valencia** → `no calc.` (una sola casa, llega incompleto),
  colocado al final.
- `--inversion 0` / `abc` → error por stderr y salida 1.
- `--json` → mismo resultado en JSON reutilizable (importes/retorno/beneficio y
  cuotas como string; `surebet`, `no_calculable`, `casas` como lista; `patas`,
  `retorno` y `beneficio` a `null` en el no calculable), con el recordatorio de
  verificar cuotas por stderr.

## Estado
71 tests en verde con `pytest -q` (24 nuevos de la spec 002). Los 16 RF tienen
test asociado.
