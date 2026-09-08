import 'package:decimal/decimal.dart';
import 'package:flutter/material.dart';

import '../../core/freebet.dart';
import '../../core/money.dart';
import '../../state/app_state.dart';
import '../theme.dart';
import '../widgets/bet_slip.dart';
import '../widgets/form_bits.dart';

class FreebetScreen extends StatefulWidget {
  const FreebetScreen({super.key});
  @override
  State<FreebetScreen> createState() => _FreebetScreenState();
}

class _FreebetScreenState extends State<FreebetScreen> {
  String? casa;
  final importe = TextEditingController(text: '10');
  final minC = TextEditingController(text: '1.50');
  final maxC = TextEditingController(text: '5.00');

  @override
  void dispose() {
    importe.dispose();
    minC.dispose();
    maxC.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = AppScope.of(context);
    final casas = state.casas;
    final sel = (casa != null && casas.contains(casa)) ? casa : (casas.isNotEmpty ? casas.first : null);

    final F = parseDec(importe.text);
    final valido = F != null && F > Decimal.fromInt(0) && sel != null;
    final jugadas = valido
        ? freebetJugadas(state.partidos,
            casaBono: sel,
            importe: F,
            cuotaMin: parseDec(minC.text),
            cuotaMax: parseDec(maxC.text),
            promo: state.filtroPromo)
        : <Jugada>[];

    return ListView(padding: const EdgeInsets.all(18), children: [
      screenTitle(context, 'Freebet',
          'Convierte una apuesta gratis: la apuesta del bono + dos coberturas igualadas.'),
      const SizedBox(height: 14),
      formCard(
        context,
        note: 'La apuesta del bono no devuelve el importe: solo cuenta la ganancia.',
        child: Wrap(spacing: 12, runSpacing: 12, children: [
          labeledField(context, 'Casa del bono', _casaDropdown(casas, sel, (v) => setState(() => casa = v))),
          labeledField(context, 'Importe (€)', _num(importe)),
          labeledField(context, 'Cuota mínima', _num(minC)),
          labeledField(context, 'Cuota máxima', _num(maxC)),
        ]),
      ),
      const SizedBox(height: 14),
      if (!valido)
        avisoBox(context, 'Indica una casa y un importe mayor que 0.')
      else if (jugadas.isEmpty)
        avisoBox(context, 'No hay jugadas viables con esos parámetros.')
      else
        for (var i = 0; i < jugadas.length; i++)
          Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: _slip(jugadas[i], i == 0),
          ),
      pieAviso(context),
    ]);
  }

  Widget _slip(Jugada j, bool destacada) {
    final legs = [
      for (final pa in j.patas)
        SlipLeg(
          chip: pa.resultado,
          chipTono: pa.tipo == 'gratis' || pa.promo ? 'blue' : 'gray',
          icon: pa.tipo == 'gratis' ? '🎟' : (pa.promo ? '🎯' : '💶'),
          casa: pa.casa,
          kind: pa.tipo == 'gratis'
              ? 'Apuesta del bono (gratis)'
              : (pa.promo ? 'cobertura promo · ventaja de 2 goles' : 'Cobertura (dinero real)'),
          odds: cuotaStr(pa.cuota),
          amount: eur(pa.importe),
        ),
    ]..sort(compararPorResultado);
    return BetSlip(
      title: j.partido,
      sub: 'Gratis al ${j.resultadoGratis} en ${j.patas.first.casa}',
      destacada: destacada,
      destacadaTono: 'green',
      badges: [
        SlipBadge(eur(j.valorExtraido), label: 'Valor', tono: 'green'),
        SlipBadge(pct(j.conversion * Decimal.fromInt(100)),
            label: 'Conversión', tono: j.conversion >= Decimal.parse('0.6') ? 'green' : 'amber'),
      ],
      legs: legs,
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
