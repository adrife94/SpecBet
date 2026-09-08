import 'package:decimal/decimal.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:betting_app/core/bonus.dart';
import 'package:betting_app/core/odds.dart';
import 'package:betting_app/core/promo.dart';

void main() {
  Decimal d(String s) => Decimal.parse(s);
  CuotaCasa casa(String n, String u, String x, String dos) =>
      CuotaCasa(n, {'1': d(u), 'X': d(x), '2': d(dos)});

  test('coste verificado: anclar 100 @2.10, cubrir 4.20 y 3.60 => -1.67 (arbitraje)', () {
    final p = Partido('A vs B', null, [
      casa('Luckia', '2.10', '3.00', '3.00'), // casa del bono
      casa('Bet365', '2.05', '4.20', '3.50'), // mejor cobertura X (4.20)
      casa('Winamax', '2.00', '3.90', '3.60'), // mejor cobertura 2 (3.60)
    ]);
    final ops = opcionesBonus([p], casaBono: 'Luckia', importe: d('100'), cuotaMinima: d('1.5'));
    final op1 = ops.firstWhere((o) => o.resultado == '1');
    expect(op1.coste.toStringAsFixed(2), '-1.67');
    // coberturas en casa distinta a la del bono.
    expect(op1.coberturas.every((c) => c.casa != 'Luckia'), isTrue);
    // ordenadas por coste ascendente (la más barata primero).
    for (var i = 1; i < ops.length; i++) {
      expect(ops[i - 1].coste <= ops[i].coste, isTrue);
    }
  });

  test('resultado bajo la cuota mínima no genera opción', () {
    final p = Partido('A vs B', null, [
      casa('Luckia', '1.30', '3.00', '3.00'),
      casa('Bet365', '2.05', '4.20', '3.50'),
      casa('Winamax', '2.00', '3.90', '3.60'),
    ]);
    final ops = opcionesBonus([p], casaBono: 'Luckia', importe: d('100'), cuotaMinima: d('1.5'));
    expect(ops.any((o) => o.resultado == '1'), isFalse); // 1.30 < 1.5
  });

  test('bonus con promo: la cobertura de ganar (2) se coloca en la casa de la promo', () {
    final p = Partido('A vs B', null, [
      casa('Luckia', '2.10', '3.00', '3.00'), // casa del bono
      casa('Bet365', '2.05', '4.20', '3.50'), // mejor cobertura X
      casa('Winamax', '2.00', '3.90', '3.60'), // mejor cobertura 2 global
      casa('Codere', '2.00', '3.20', '3.40'), // casa con promo
    ]);
    final ops = opcionesBonus([p],
        casaBono: 'Luckia', importe: d('100'), cuotaMinima: d('1.5'), promo: construirFiltroPromo(['Codere']));
    final op1 = ops.firstWhere((o) => o.resultado == '1'); // ancla el 1, cubre X y 2
    final cob2 = op1.coberturas.firstWhere((c) => c.resultado == '2');
    expect(cob2.casa, 'Codere');
    expect(cob2.promo, isTrue);
    // la X no se restringe.
    expect(op1.coberturas.firstWhere((c) => c.resultado == 'X').promo, isFalse);
  });
}
