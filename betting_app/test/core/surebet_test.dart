import 'package:decimal/decimal.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:betting_app/core/odds.dart';
import 'package:betting_app/core/promo.dart';
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

  test('con filtro promo, las patas 1 y 2 se colocan en la casa de la promo', () {
    // Winamax no es la mejor en 1 ni en 2, pero el filtro la fuerza ahí.
    final p = Partido('A vs B', null, [
      casa('SpeedyBet', '2.70', '3.60', '3.20'),
      casa('Winamax', '2.50', '3.55', '3.00'),
    ]);
    final filtro = construirFiltroPromo(['Winamax']);
    final r = repartirPartido(p, d('100'), promo: filtro);

    // 1 y 2 usan Winamax (reposicionadas); la X sigue en la mejor global.
    expect(r.patas!['1']!.casas, ['Winamax']);
    expect(r.patas!['1']!.cuota, d('2.50'));
    expect(r.patas!['1']!.promo, isTrue);
    expect(r.patas!['2']!.casas, ['Winamax']);
    expect(r.patas!['2']!.promo, isTrue);
    expect(r.patas!['X']!.promo, isFalse);
    expect(r.patas!['X']!.casas, ['SpeedyBet']);
  });

  test('sin casa de promo que cotice la pata, se deja su mejor cuota (RF-10)', () {
    final p = Partido('A vs B', null, [
      casa('SpeedyBet', '2.70', '3.60', '3.20'),
      CuotaCasa('Winamax', {'1': null, 'X': d('3.55'), '2': d('3.00')}),
    ]);
    final r = repartirPartido(p, d('100'), promo: construirFiltroPromo(['Winamax']));
    // Winamax no cotiza el 1 => se queda la mejor global, sin marca de promo.
    expect(r.patas!['1']!.casas, ['SpeedyBet']);
    expect(r.patas!['1']!.promo, isFalse);
    // el 2 sí se reposiciona.
    expect(r.patas!['2']!.casas, ['Winamax']);
    expect(r.patas!['2']!.promo, isTrue);
  });
}
