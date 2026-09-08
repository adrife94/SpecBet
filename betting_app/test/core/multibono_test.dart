import 'package:decimal/decimal.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:betting_app/core/multibono.dart';
import 'package:betting_app/core/odds.dart';
import 'package:betting_app/core/promo.dart';

void main() {
  Decimal d(String s) => Decimal.parse(s);
  CuotaCasa casa(String n, String u, String x, String dos) =>
      CuotaCasa(n, {'1': d(u), 'X': d(x), '2': d(dos)});
  Bono bono(String n, String imp) => Bono(n, d(imp), d('1.01'));

  test('3 bonos 1.5/4/6 => R=600, real=350, pérdida=50, neto=250', () {
    final p = Partido('A vs B', null, [
      casa('Luckia', '1.5', '4', '6'),
      casa('Bet365', '1.5', '4', '6'),
      casa('Winamax', '1.5', '4', '6'),
      casa('Codere', '1.5', '4', '6'), // relleno (casa no de bono)
    ]);
    final op = evaluarMultibono([p], [bono('Luckia', '100'), bono('Bet365', '100'), bono('Winamax', '100')]).first;
    expect(op.retorno, d('600'));
    expect(op.dineroReal, d('350'));
    expect(op.perdida, d('50'));
    expect(op.neto, d('250'));
  });

  test('2 bonos: el tercer resultado se cubre solo con dinero real', () {
    final p = Partido('A vs B', null, [
      casa('Luckia', '3', '3', '3'),
      casa('Bet365', '3', '3', '3'),
      casa('Codere', '3', '3', '3'),
    ]);
    final op = evaluarMultibono([p], [bono('Luckia', '100'), bono('Bet365', '100')]).first;
    final bonos = op.patas.where((l) => l.tipo == 'bono').length;
    final rellenos = op.patas.where((l) => l.tipo == 'relleno').length;
    expect(bonos, 2);
    expect(rellenos, 1);
    expect(op.dineroReal, d('100')); // 300/3
    expect(op.perdida, d('0'));
  });

  test('falta una casa de bono => sin opción para ese partido', () {
    final p = Partido('A vs B', null, [
      casa('Luckia', '2', '3', '4'),
      casa('Bet365', '2', '3', '4'),
    ]);
    final ops = evaluarMultibono([p], [bono('Luckia', '100'), bono('Bet365', '100'), bono('Winamax', '100')]);
    expect(ops, isEmpty);
  });

  test('multibono con promo: el relleno de ganar (2) se coloca en la casa de la promo', () {
    // Los bonos no pueden anclar el 2 (1.5 < mín 2), así que el 2 es relleno.
    final p = Partido('A vs B', null, [
      casa('Luckia', '3', '3', '1.5'), // bono
      casa('Bet365', '3', '3', '1.5'), // bono
      casa('Winamax', '2', '2', '6'), // mejor 2 global (no bono)
      casa('Codere', '2', '2', '5'), // casa con promo (no bono)
    ]);
    final bonos = [Bono('Luckia', d('100'), d('2')), Bono('Bet365', d('100'), d('2'))];
    final op = evaluarMultibono([p], bonos, promo: construirFiltroPromo(['Codere'])).first;
    final r2 = op.patas.firstWhere((l) => l.resultado == '2');
    expect(r2.tipo, 'relleno');
    expect(r2.casa, 'Codere');
    expect(r2.promo, isTrue);
  });
}
