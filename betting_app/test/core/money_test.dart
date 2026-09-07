import 'package:decimal/decimal.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:betting_app/core/money.dart';

void main() {
  Decimal d(String s) => Decimal.parse(s);

  test('div es exacto en decimales terminantes', () {
    expect(div(d('105'), d('2.10')), d('50'));
    expect(div(d('24'), d('3')), d('8'));
  });

  test('div mantiene precisión en no terminantes', () {
    // 100 / 3 ≈ 33.333... con precisión amplia (no double).
    final r = div(d('100'), d('3'));
    expect(r.toStringAsFixed(2), '33.33');
    expect(r > d('33.3333333'), isTrue);
  });

  test('formato de dinero en español (coma, €), ROUND_HALF_UP', () {
    expect(eur(d('172.5')), '172,50 €');
    expect(eur(d('6.275')), '6,28 €'); // half-up
    expect(eur(d('0')), '0,00 €');
  });

  test('formato de porcentaje y cuota', () {
    expect(pct(d('62.69')), '62,69 %');
    expect(cuotaStr(d('2.6')), '2.60'); // cuota con punto
    expect(cuotaStr(null), '—');
  });
}
