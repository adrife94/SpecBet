import 'package:decimal/decimal.dart';
import 'package:flutter/material.dart';

import '../../core/money.dart';
import '../../core/odds.dart';
import '../../core/promo.dart';
import '../../state/app_state.dart';
import '../theme.dart';
import 'form_bits.dart';

const _labels = {
  'asegurar_1': 'Asegurar 1',
  'asegurar_2': 'Asegurar 2',
  'asegurar_ambos': 'Asegurar ambos',
};

/// Panel del filtro de promo (ventaja de 2 goles). Se embebe al pie de cada
/// herramienta; si el filtro está apagado, no ocupa espacio. El coste y el
/// windfall se calculan sobre [importeRef] por pata.
class PromoPanel extends StatelessWidget {
  final Decimal importeRef;
  const PromoPanel({super.key, required this.importeRef});

  @override
  Widget build(BuildContext context) {
    final state = AppScope.of(context);
    if (!state.promoOn) return const SizedBox.shrink();
    final p = Theme.of(context).extension<AppPalette>()!;

    if (state.promoCasas.isEmpty) {
      return Padding(
        padding: const EdgeInsets.only(top: 16),
        child: avisoBox(context, 'Selecciona al menos una casa con promo en la barra lateral.'),
      );
    }

    final filtro = FiltroPromo(state.promoCasas.map(normalizar).toSet());
    final cards = <Widget>[];
    for (final partido in state.partidos) {
      final promo = opcionesPromo(partido, filtro);
      if (promo.opciones.isEmpty) continue;
      cards.add(_card(context, promo, p));
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const SizedBox(height: 22),
        Text('Filtro promo · ventaja de 2 goles',
            style: TextStyle(fontSize: 14, fontWeight: FontWeight.w700, color: p.ink)),
        Text('Coste y windfall sobre ${eur(importeRef)} por pata; se compara con la mejor cuota de referencia.',
            style: TextStyle(fontSize: 11.5, color: p.ink3)),
        const SizedBox(height: 10),
        if (cards.isEmpty)
          avisoBox(context, 'Ninguna casa de la promo cotiza patas de ganar en estos partidos.')
        else
          for (final c in cards) Padding(padding: const EdgeInsets.only(bottom: 12), child: c),
      ],
    );
  }

  Widget _card(BuildContext context, PromoPartido promo, AppPalette p) {
    return Container(
      decoration: BoxDecoration(
        color: p.panel,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: p.line),
      ),
      padding: const EdgeInsets.all(13),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(promo.partido, style: const TextStyle(fontSize: 13.5, fontWeight: FontWeight.w600)),
          const SizedBox(height: 10),
          Wrap(
            spacing: 10,
            runSpacing: 10,
            children: [for (final o in promo.opciones) _opcion(o, p)],
          ),
        ],
      ),
    );
  }

  Widget _opcion(OpcionPromo o, AppPalette p) {
    var coste = Decimal.fromInt(0);
    var windfall = Decimal.fromInt(0);
    for (final pata in o.patas) {
      coste += costePromo(pata, importeRef);
      windfall += windfallPromo(pata, importeRef);
    }
    final ambos = o.nombre == 'asegurar_ambos';
    return Container(
      width: 250,
      decoration: BoxDecoration(
        color: p.panel2,
        borderRadius: BorderRadius.circular(9),
        border: Border.all(color: p.line),
      ),
      padding: const EdgeInsets.all(11),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(_labels[o.nombre] ?? o.nombre, style: const TextStyle(fontSize: 12.5, fontWeight: FontWeight.w700)),
          const SizedBox(height: 7),
          for (final pata in o.patas)
            Padding(
              padding: const EdgeInsets.only(bottom: 4),
              child: Row(children: [
                _chip(pata.resultado, p),
                const SizedBox(width: 7),
                Expanded(
                  child: Text('${pata.casa} @${cuotaStr(pata.cuota)}  ·  ref ${pata.casaReferencia} ${cuotaStr(pata.cuotaReferencia)}',
                      style: TextStyle(fontSize: 11, color: p.ink2)),
                ),
              ]),
            ),
          const SizedBox(height: 6),
          Wrap(spacing: 6, runSpacing: 6, children: [
            _badge(p, 'Coste', eur(coste), 'amber'),
            _badge(p, 'Windfall', eur(windfall), 'green'),
          ]),
          if (ambos)
            Padding(
              padding: const EdgeInsets.only(top: 6),
              child: Text('Los dos windfalls pueden acumularse.', style: TextStyle(fontSize: 10.5, color: p.amberFg)),
            ),
        ],
      ),
    );
  }

  Widget _chip(String r, AppPalette p) => Container(
        width: 18,
        height: 18,
        alignment: Alignment.center,
        decoration: BoxDecoration(color: p.blueBg, borderRadius: BorderRadius.circular(5)),
        child: Text(r, style: TextStyle(color: p.blueFg, fontSize: 10, fontWeight: FontWeight.w700)),
      );

  Widget _badge(AppPalette p, String label, String value, String tono) {
    final (bg, fg) = p.tono(tono);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 4),
      decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(7)),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        Text(label, style: TextStyle(color: fg.withValues(alpha: 0.85), fontSize: 11, fontWeight: FontWeight.w500)),
        const SizedBox(width: 5),
        Text(value, style: mono.copyWith(color: fg, fontSize: 11, fontWeight: FontWeight.w600)),
      ]),
    );
  }
}
