import 'package:decimal/decimal.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:betting_app/core/compare.dart';
import 'package:betting_app/core/odds.dart';

void main() {
  Decimal d(String s) => Decimal.parse(s);

  CuotaCasa casa(String n, String uno, String x, String dos) =>
      CuotaCasa(n, {'1': d(uno), 'X': d(x), '2': d(dos)});

  test('payout verificado a mano: 2.10 / 3.40 / 3.60 = 95.41 %', () {
    final p = Partido('A vs B', null, [
      casa('Bet365', '2.10', '3.40', '3.60'),
      casa('Winamax', '2.05', '3.30', '3.55'),
    ]);
    final mejores = mejoresDePartido(p);
    expect(mejores['1']!.cuota, d('2.10'));
    expect(mejores['X']!.cuota, d('3.40'));
    expect(mejores['2']!.cuota, d('3.60'));
    expect(payout(mejores)!.toStringAsFixed(2), '95.41');
  });

  test('mejor cuota con empate lista todas las casas en orden', () {
    final p = Partido('A vs B', null, [
      casa('Bet365', '2.10', '3.40', '3.60'),
      casa('Winamax', '2.10', '3.30', '3.55'),
    ]);
    final mejores = mejoresDePartido(p);
    expect(mejores['1']!.cuota, d('2.10'));
    expect(mejores['1']!.casas, ['Bet365', 'Winamax']);
  });

  test('cuota <= 1 es hueco; resultado sin cuota válida -> incompleto', () {
    final p = Partido('A vs B', null, [
      CuotaCasa('Bet365', {'1': d('2.10'), 'X': cuotaValida(1), '2': d('3.60')}),
      CuotaCasa('Winamax', {'1': d('2.05'), 'X': null, '2': d('3.55')}),
    ]);
    final mejores = mejoresDePartido(p);
    expect(mejores['X'], isNull);
    expect(esIncompleto(p, mejores), isTrue);
    expect(payout(mejores), isNull);
  });

  test('menos de dos casas -> incompleto', () {
    final p = Partido('Solo', null, [casa('Bet365', '2.10', '3.40', '3.60')]);
    expect(esIncompleto(p, mejoresDePartido(p)), isTrue);
  });

  test('comparar ordena por payout desc y deja incompletos al final', () {
    final partidos = [
      Partido('Incompleto', null, [casa('Bet365', '2.10', '3.40', '3.60')]),
      Partido('Bajo', null, [casa('A', '2.60', '2.60', '2.60'), casa('B', '2.55', '2.55', '2.55')]),
      Partido('Alto', null, [casa('A', '2.95', '3.10', '3.00'), casa('B', '2.90', '3.05', '2.95')]),
    ];
    final orden = comparar(partidos).map((e) => e.nombre).toList();
    expect(orden, ['Alto', 'Bajo', 'Incompleto']);
  });

  test('parseFormatoA (forma canónica) y verificarDuplicados', () {
    final json = '''
    {"version":1,"partidos":[
      {"partido":"A vs B","fecha":"2026-09-12T21:00","cuotas":[
        {"casa":"Bet365","1":2.10,"X":3.40,"2":3.60},
        {"casa":"Winamax","1":2.05,"X":3.30,"2":3.55}]}
    ]}''';
    final partidos = parsearFormatoA(json);
    expect(partidos, hasLength(1));
    expect(partidos.first.nombre, 'A vs B');
    expect(partidos.first.casa('bet365')!['1'], d('2.10'));
    verificarDuplicados(partidos); // no lanza
  });

  test('verificarDuplicados detecta casa repetida', () {
    final p = Partido('A vs B', null, [
      casa('Bet365', '2.10', '3.40', '3.60'),
      casa(' bet365 ', '2.05', '3.30', '3.55'),
    ]);
    expect(() => verificarDuplicados([p]), throwsA(isA<ErrorDatos>()));
  });
}
