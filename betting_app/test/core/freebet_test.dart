import 'package:decimal/decimal.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:betting_app/core/freebet.dart';
import 'package:betting_app/core/odds.dart';

void main() {
  Decimal d(String s) => Decimal.parse(s);
  CuotaCasa casa(String n, String u, String x, String dos) =>
      CuotaCasa(n, {'1': d(u), 'X': d(x), '2': d(dos)});

  test('mejor jugada verificada: pata gratis al 1 @3.60, valor 5.97', () {
    final p = Partido('M', null, [
      casa('Luckia', '3.60', '3.00', '2.00'), // casa del bono
      casa('Bet365', '3.50', '3.40', '2.05'), // mejor cobertura de la X (3.40)
      casa('Winamax', '3.55', '3.30', '2.10'), // mejor cobertura del 2 (2.10)
    ]);
    final j = mejorJugada(p, casaBono: 'Luckia', importe: d('10'))!;

    expect(j.resultadoGratis, '1');
    expect(j.valorExtraido.toStringAsFixed(2), '5.97');
    expect((j.conversion * Decimal.fromInt(100)).toStringAsFixed(2), '59.72');

    final gratis = j.patas.firstWhere((x) => x.tipo == 'gratis');
    expect(gratis.casa, 'Luckia');
    expect(gratis.cuota, d('3.60'));
    // las coberturas nunca van en la casa del bono.
    expect(j.patas.where((x) => x.tipo == 'cobertura').every((x) => x.casa != 'Luckia'), isTrue);
  });

  test('cuota máxima descarta la pata gratis de cuota alta', () {
    final p = Partido('M', null, [
      casa('Luckia', '3.60', '3.00', '2.00'),
      casa('Bet365', '3.50', '3.40', '2.05'),
      casa('Winamax', '3.55', '3.30', '2.10'),
    ]);
    // con máx 3.5, el "1" (3.60) ya no vale como pata gratis.
    final j = mejorJugada(p, casaBono: 'Luckia', importe: d('10'), cuotaMax: d('3.5'))!;
    expect(j.resultadoGratis == '1', isFalse);
  });
}
