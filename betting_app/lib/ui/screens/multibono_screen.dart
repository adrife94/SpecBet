import 'package:decimal/decimal.dart';
import 'package:flutter/material.dart';

import '../../core/money.dart';
import '../../core/multibono.dart';
import '../../core/odds.dart';
import '../../state/app_state.dart';
import '../theme.dart';
import '../widgets/bet_slip.dart';
import '../widgets/form_bits.dart';

class MultibonoScreen extends StatefulWidget {
  const MultibonoScreen({super.key});
  @override
  State<MultibonoScreen> createState() => _MultibonoScreenState();
}

class _MultibonoScreenState extends State<MultibonoScreen> {
  int count = 3;
  final List<String?> casaSel = ['Winamax', 'YoSports', 'Codere'];
  final imp = List.generate(3, (_) => TextEditingController(text: '100'));
  final minC = List.generate(3, (_) => TextEditingController(text: '1.50'));

  @override
  void dispose() {
    for (final c in [...imp, ...minC]) {
      c.dispose();
    }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = AppScope.of(context);
    final casas = state.casas;

    final bonos = <Bono>[];
    var valido = true;
    for (var i = 0; i < count; i++) {
      final sel = (casaSel[i] != null && casas.contains(casaSel[i])) ? casaSel[i] : (casas.isNotEmpty ? casas.first : null);
      final a = parseDec(imp[i].text);
      final m = parseDec(minC[i].text);
      if (sel == null || a == null || a <= Decimal.fromInt(0) || m == null || m <= Decimal.fromInt(1)) {
        valido = false;
        break;
      }
      bonos.add(Bono(sel, a, m));
    }
    // casas de bono distintas entre sí
    if (valido && bonos.map((b) => normalizar(b.casa)).toSet().length != bonos.length) {
      valido = false;
    }
    final ops = valido ? evaluarMultibono(state.partidos, bonos, promo: state.filtroPromo) : <OpcionMulti>[];

    return ListView(padding: const EdgeInsets.all(18), children: [
      screenTitle(context, 'Multibono',
          'Reparte 2 o 3 bonos entre los resultados de un partido; el relleno va con dinero real.'),
      const SizedBox(height: 14),
      formCard(
        context,
        note: 'Cada bono en una casa distinta. Se elige la asignación de menor pérdida.',
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            labeledField(
              context,
              'Nº de bonos',
              SizedBox(
                width: 90,
                child: DropdownButtonFormField<int>(
                  initialValue: count,
                  isDense: true,
                  isExpanded: true,
                  decoration: denseInput,
                  items: const [DropdownMenuItem(value: 2, child: Text('2')), DropdownMenuItem(value: 3, child: Text('3'))],
                  onChanged: (v) => setState(() => count = v ?? 3),
                ),
              ),
            ),
            const SizedBox(height: 12),
            for (var i = 0; i < count; i++)
              Padding(
                padding: const EdgeInsets.only(bottom: 10),
                child: Wrap(spacing: 12, runSpacing: 8, crossAxisAlignment: WrapCrossAlignment.end, children: [
                  labeledField(context, 'Bono ${i + 1} · casa',
                      _casaDropdown(casas, casaSel[i], (v) => setState(() => casaSel[i] = v))),
                  labeledField(context, 'Importe (€)', _num(imp[i])),
                  labeledField(context, 'Cuota mín.', _num(minC[i])),
                ]),
              ),
          ],
        ),
      ),
      const SizedBox(height: 14),
      if (!valido)
        avisoBox(context, 'Rellena 2–3 bonos en casas distintas, con importe > 0 y cuota mínima > 1.')
      else if (ops.isEmpty)
        avisoBox(context, 'Ningún partido admite una asignación válida.')
      else
        for (var i = 0; i < ops.length; i++)
          Padding(padding: const EdgeInsets.only(bottom: 12), child: _slip(ops[i], i == 0)),
      pieAviso(context),
    ]);
  }

  Widget _slip(OpcionMulti o, bool destacada) => BetSlip(
        title: o.partido,
        sub: '${o.patas.length} apuestas',
        destacada: destacada,
        destacadaTono: 'blue',
        badges: [
          SlipBadge(eur(o.perdida), label: 'Pérdida', tono: 'red'),
          SlipBadge(pct(o.perdidaPct), label: '%', tono: 'red'),
          SlipBadge(eur(o.dineroReal), label: 'Real', tono: o.dineroReal > Decimal.fromInt(0) ? 'amber' : 'green'),
          SlipBadge(eur(o.neto), label: 'Neto', tono: 'green'),
        ],
        legs: [
          for (final l in o.patas)
            SlipLeg(
              chip: l.resultado,
              chipTono: l.tipo == 'bono' || l.promo ? 'blue' : 'gray',
              icon: l.tipo == 'bono' ? '🎟' : (l.promo ? '🎯' : '💶'),
              casa: l.casa,
              kind: l.tipo == 'bono'
                  ? 'bono'
                  : (l.promo ? 'relleno promo · ventaja de 2 goles' : 'relleno (dinero real)'),
              odds: cuotaStr(l.cuota),
              amount: eur(l.importe),
            ),
        ],
        footer: 'Retorno mínimo ${eur(o.retorno)} en cualquier resultado.',
      );

  Widget _casaDropdown(List<String> casas, String? sel, ValueChanged<String?> onCh) {
    final v = (sel != null && casas.contains(sel)) ? sel : (casas.isNotEmpty ? casas.first : null);
    return SizedBox(
      width: 150,
      child: DropdownButtonFormField<String>(
        initialValue: v,
        isDense: true,
        isExpanded: true,
        decoration: denseInput,
        items: [for (final c in casas) DropdownMenuItem(value: c, child: Text(c))],
        onChanged: onCh,
      ),
    );
  }

  Widget _num(TextEditingController c) => SizedBox(
        width: 110,
        child: TextField(
          controller: c,
          keyboardType: TextInputType.number,
          onChanged: (_) => setState(() {}),
          style: mono,
          decoration: denseInput,
        ),
      );
}
