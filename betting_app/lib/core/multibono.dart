import 'package:decimal/decimal.dart';

import 'money.dart';
import 'odds.dart';

/// Rollover coordinado de 2–3 bonos. Port de `core.calcular_opcion_multi` /
/// `_opcion_de_partido_multi` / `evaluar_multibono` (sin plazo por ahora).

class Bono {
  final String casa;
  final Decimal importe;
  final Decimal cuotaMinima;
  Bono(this.casa, this.importe, this.cuotaMinima);
}

class PataMulti {
  final String tipo; // "bono" | "relleno"
  final String resultado;
  final Decimal importe;
  final Decimal cuota;
  final String casa;
  PataMulti(this.tipo, this.resultado, this.importe, this.cuota, this.casa);
}

class OpcionMulti {
  final String partido;
  final Decimal retorno; // techo R
  final List<PataMulti> patas;
  final Decimal dineroReal;
  final Decimal perdida;
  final Decimal perdidaPct;
  final Decimal neto;
  OpcionMulti(this.partido, this.retorno, this.patas, this.dineroReal, this.perdida,
      this.perdidaPct, this.neto);
}

typedef Anclado = ({Bono bono, Decimal cuota});

List<List<int>> _perms(List<int> items, int k) {
  if (k == 0) return [<int>[]];
  final out = <List<int>>[];
  for (var i = 0; i < items.length; i++) {
    final rest = [...items]..removeAt(i);
    for (final p in _perms(rest, k - 1)) {
      out.add([items[i], ...p]);
    }
  }
  return out;
}

OpcionMulti calcularOpcionMulti(
  String partido,
  Map<String, Anclado?> asignacion,
  Map<String, ({Decimal cuota, String casa})> rellenos,
) {
  final anclados = asignacion.values.whereType<Anclado>();
  final retorno = anclados.map((a) => a.bono.importe * a.cuota).reduce((x, y) => y > x ? y : x);

  final patas = <PataMulti>[];
  var dineroReal = cero;
  var totalBono = cero;
  for (final r in resultados) {
    final anclado = asignacion[r];
    Decimal falta;
    if (anclado != null) {
      totalBono += anclado.bono.importe;
      patas.add(PataMulti('bono', r, anclado.bono.importe, anclado.cuota, anclado.bono.casa));
      falta = retorno - anclado.bono.importe * anclado.cuota;
    } else {
      falta = retorno; // resultado sin bono: cobertura entera
    }
    if (falta > cero) {
      final rel = rellenos[r]!;
      final stake = div(falta, rel.cuota);
      dineroReal += stake;
      patas.add(PataMulti('relleno', r, stake, rel.cuota, rel.casa));
    }
  }

  final total = totalBono + dineroReal;
  final perdida = total - retorno;
  return OpcionMulti(
      partido, retorno, patas, dineroReal, perdida, div(perdida, totalBono) * cien, retorno - dineroReal);
}

/// Mejor opción (menor pérdida) de un partido, o `null` si ninguna asignación es
/// válida (falta una casa de bono, cuota bajo la mínima o resultado no rellenable).
OpcionMulti? opcionDePartidoMulti(Partido p, List<Bono> bonos) {
  final casasBono = bonos.map((b) => normalizar(b.casa)).toSet();
  for (final b in bonos) {
    if (p.casa(b.casa) == null) return null;
  }

  OpcionMulti? mejor;
  for (final perm in _perms([0, 1, 2], bonos.length)) {
    final asignacion = <String, Anclado?>{for (final r in resultados) r: null};
    var valida = true;
    for (var i = 0; i < bonos.length; i++) {
      final b = bonos[i];
      final r = resultados[perm[i]];
      final cuota = p.casa(b.casa)![r];
      if (cuota == null || cuota < b.cuotaMinima) {
        valida = false;
        break;
      }
      asignacion[r] = (bono: b, cuota: cuota);
    }
    if (!valida) continue;

    final retorno = asignacion.values
        .whereType<Anclado>()
        .map((a) => a.bono.importe * a.cuota)
        .reduce((x, y) => y > x ? y : x);
    final rellenos = <String, ({Decimal cuota, String casa})>{};
    var cubrible = true;
    for (final r in resultados) {
      final anclado = asignacion[r];
      final falta = anclado == null ? retorno : retorno - anclado.bono.importe * anclado.cuota;
      if (falta > cero) {
        final cob = mejorCuota(p, r, excluir: casasBono);
        if (cob == null) {
          cubrible = false;
          break;
        }
        rellenos[r] = cob;
      }
    }
    if (!cubrible) continue;

    final op = calcularOpcionMulti(p.nombre, asignacion, rellenos);
    if (mejor == null || op.perdida < mejor.perdida) mejor = op;
  }
  return mejor;
}

/// Mejor opción por partido, ordenadas por pérdida ascendente.
List<OpcionMulti> evaluarMultibono(List<Partido> partidos, List<Bono> bonos) {
  final out = <OpcionMulti>[];
  for (final p in partidos) {
    final op = opcionDePartidoMulti(p, bonos);
    if (op != null) out.add(op);
  }
  out.sort((a, b) => a.perdida.compareTo(b.perdida));
  return out;
}
