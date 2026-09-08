import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../core/money.dart';
import '../../core/odds.dart';
import '../../state/app_state.dart';
import '../theme.dart';
import '../widgets/form_bits.dart';

/// Prompt para pegar en el navegador de Claude (en la página de cuotas) y
/// obtener el JSON en Formato A que espera el importador.
const _promptCuotas = '''Estás viendo una página con cuotas de apuestas 1X2. Extrae TODOS los partidos visibles y devuélveme SOLO un JSON válido (sin texto alrededor, sin ```), con esta estructura exacta:

[
  {
    "partido": "Local vs Visitante",
    "fecha": "2026-09-12T21:00",
    "cuotas": [
      {"casa": "Bet365", "1": 2.35, "X": 3.15, "2": 3.50}
    ]
  }
]

Reglas:
- "1" = victoria local, "X" = empate, "2" = victoria visitante.
- Usa punto decimal (2.35, no 2,35). Si una cuota no aparece, pon null.
- Incluye todas las casas que veas para cada partido.
- No inventes cuotas: copia solo las que estén en la página.''';

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
        pieAviso(context),
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
    var copiado = false;
    showDialog<void>(
      context: context,
      builder: (context) {
        final p = Theme.of(context).extension<AppPalette>()!;
        return StatefulBuilder(
          builder: (context, setLocal) => AlertDialog(
          title: const Text('Importar cuotas'),
          content: SizedBox(
            width: 560,
            child: SingleChildScrollView(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text('1. Copia este prompt y pégalo en el navegador de Claude, en la página de cuotas:',
                      style: TextStyle(fontSize: 12.5, color: p.ink2)),
                  const SizedBox(height: 8),
                  Container(
                    width: double.infinity,
                    constraints: const BoxConstraints(maxHeight: 150),
                    decoration: BoxDecoration(
                      color: p.panel2,
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: p.line),
                    ),
                    padding: const EdgeInsets.all(10),
                    child: SingleChildScrollView(
                      child: SelectableText(_promptCuotas, style: mono.copyWith(fontSize: 11, height: 1.35)),
                    ),
                  ),
                  const SizedBox(height: 8),
                  Align(
                    alignment: Alignment.centerLeft,
                    child: OutlinedButton.icon(
                      onPressed: () async {
                        await Clipboard.setData(const ClipboardData(text: _promptCuotas));
                        setLocal(() => copiado = true);
                      },
                      icon: Icon(copiado ? Icons.check : Icons.copy, size: 16),
                      label: Text(copiado ? 'Copiado' : 'Copiar prompt'),
                    ),
                  ),
                  const SizedBox(height: 16),
                  Text('2. Pega aquí el JSON que te devuelva. Nada sale de este dispositivo.',
                      style: TextStyle(fontSize: 12.5, color: p.ink2)),
                  const SizedBox(height: 8),
                  TextField(
                    controller: ctrl,
                    minLines: 6,
                    maxLines: 12,
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
      );
      },
    );
  }
}
