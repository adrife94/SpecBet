import 'package:decimal/decimal.dart';

import 'compare.dart';
import 'money.dart';
import 'odds.dart';

/// Reparto de una inversión entre 1/X/2 igualando el retorno (surebet).
/// Port de `core.repartir_partido` / `repartir`.

class PataReparto {
  final String resultado;
  final Decimal importe;
  final Decimal cuota;
  final List<String> casas;
  PataReparto(this.resultado, this.importe, this.cuota, this.casas);
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

Reparto repartirPartido(Partido p, Decimal inversion) {
  final mejores = mejoresDePartido(p);
  if (esIncompleto(p, mejores)) {
    return Reparto(p.nombre, true, false, payout(mejores), inversion, null, null, null);
  }
  var inversa = cero;
  for (final r in resultados) {
    inversa += div(uno, mejores[r]!.cuota);
  }
  final retorno = div(inversion, inversa);
  final patas = <String, PataReparto>{
    for (final r in resultados)
      r: PataReparto(r, div(retorno, mejores[r]!.cuota), mejores[r]!.cuota, mejores[r]!.casas),
  };
  final beneficio = retorno - inversion;
  return Reparto(p.nombre, false, beneficio > cero, payout(mejores), inversion, retorno, beneficio, patas);
}

/// Reparte en cada partido y ordena por beneficio descendente; los no
/// calculables al final en su orden de entrada.
List<Reparto> repartir(List<Partido> partidos, Decimal inversion) {
  final rs = partidos.map((p) => repartirPartido(p, inversion)).toList();
  final calc = rs.where((r) => !r.noCalculable).toList()
    ..sort((a, b) => b.beneficio!.compareTo(a.beneficio!));
  final noc = rs.where((r) => r.noCalculable).toList();
  return [...calc, ...noc];
}
