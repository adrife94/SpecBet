import 'package:decimal/decimal.dart';
import 'package:flutter/material.dart';

import '../../core/money.dart';
import '../../core/surebet.dart';
import '../../state/app_state.dart';
import '../theme.dart';
import '../widgets/bet_slip.dart';
import '../widgets/form_bits.dart';

class SurebetScreen extends StatefulWidget {
  const SurebetScreen({super.key});
  @override
  State<SurebetScreen> createState() => _SurebetScreenState();
}

class _SurebetScreenState extends State<SurebetScreen> {
  final invCtrl = TextEditingController(text: '200');

  @override
  void dispose() {
    invCtrl.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final state = AppScope.of(context);
    final filtro = state.filtroPromo;
    final inv = parseDec(invCtrl.text);
    final valido = inv != null && inv > Decimal.fromInt(0);
    final repartos = valido ? repartir(state.partidos, inv, promo: filtro) : <Reparto>[];

    return ListView(padding: const EdgeInsets.all(18), children: [
      screenTitle(context, 'Surebet',
          'Reparto de la inversión entre 1/X/2 con la mejor cuota de cada resultado.'),
      const SizedBox(height: 14),
      formCard(
        context,
        note: filtro != null
            ? 'Filtro promo activo: las patas de ganar (1 y 2) se colocan en tus casas con promo.'
            : 'El reparto iguala el retorno en los tres resultados.',
        child: labeledField(
          context,
          'Inversión (€)',
          SizedBox(
            width: 150,
            child: TextField(
              controller: invCtrl,
              keyboardType: TextInputType.number,
              onChanged: (_) => setState(() {}),
              style: mono,
              decoration: denseInput,
            ),
          ),
        ),
      ),
      const SizedBox(height: 14),
      if (!valido)
        avisoBox(context, 'Introduce una inversión mayor que 0.')
      else
        for (final r in repartos)
          Padding(
            padding: const EdgeInsets.only(bottom: 12),
            child: r.noCalculable
                ? _incompleto(context, r)
                : BetSlip(
                    title: r.nombre,
                    destacada: r.surebet,
                    destacadaTono: 'green',
                    badges: [
                      if (r.surebet) const SlipBadge('Surebet', tono: 'green'),
                      if (r.payout != null)
                        SlipBadge(pct(r.payout!), tono: r.surebet ? 'green' : 'red'),
                      SlipBadge('${r.surebet ? '+' : ''}${eur(r.beneficio!)}',
                          tono: r.surebet ? 'green' : 'red'),
                    ],
                    legs: [
                      for (final k in ['1', 'X', '2'])
                        SlipLeg(
                          chip: k,
                          chipTono: r.patas![k]!.promo ? 'blue' : 'gray',
                          icon: r.patas![k]!.promo ? '🎯' : null,
                          casa: r.patas![k]!.casas.join('/'),
                          kind: r.patas![k]!.promo ? 'promo · ventaja de 2 goles' : null,
                          odds: cuotaStr(r.patas![k]!.cuota),
                          amount: eur(r.patas![k]!.importe),
                        ),
                    ],
                    footer: _footer(r),
                  ),
          ),
      pieAviso(context),
    ]);
  }

  /// Pie del boleto: retorno y, si hay patas reposicionadas por promo, el
  /// windfall (cada pata asegurada devuelve su importe × cuota = el retorno).
  String _footer(Reparto r) {
    final base = 'Retorno ${eur(r.retorno!)}';
    final hayPromo = r.patas!.values.any((pa) => pa.promo);
    if (!hayPromo) return base;
    return '$base · si salta la promo, +${eur(r.retorno!)} extra por cada pata asegurada';
  }

  Widget _incompleto(BuildContext context, Reparto r) {
    final p = Theme.of(context).extension<AppPalette>()!;
    return Container(
      decoration: BoxDecoration(
        color: p.panel,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: p.line),
      ),
      padding: const EdgeInsets.all(14),
      child: Row(children: [
        Expanded(child: Text(r.nombre, style: const TextStyle(fontWeight: FontWeight.w600))),
        Text('Incompleto (faltan cuotas)', style: TextStyle(color: p.ink3, fontSize: 12)),
      ]),
    );
  }
}
