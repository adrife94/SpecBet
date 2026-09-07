import 'package:decimal/decimal.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:betting_app/core/odds.dart';
import 'package:betting_app/core/promo.dart';

void main() {
  Decimal d(String s) => Decimal.parse(s);
  CuotaCasa casa(String n, String u, String x, String dos) =>
      CuotaCasa(n, {'1': d(u), 'X': d(x), '2': d(dos)});

  test('lista vacía => error', () {
    expect(() => construirFiltroPromo([]), throwsA(isA<ErrorDatos>()));
    expect(() => construirFiltroPromo(['  ']), throwsA(isA<ErrorDatos>()));
  });

  test('coste y windfall verificados: promo 2.00 vs ref 2.10, importe 50', () {
    final p = Partido('A vs B', null, [
      casa('Bet365', '2.00', '3.40', '3.50'),
      casa('Winamax', '2.10', '3.30', '3.60'),
    ]);
    final filtro = construirFiltroPromo(['Bet365']);
    final pata = posicionPromo(p, '1', filtro)!;
    expect(pata.casa, 'Bet365');
    expect(pata.casaReferencia, 'Winamax');
    expect(costePromo(pata, d('50')).toStringAsFixed(2), '5.00');
    expect(windfallPromo(pata, d('50')).toStringAsFixed(2), '100.00');
  });

  test('coste 0 cuando la mejor cuota ya es de la promo', () {
    final p = Partido('A vs B', null, [
      casa('Bet365', '2.15', '3.40', '3.50'),
      casa('Winamax', '2.10', '3.30', '3.60'),
    ]);
    final filtro = construirFiltroPromo(['Bet365']);
    final pata = posicionPromo(p, '1', filtro)!;
    expect(costePromo(pata, d('50')), d('0'));
  });

  test('tres opciones juntas con aviso de acumulación', () {
    final p = Partido('A vs B', null, [
      casa('Bet365', '2.00', '3.40', '3.50'),
      casa('Winamax', '2.10', '3.30', '3.60'),
    ]);
    final promo = opcionesPromo(p, construirFiltroPromo(['Bet365']));
    expect(promo.opciones.map((o) => o.nombre), ['asegurar_1', 'asegurar_2', 'asegurar_ambos']);
    expect(promo.avisos.any((a) => a.contains('acumul')), isTrue);
    // la X nunca se restringe.
    final rs = {for (final o in promo.opciones) for (final pa in o.patas) pa.resultado};
    expect(rs.contains('X'), isFalse);
  });

  test('pata no asegurable => null y cobertura excluye la casa del bono', () {
    final p = Partido('A vs B', null, [
      CuotaCasa('Bet365', {'1': null, 'X': d('3.40'), '2': d('3.50')}),
      casa('Winamax', '2.10', '3.30', '3.60'),
    ]);
    final filtro = construirFiltroPromo(['Bet365']);
    expect(posicionPromo(p, '1', filtro), isNull);
    // si la única casa de promo es la del bono, no hay cobertura de promo.
    expect(posicionPromoCobertura(p, '2', filtro, 'Bet365'), isNull);
  });
}
