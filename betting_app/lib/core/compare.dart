import 'package:decimal/decimal.dart';

import 'money.dart';
import 'odds.dart';

/// Comparador de cuotas / % de pago. Port de `core.mejores_de_partido`,
/// `es_incompleto` y `calcular_payout`.

/// La mejor cuota de un resultado y todas las casas que la igualan.
class MejorCuota {
  final Decimal cuota;
  final List<String> casas;
  MejorCuota(this.cuota, this.casas);
}

/// Mejor cuota de cada resultado 1/X/2 entre las casas del partido. Ante empate,
/// las casas se listan en su orden de entrada. `null` si ningún dato válido.
Map<String, MejorCuota?> mejoresDePartido(Partido p) {
  final res = <String, MejorCuota?>{};
  for (final r in resultados) {
    Decimal? tope;
    final casas = <String>[];
    for (final c in p.casas) {
      final v = c[r];
      if (v == null) continue;
      if (tope == null || v > tope) {
        tope = v;
        casas
          ..clear()
          ..add(c.casa);
      } else if (v == tope) {
        casas.add(c.casa);
      }
    }
    res[r] = tope == null ? null : MejorCuota(tope, List.unmodifiable(casas));
  }
  return res;
}

/// Un partido es incompleto si a algún resultado le falta cuota válida en toda
/// casa, o si menos de dos casas distintas aportan alguna cuota válida.
bool esIncompleto(Partido p, Map<String, MejorCuota?> mejores) {
  if (resultados.any((r) => mejores[r] == null)) return true;
  final casas = <String>{};
  for (final c in p.casas) {
    if (resultados.any((r) => c[r] != null)) casas.add(normalizar(c.casa));
  }
  return casas.length < 2;
}

/// % de pago = 100 / (1/mejor_1 + 1/mejor_X + 1/mejor_2). Sin redondear.
/// `null` si falta la mejor cuota de algún resultado.
Decimal? payout(Map<String, MejorCuota?> mejores) {
  if (resultados.any((r) => mejores[r] == null)) return null;
  var inversa = cero;
  for (final r in resultados) {
    inversa += div(uno, mejores[r]!.cuota);
  }
  return div(cien, inversa);
}

/// Un partido evaluado por el comparador.
class PartidoEvaluado {
  final String nombre;
  final String? fecha;
  final Map<String, MejorCuota?> mejores;
  final bool incompleto;
  final Decimal? payout;
  PartidoEvaluado(this.nombre, this.fecha, this.mejores, this.incompleto, this.payout);
}

PartidoEvaluado evaluarPartido(Partido p) {
  final mejores = mejoresDePartido(p);
  final incompleto = esIncompleto(p, mejores);
  return PartidoEvaluado(p.nombre, p.fecha, mejores, incompleto, incompleto ? null : payout(mejores));
}

/// Evalúa todos los partidos y los ordena: completos por % de pago descendente
/// (estable), incompletos al final en su orden de entrada.
List<PartidoEvaluado> comparar(List<Partido> partidos) {
  final evaluados = partidos.map(evaluarPartido).toList();
  final completos = evaluados.where((e) => !e.incompleto).toList()
    ..sort((a, b) => b.payout!.compareTo(a.payout!));
  final incompletos = evaluados.where((e) => e.incompleto).toList();
  return [...completos, ...incompletos];
}
