import 'package:decimal/decimal.dart';
import 'package:flutter/material.dart';

import '../../core/compare.dart';
import '../../core/money.dart';
import '../../state/app_state.dart';
import '../theme.dart';
import '../widgets/metric_badge.dart';
import '../widgets/promo_panel.dart';

class ComparadorScreen extends StatelessWidget {
  const ComparadorScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final state = AppScope.of(context);
    final p = Theme.of(context).extension<AppPalette>()!;
    final evaluados = comparar(state.partidos);

    return ListView(
      padding: const EdgeInsets.all(18),
      children: [
        const Text('Comparador', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w600)),
        Text(
          'Ordenado por % de pago. Se resalta la mejor cuota de cada resultado; los incompletos, al final.',
          style: TextStyle(color: p.ink2, fontSize: 12.5),
        ),
        const SizedBox(height: 14),
        Card(
          margin: EdgeInsets.zero,
          color: p.panel,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(10),
            side: BorderSide(color: p.line),
          ),
          child: SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: DataTable(
              headingRowColor: WidgetStatePropertyAll(p.panel2),
              columns: const [
                DataColumn(label: Text('Partido')),
                DataColumn(label: Text('% de pago')),
                DataColumn(label: Text('Mejor 1')),
                DataColumn(label: Text('Mejor X')),
                DataColumn(label: Text('Mejor 2')),
              ],
              rows: [
                for (final ev in evaluados)
                  DataRow(cells: [
                    DataCell(Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(ev.nombre, style: const TextStyle(fontWeight: FontWeight.w600)),
                        Text(ev.fecha ?? 'sin fecha', style: mono.copyWith(fontSize: 10.5, color: p.ink3)),
                      ],
                    )),
                    DataCell(MetricBadge(value: ev.payout == null ? '—' : pct(ev.payout!), tono: _tono(ev))),
                    for (final r in ['1', 'X', '2']) DataCell(_celda(ev.mejores[r], p)),
                  ]),
              ],
            ),
          ),
        ),
        PromoPanel(importeRef: Decimal.fromInt(100)),
      ],
    );
  }

  String _tono(PartidoEvaluado ev) {
    final pay = ev.payout;
    if (pay == null) return 'gray';
    if (pay >= cien) return 'green';
    if (pay >= Decimal.fromInt(97)) return 'amber';
    return 'gray';
  }

  Widget _celda(MejorCuota? m, AppPalette p) {
    if (m == null) return Text('—', style: mono.copyWith(color: p.ink3));
    return Column(
      mainAxisAlignment: MainAxisAlignment.center,
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(cuotaStr(m.cuota), style: mono.copyWith(fontSize: 13.5, fontWeight: FontWeight.w600)),
        Text(m.casas.join('/'), style: TextStyle(fontSize: 11, color: p.ink2)),
      ],
    );
  }
}
