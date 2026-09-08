import 'package:decimal/decimal.dart';

import 'money.dart';
import 'odds.dart';
import 'promo.dart';

/// Conversión de una freebet (stake no retornado). Port de
/// `core.calcular_jugada` / `mejor_jugada`.

class PataFreebet {
  final String tipo; // "gratis" | "cobertura"
  final String resultado;
  final Decimal importe;
  final Decimal cuota;
  final String casa;

  /// `true` si es una cobertura de ganar (1/2) reposicionada en una casa de la
  /// promo «ventaja de 2 goles» (RF-20).
  final bool promo;
  PataFreebet(this.tipo, this.resultado, this.importe, this.cuota, this.casa, {this.promo = false});
}

class Jugada {
  final String partido;
  final String resultadoGratis;
  final List<PataFreebet> patas;
  final Decimal valorExtraido;
  final Decimal conversion; // fracción: valor / importe
  Jugada(this.partido, this.resultadoGratis, this.patas, this.valorExtraido, this.conversion);
}

Jugada? _jugadaParaResultado(
  Partido p,
  String resultadoGratis, {
  required String casaBono,
  required Decimal importe,
  Decimal? cuotaMin,
  Decimal? cuotaMax,
  FiltroPromo? promo,
}) {
  final entradaBono = p.casa(casaBono);
  if (entradaBono == null) return null;
  final cuotaGratis = entradaBono[resultadoGratis];
  if (cuotaGratis == null) return null;
  if (cuotaMin != null && cuotaGratis < cuotaMin) return null;
  if (cuotaMax != null && cuotaGratis > cuotaMax) return null;

  final retorno = importe * (cuotaGratis - uno); // R = F·(a−1)
  final patas = [PataFreebet('gratis', resultadoGratis, importe, cuotaGratis, entradaBono.casa)];
  var invCobertura = cero;
  for (final r in resultados) {
    if (r == resultadoGratis) continue;
    // Con promo, la cobertura de una pata de ganar (1/2) se coloca en la mejor
    // casa de la promo distinta de la del bono (RF-20); si no la cotiza, normal.
    ({Decimal cuota, String casa})? cob;
    var esPromo = false;
    if (promo != null && (r == '1' || r == '2')) {
      final pos = posicionPromoCobertura(p, r, promo, casaBono);
      if (pos != null) {
        cob = pos;
        esPromo = true;
      }
    }
    cob ??= mejorCuota(p, r, excluir: {normalizar(casaBono)});
    if (cob == null) return null; // no cubrible en casa distinta
    final stake = div(retorno, cob.cuota);
    invCobertura += stake;
    patas.add(PataFreebet('cobertura', r, stake, cob.cuota, cob.casa, promo: esPromo));
  }
  final valor = retorno - invCobertura;
  return Jugada(p.nombre, resultadoGratis, patas, valor, div(valor, importe));
}

/// Mejor jugada de una freebet en un partido (mayor valor extraído). Con
/// `resultadoFijo` solo prueba ese resultado. `null` si nada es viable.
Jugada? mejorJugada(
  Partido p, {
  required String casaBono,
  required Decimal importe,
  Decimal? cuotaMin,
  Decimal? cuotaMax,
  String? resultadoFijo,
  FiltroPromo? promo,
}) {
  final rs = resultadoFijo != null ? [resultadoFijo] : resultados;
  // El resultado gratis se elige sin promo (por valor base); luego, si hay
  // filtro, se recalcula esa jugada reposicionando las coberturas de ganar.
  Jugada? mejor;
  for (final r in rs) {
    final j = _jugadaParaResultado(p, r,
        casaBono: casaBono, importe: importe, cuotaMin: cuotaMin, cuotaMax: cuotaMax);
    if (j == null) continue;
    if (mejor == null || j.valorExtraido > mejor.valorExtraido) mejor = j;
  }
  if (mejor == null || promo == null) return mejor;
  return _jugadaParaResultado(p, mejor.resultadoGratis,
          casaBono: casaBono, importe: importe, cuotaMin: cuotaMin, cuotaMax: cuotaMax, promo: promo) ??
      mejor;
}

/// Evalúa la freebet en todos los partidos y ordena por valor extraído
/// descendente (la primera es la recomendada). Solo devuelve partidos jugables.
List<Jugada> freebetJugadas(
  List<Partido> partidos, {
  required String casaBono,
  required Decimal importe,
  Decimal? cuotaMin,
  Decimal? cuotaMax,
  FiltroPromo? promo,
}) {
  final out = <Jugada>[];
  for (final p in partidos) {
    final j = mejorJugada(p,
        casaBono: casaBono, importe: importe, cuotaMin: cuotaMin, cuotaMax: cuotaMax, promo: promo);
    if (j != null) out.add(j);
  }
  out.sort((a, b) => b.valorExtraido.compareTo(a.valorExtraido));
  return out;
}
