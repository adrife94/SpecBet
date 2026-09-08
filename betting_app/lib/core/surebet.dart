import 'package:decimal/decimal.dart';

import 'compare.dart';
import 'money.dart';
import 'odds.dart';
import 'promo.dart';

/// Reparto de una inversión entre 1/X/2 igualando el retorno (surebet).
/// Port de `core.repartir_partido` / `repartir`.

class PataReparto {
  final String resultado;
  final Decimal importe;
  final Decimal cuota;
  final List<String> casas;

  /// `true` si esta pata de ganar se reposicionó en una casa de la promo
  /// (filtro «ventaja de 2 goles»), en vez de su mejor cuota global.
  final bool promo;
  PataReparto(this.resultado, this.importe, this.cuota, this.casas, {this.promo = false});
}

class Reparto {
  final String nombre;
  final bool noCalculable;
  final bool surebet;
  final Decimal? payout;
  final Decimal inversion;
  final Decimal? retorno;
  final Decimal? beneficio;
  final Map<String, PataReparto>? patas;
  Reparto(this.nombre, this.noCalculable, this.surebet, this.payout, this.inversion,
      this.retorno, this.beneficio, this.patas);
}

/// Reparte la inversión igualando el retorno. Si [promo] no es `null`, las patas
/// de ganar (1 y 2) se cogen de la mejor casa de la promo (RF-6/RF-8/RF-19); si
/// ninguna casa de la promo cotiza una de ellas, se deja su mejor cuota normal
/// (RF-10). La X nunca se restringe (RF-7).
Reparto repartirPartido(Partido p, Decimal inversion, {FiltroPromo? promo}) {
  final mejores = mejoresDePartido(p);
  if (esIncompleto(p, mejores)) {
    return Reparto(p.nombre, true, false, payout(mejores), inversion, null, null, null);
  }
  // Cuota efectiva por resultado: con promo, 1 y 2 se posicionan en su casa.
  final efectivas = <String, MejorCuota>{for (final r in resultados) r: mejores[r]!};
  final reposicionadas = <String>{};
  if (promo != null) {
    for (final r in const ['1', '2']) {
      final pos = mejorCuota(p, r, soloEn: promo.casas);
      if (pos != null) {
        efectivas[r] = MejorCuota(pos.cuota, [pos.casa]);
        reposicionadas.add(r);
      }
    }
  }
  var inversa = cero;
  for (final r in resultados) {
    inversa += div(uno, efectivas[r]!.cuota);
  }
  final retorno = div(inversion, inversa);
  final patas = <String, PataReparto>{
    for (final r in resultados)
      r: PataReparto(r, div(retorno, efectivas[r]!.cuota), efectivas[r]!.cuota, efectivas[r]!.casas,
          promo: reposicionadas.contains(r)),
  };
  final beneficio = retorno - inversion;
  return Reparto(p.nombre, false, beneficio > cero, payout(efectivas), inversion, retorno, beneficio, patas);
}

/// Reparte en cada partido y ordena por beneficio descendente; los no
/// calculables al final en su orden de entrada. [promo] se propaga a cada partido.
List<Reparto> repartir(List<Partido> partidos, Decimal inversion, {FiltroPromo? promo}) {
  final rs = partidos.map((p) => repartirPartido(p, inversion, promo: promo)).toList();
  final calc = rs.where((r) => !r.noCalculable).toList()
    ..sort((a, b) => b.beneficio!.compareTo(a.beneficio!));
  final noc = rs.where((r) => r.noCalculable).toList();
  return [...calc, ...noc];
}
