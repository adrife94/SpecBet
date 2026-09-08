import 'package:decimal/decimal.dart';

import 'money.dart';
import 'odds.dart';
import 'promo.dart';

/// Apuesta de menor coste para cumplir el rollover de un bono. Port de
/// `core.calcular_opcion` / `_opciones_de_partido` / `evaluar_bonus` (sin plazo).

class CoberturaBonus {
  final String resultado;
  final Decimal importe;
  final Decimal cuota;
  final String casa;

  /// `true` si es una cobertura de ganar (1/2) reposicionada en una casa de la
  /// promo «ventaja de 2 goles» (RF-21).
  final bool promo;
  CoberturaBonus(this.resultado, this.importe, this.cuota, this.casa, {this.promo = false});
}

class OpcionBonus {
  final String partido;
  final String resultado; // resultado anclado en la casa del bono
  final Decimal importe;
  final Decimal cuota;
  final String casa;
  final List<CoberturaBonus> coberturas;
  final Decimal coste; // (bono + coberturas) − retorno
  OpcionBonus(this.partido, this.resultado, this.importe, this.cuota, this.casa,
      this.coberturas, this.coste);
}

List<OpcionBonus> _opcionesDePartido(
  Partido p, {
  required String casaBono,
  required Decimal importe,
  required Decimal cuotaMinima,
  FiltroPromo? promo,
}) {
  final entrada = p.casa(casaBono);
  if (entrada == null) return const [];
  final excl = {normalizar(casaBono)};
  final out = <OpcionBonus>[];
  for (final r in resultados) {
    final cuota = entrada[r];
    if (cuota == null || cuota < cuotaMinima) continue;
    final retorno = importe * cuota; // R
    final coberturas = <CoberturaBonus>[];
    var totalCob = cero;
    var cubrible = true;
    for (final otro in resultados) {
      if (otro == r) continue;
      // Con promo, la cobertura de una pata de ganar (1/2) va a la mejor casa de
      // la promo distinta de la del bono (RF-21); si no la cotiza, la normal.
      ({Decimal cuota, String casa})? cob;
      var esPromo = false;
      if (promo != null && (otro == '1' || otro == '2')) {
        final pos = posicionPromoCobertura(p, otro, promo, casaBono);
        if (pos != null) {
          cob = pos;
          esPromo = true;
        }
      }
      cob ??= mejorCuota(p, otro, excluir: excl);
      if (cob == null) {
        cubrible = false;
        break;
      }
      final stake = div(retorno, cob.cuota);
      totalCob += stake;
      coberturas.add(CoberturaBonus(otro, stake, cob.cuota, cob.casa, promo: esPromo));
    }
    if (!cubrible) continue;
    final coste = (importe + totalCob) - retorno;
    out.add(OpcionBonus(p.nombre, r, importe, cuota, entrada.casa, coberturas, coste));
  }
  return out;
}

/// Todas las opciones válidas de un bono en todos los partidos, ordenadas por
/// coste ascendente (las de coste negativo, arbitraje, primero).
List<OpcionBonus> opcionesBonus(
  List<Partido> partidos, {
  required String casaBono,
  required Decimal importe,
  required Decimal cuotaMinima,
  FiltroPromo? promo,
}) {
  final out = <OpcionBonus>[];
  for (final p in partidos) {
    out.addAll(_opcionesDePartido(p,
        casaBono: casaBono, importe: importe, cuotaMinima: cuotaMinima, promo: promo));
  }
  out.sort((a, b) => a.coste.compareTo(b.coste));
  return out;
}
