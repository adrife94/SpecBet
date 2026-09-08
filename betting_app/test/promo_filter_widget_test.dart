import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:betting_app/main.dart';

void main() {
  testWidgets('promo con solo Winamax lo muestra en las opciones 1 y 2', (tester) async {
    // Viewport alto para que el ListView construya todo sin scroll.
    tester.view.physicalSize = const Size(1400, 10000);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(tester.view.resetPhysicalSize);
    addTearDown(tester.view.resetDevicePixelRatio);

    await tester.pumpWidget(const BettingApp());

    // Surebet es una pestaña con promo.
    await tester.tap(find.text('Surebet').first);
    await tester.pumpAndSettle();

    // Enciende el filtro promo.
    await tester.tap(find.byType(Switch));
    await tester.pumpAndSettle();

    // Marca SOLO Winamax.
    await tester.tap(find.widgetWithText(FilterChip, 'Winamax'));
    await tester.pumpAndSettle();

    // Las patas de ganar (1 y 2) se reposicionan en Winamax: aparece la etiqueta
    // de promo en las tarjetas y Winamax como casa de esas patas.
    expect(find.textContaining('promo · ventaja de 2 goles'), findsWidgets);
    expect(find.text('Winamax'), findsWidgets);
  });
}
