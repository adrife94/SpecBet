import 'package:flutter/material.dart';

import '../../core/money.dart';
import '../../core/odds.dart';
import '../../state/app_state.dart';
import '../theme.dart';

class CuotasScreen extends StatelessWidget {
  const CuotasScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final state = AppScope.of(context);
    final p = Theme.of(context).extension<AppPalette>()!;
    final casas = state.casas;

    return ListView(
      padding: const EdgeInsets.all(18),
      children: [
        Row(
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('Cuotas', style: TextStyle(fontSize: 22, fontWeight: FontWeight.w600)),
                  Text(
                    'Fuente única compartida por las herramientas. Importa el JSON del navegador.',
                    style: TextStyle(color: p.ink2, fontSize: 12.5),
                  ),
                ],
              ),
            ),
            FilledButton(
              onPressed: () => _importar(context, state),
              child: const Text('Importar JSON'),
            ),
          ],
        ),
        const SizedBox(height: 14),
        Wrap(spacing: 8, runSpacing: 8, children: [
          _badge(p, 'Partidos', '${state.partidos.length}'),
          _badge(p, 'Casas', '${casas.length}'),
        ]),
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
              columns: [
                const DataColumn(label: Text('Partido')),
                for (final c in casas) DataColumn(label: Text(c)),
              ],
              rows: [
                for (final partido in state.partidos)
                  DataRow(cells: [
                    DataCell(Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(partido.nombre, style: const TextStyle(fontWeight: FontWeight.w600)),
                        Text(partido.fecha ?? 'sin fecha', style: mono.copyWith(fontSize: 10.5, color: p.ink3)),
                      ],
                    )),
                    for (final c in casas) DataCell(_trio(partido.casa(c), p)),
                  ]),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _trio(CuotaCasa? c, AppPalette p) {
    String s(String r) => cuotaStr(c?[r]);
    return Text('${s('1')} / ${s('X')} / ${s('2')}', style: mono.copyWith(fontSize: 12));
  }

  Widget _badge(AppPalette p, String label, String value) => Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
        decoration: BoxDecoration(color: p.grayBg, borderRadius: BorderRadius.circular(7)),
        child: Text('$label  $value', style: TextStyle(color: p.grayFg, fontSize: 11.5, fontWeight: FontWeight.w600)),
      );

  void _importar(BuildContext context, AppState state) {
    final ctrl = TextEditingController();
    String? error;
    showDialog<void>(
      context: context,
      builder: (context) => StatefulBuilder(
        builder: (context, setLocal) => AlertDialog(
          title: const Text('Importar cuotas (Formato A)'),
          content: SizedBox(
            width: 560,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Pega el JSON que copiaste del navegador. Nada sale de este dispositivo.'),
                const SizedBox(height: 10),
                TextField(
                  controller: ctrl,
                  minLines: 8,
                  maxLines: 14,
                  style: mono.copyWith(fontSize: 12),
                  decoration: const InputDecoration(border: OutlineInputBorder(), isDense: true),
                ),
                if (error != null) ...[
                  const SizedBox(height: 8),
                  Text(error!, style: const TextStyle(color: Colors.red)),
                ],
              ],
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancelar')),
            FilledButton(
              onPressed: () {
                try {
                  state.importar(ctrl.text);
                  Navigator.pop(context);
                } on ErrorDatos catch (e) {
                  setLocal(() => error = e.mensaje);
                }
              },
              child: const Text('Importar'),
            ),
          ],
        ),
      ),
    );
  }
}
