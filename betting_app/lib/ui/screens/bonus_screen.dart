import 'package:decimal/decimal.dart';
import 'package:flutter/material.dart';

import '../../core/bonus.dart';
import '../../core/money.dart';
import '../../state/app_state.dart';
import '../theme.dart';
import '../widgets/bet_slip.dart';
import '../widgets/form_bits.dart';

class BonusScreen extends StatefulWidget {
  const BonusScreen({super.key});
  @override
  State<BonusScreen> createState() => _BonusScreenState();
}

class _BonusScreenState extends State<BonusScreen> {
  String? casa;
  final importe = TextEditingController(text: '20');
  final minC = TextEditingController(text: '1.80');

  @override
  void dispose() {
    importe.dispose();
    minC.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = AppScope.of(context);
    final casas = state.casas;
    final sel = (casa != null && casas.contains(casa)) ? casa : (casas.isNotEmpty ? casas.first : null);

    final imp = parseDec(importe.text);
    final min = parseDec(minC.text);
    final valido = imp != null && imp > Decimal.fromInt(0) && min != null && min > Decimal.fromInt(1) && sel != null;
    final ops = valido
        ? opcionesBonus(state.partidos, casaBono: sel, importe: imp, cuotaMinima: min, promo: state.filtroPromo)
        : <OpcionBonus>[];

    return ListView(padding: const EdgeInsets.all(18), children: [
      screenTitle(context, 'Bono',
          'Cumple el rollover al menor coste: apuesta anclada en la casa del bono + coberturas.'),
      const SizedBox(height: 14),
      formCard(
        context,
        note: 'Anclar en cuota más alta cuesta más, pero es más probable que la apuesta pierda.',
        child: Wrap(spacing: 12, runSpacing: 12, children: [
          labeledField(context, 'Casa del bono', _casaDropdown(casas, sel, (v) => setState(() => casa = v))),
          labeledField(context, 'Importe (€)', _num(importe)),
          labeledField(context, 'Cuota mínima', _num(minC)),
        ]),
      ),
      const SizedBox(height: 14),
      if (!valido)
        avisoBox(context, 'Indica casa, importe > 0 y cuota mínima > 1.')
      else if (ops.isEmpty)
        avisoBox(context, 'No hay opciones válidas para este bono.')
      else
        for (var i = 0; i < ops.length; i++)
          Padding(padding: const EdgeInsets.only(bottom: 12), child: _slip(ops[i], i == 0)),
      pieAviso(context),
    ]);
  }

  Widget _slip(OpcionBonus o, bool destacada) {
    final desembolso = o.coberturas.fold(o.importe, (a, c) => a + c.importe);
    final legs = [
      SlipLeg(
        chip: o.resultado,
        chipTono: 'blue',
        icon: '💶',
        casa: o.casa,
        kind: 'apuesta anclada (requisito)',
        odds: cuotaStr(o.cuota),
        amount: eur(o.importe),
      ),
      for (final c in o.coberturas)
        SlipLeg(
          chip: c.resultado,
          chipTono: c.promo ? 'blue' : 'gray',
          icon: c.promo ? '🎯' : '💶',
          casa: c.casa,
          kind: c.promo ? 'cobertura promo · ventaja de 2 goles' : 'cobertura (dinero real)',
          odds: cuotaStr(c.cuota),
          amount: eur(c.importe),
        ),
    ]..sort(compararPorResultado);
    return BetSlip(
      title: o.partido,
      sub: 'Anclada al ${o.resultado} en ${o.casa}',
      destacada: destacada,
      destacadaTono: 'amber',
      badges: [
        SlipBadge(eur(o.coste), label: 'Coste', tono: o.coste <= Decimal.fromInt(0) ? 'green' : 'amber'),
        SlipBadge(eur(desembolso), label: 'Desembolso', tono: 'gray'),
      ],
      legs: legs,
      footer: 'Retorno igualado en cualquier resultado.',
    );
  }

  Widget _casaDropdown(List<String> casas, String? sel, ValueChanged<String?> onCh) => SizedBox(
        width: 170,
        child: DropdownButtonFormField<String>(
          initialValue: sel,
          isDense: true,
          isExpanded: true,
          decoration: denseInput,
          items: [for (final c in casas) DropdownMenuItem(value: c, child: Text(c))],
          onChanged: onCh,
        ),
      );

  Widget _num(TextEditingController c) => SizedBox(
        width: 130,
        child: TextField(
          controller: c,
          keyboardType: TextInputType.number,
          onChanged: (_) => setState(() {}),
          style: mono,
          decoration: denseInput,
        ),
      );
}
