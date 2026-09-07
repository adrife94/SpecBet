import 'package:decimal/decimal.dart';

import 'money.dart';
import 'odds.dart';

/// Conversión de una freebet (stake no retornado). Port de
/// `core.calcular_jugada` / `mejor_jugada`.

class PataFreebet {
  final String tipo; // "gratis" | "cobertura"
  final String resultado;
  final Decimal importe;
  final Decimal cuota;
  final String casa;
  PataFreebet(this.tipo, this.resultado, this.importe, this.cuota, this.casa);
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
    final cob = mejorCuota(p, r, excluir: {normalizar(casaBono)});
    if (cob == null) return null; // no cubrible en casa distinta
    final stake = div(retorno, cob.cuota);
    invCobertura += stake;
    patas.add(PataFreebet('cobertura', r, stake, cob.cuota, cob.casa));
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
}) {
  final rs = resultadoFijo != null ? [resultadoFijo] : resultados;
  Jugada? mejor;
  for (final r in rs) {
    final j = _jugadaParaResultado(p, r,
        casaBono: casaBono, importe: importe, cuotaMin: cuotaMin, cuotaMax: cuotaMax);
    if (j == null) continue;
    if (mejor == null || j.valorExtraido > mejor.valorExtraido) mejor = j;
  }
  return mejor;
}

/// Evalúa la freebet en todos los partidos y ordena por valor extraído
/// descendente (la primera es la recomendada). Solo devuelve partidos jugables.
List<Jugada> freebetJugadas(
  List<Partido> partidos, {
  required String casaBono,
  required Decimal importe,
  Decimal? cuotaMin,
  Decimal? cuotaMax,
}) {
  final out = <Jugada>[];
  for (final p in partidos) {
    final j = mejorJugada(p, casaBono: casaBono, importe: importe, cuotaMin: cuotaMin, cuotaMax: cuotaMax);
    if (j != null) out.add(j);
  }
  out.sort((a, b) => b.valorExtraido.compareTo(a.valorExtraido));
  return out;
}
