import 'package:decimal/decimal.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:betting_app/core/odds.dart';
import 'package:betting_app/core/surebet.dart';

void main() {
  Decimal d(String s) => Decimal.parse(s);
  CuotaCasa casa(String n, String u, String x, String dos) =>
      CuotaCasa(n, {'1': d(u), 'X': d(x), '2': d(dos)});

  test('reparto surebet: retorno igual en las tres patas y beneficio positivo', () {
    final p = Partido('A vs B', null, [
      casa('A', '2.70', '3.60', '3.20'),
      casa('B', '2.60', '3.50', '3.10'),
    ]);
    final r = repartirPartido(p, d('100'));
    expect(r.noCalculable, isFalse);
    expect(r.surebet, isTrue);
    expect(r.beneficio! > d('0'), isTrue);

    // importe·cuota es el mismo en 1/X/2 (retorno igualado).
    String ret(String k) => (r.patas![k]!.importe * r.patas![k]!.cuota).toStringAsFixed(2);
    expect(ret('1'), ret('X'));
    expect(ret('X'), ret('2'));
    // los importes suman la inversión.
    final suma = r.patas!.values.fold(Decimal.fromInt(0), (a, l) => a + l.importe);
    expect(suma.toStringAsFixed(2), '100.00');
  });

  test('payout < 100 % => pérdida garantizada (no surebet)', () {
    final p = Partido('A vs B', null, [
      casa('A', '2.10', '3.40', '3.60'),
      casa('B', '2.05', '3.30', '3.55'),
    ]);
    final r = repartirPartido(p, d('200'));
    expect(r.surebet, isFalse);
    expect(r.beneficio! < d('0'), isTrue);
  });

  test('una sola casa => no calculable', () {
    final p = Partido('Solo', null, [casa('A', '2.70', '3.60', '3.20')]);
    expect(repartirPartido(p, d('100')).noCalculable, isTrue);
  });
}
