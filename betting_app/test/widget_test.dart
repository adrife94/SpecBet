import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:betting_app/main.dart';

void main() {
  testWidgets('arranca y muestra el título y la navegación', (tester) async {
    await tester.pumpWidget(const BettingApp());
    expect(find.text('SpecBet'), findsOneWidget);
    expect(find.text('Cuotas'), findsWidgets);
    expect(find.text('Comparador'), findsWidgets);
  });

  testWidgets('layout móvil estrecho: navega sin overflows', (tester) async {
    tester.view.physicalSize = const Size(390, 800);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);
    await tester.pumpWidget(const BettingApp());
    for (final t in ['Comparador', 'Surebet', 'Freebet', 'Bono', 'Multibono', 'Cuotas']) {
      await tester.tap(find.text(t).first);
      await tester.pumpAndSettle();
    }
  });

  testWidgets('navega por las herramientas con el filtro promo activo', (tester) async {
    await tester.pumpWidget(const BettingApp());
    // el filtro promo solo está en las calculadoras: ve a Surebet y enciéndelo.
    await tester.tap(find.text('Surebet').first);
    await tester.pumpAndSettle();
    await tester.tap(find.byType(Switch));
    await tester.pumpAndSettle();
    for (final t in ['Comparador', 'Surebet', 'Freebet', 'Bono', 'Multibono', 'Cuotas']) {
      await tester.tap(find.text(t).first);
      await tester.pumpAndSettle();
    }
  });
}
