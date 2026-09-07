import 'package:decimal/decimal.dart';

import 'compare.dart';
import 'money.dart';
import 'odds.dart';

/// Filtro de promo "ventaja de 2 goles". Port de `core` spec 005:
/// `FiltroPromo`, `posicion_promo`, `opciones_promo`, `coste_promo`,
/// `windfall_promo`, `posicion_promo_cobertura`, `payout_asegurado`.

class FiltroPromo {
  final Set<String> casas; // claves normalizadas
  FiltroPromo(this.casas);
}

FiltroPromo construirFiltroPromo(List<String> casas) {
  final n = casas.where((c) => c.trim().isNotEmpty).map(normalizar).toSet();
  if (n.isEmpty) throw ErrorDatos('El filtro de promo necesita al menos una casa.');
  return FiltroPromo(n);
}

class PataPromo {
  final String resultado;
  final String casa;
  final Decimal cuota;
  final String casaReferencia;
  final Decimal cuotaReferencia;
  PataPromo(this.resultado, this.casa, this.cuota, this.casaReferencia, this.cuotaReferencia);
}

class OpcionPromo {
  final String nombre; // "asegurar_1" | "asegurar_2" | "asegurar_ambos"
  final List<PataPromo> patas;
  OpcionPromo(this.nombre, this.patas);
}

class PromoPartido {
  final String partido;
  final List<OpcionPromo> opciones;
  final List<String> avisos;
  PromoPartido(this.partido, this.opciones, this.avisos);
}

/// Posiciona una pata de ganar (1 o 2): mejor cuota entre las casas de la promo
/// y mejor cuota de referencia (sin restricción). `null` si ninguna casa de la
/// promo la cotiza.
PataPromo? posicionPromo(Partido p, String resultado, FiltroPromo filtro) {
  final promo = mejorCuota(p, resultado, soloEn: filtro.casas);
  if (promo == null) return null;
  final ref = mejorCuota(p, resultado)!;
  return PataPromo(resultado, promo.casa, promo.cuota, ref.casa, ref.cuota);
}

/// Coste relativo en euros: importe·(referencia − promo). 0 si ya es la mejor.
Decimal costePromo(PataPromo pata, Decimal importe) =>
    importe * (pata.cuotaReferencia - pata.cuota);

/// Windfall en euros si salta la ventaja de 2 goles: importe·cuota.
Decimal windfallPromo(PataPromo pata, Decimal importe) => importe * pata.cuota;

/// Las tres opciones (asegurar 1 / 2 / ambos); la X nunca se restringe.
PromoPartido opcionesPromo(Partido p, FiltroPromo filtro) {
  final p1 = posicionPromo(p, '1', filtro);
  final p2 = posicionPromo(p, '2', filtro);
  final opciones = <OpcionPromo>[];
  final avisos = <String>[];
  if (p1 != null) {
    opciones.add(OpcionPromo('asegurar_1', [p1]));
  } else {
    avisos.add('Ninguna casa de la promo cotiza el resultado 1; no se puede asegurar esa pata.');
  }
  if (p2 != null) {
    opciones.add(OpcionPromo('asegurar_2', [p2]));
  } else {
    avisos.add('Ninguna casa de la promo cotiza el resultado 2; no se puede asegurar esa pata.');
  }
  if (p1 != null && p2 != null) {
    opciones.add(OpcionPromo('asegurar_ambos', [p1, p2]));
    avisos.add('Con ambas patas aseguradas, los dos windfalls pueden acumularse.');
  }
  return PromoPartido(p.nombre, opciones, avisos);
}

/// Mejor cuota de un resultado de ganar entre las casas de la promo, excluyendo
/// la del bono (constitución nº 10). Para coberturas en freebet/bonus.
({Decimal cuota, String casa})? posicionPromoCobertura(
    Partido p, String resultado, FiltroPromo filtro, String casaBono) {
  final casas = filtro.casas.difference({normalizar(casaBono)});
  if (casas.isEmpty) return null;
  return mejorCuota(p, resultado, soloEn: casas);
}

/// % de pago a partir de las cuotas 1/X/2.
Decimal payoutDeCuotas(Map<String, Decimal> cuotas) {
  var inversa = cero;
  for (final r in resultados) {
    inversa += div(uno, cuotas[r]!);
  }
  return div(cien, inversa);
}

/// % de pago sustituyendo las patas aseguradas por su cuota de promo. `null` si
/// el partido está incompleto.
Decimal? payoutAsegurado(Map<String, MejorCuota?> mejores, OpcionPromo opcion) {
  if (resultados.any((r) => mejores[r] == null)) return null;
  final cuotas = {for (final r in resultados) r: mejores[r]!.cuota};
  for (final pata in opcion.patas) {
    cuotas[pata.resultado] = pata.cuota;
  }
  return payoutDeCuotas(cuotas);
}
