import 'package:flutter/material.dart';

import '../../state/app_state.dart';
import '../theme.dart';

Widget screenTitle(BuildContext c, String title, String sub) {
  final p = Theme.of(c).extension<AppPalette>()!;
  return Column(
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text(title, style: const TextStyle(fontSize: 22, fontWeight: FontWeight.w600)),
      Text(sub, style: TextStyle(color: p.ink2, fontSize: 12.5)),
    ],
  );
}

Widget labeledField(BuildContext c, String label, Widget child) {
  final p = Theme.of(c).extension<AppPalette>()!;
  return Column(
    mainAxisSize: MainAxisSize.min,
    crossAxisAlignment: CrossAxisAlignment.start,
    children: [
      Text(label.toUpperCase(),
          style: TextStyle(fontSize: 10.5, letterSpacing: 0.6, color: p.ink3, fontWeight: FontWeight.w600)),
      const SizedBox(height: 5),
      child,
    ],
  );
}

Widget formCard(BuildContext c, {required Widget child, String? note}) {
  final p = Theme.of(c).extension<AppPalette>()!;
  return Container(
    decoration: BoxDecoration(
      color: p.panel,
      borderRadius: BorderRadius.circular(10),
      border: Border.all(color: p.line),
    ),
    padding: const EdgeInsets.all(14),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        child,
        if (note != null) ...[
          const SizedBox(height: 10),
          Text(note, style: TextStyle(fontSize: 11.5, color: p.ink3)),
        ],
      ],
    ),
  );
}

const InputDecoration denseInput = InputDecoration(border: OutlineInputBorder(), isDense: true);

/// Pie de página: aviso de caducidad de cuotas + fuente de datos activa.
/// Va como último hijo del ListView de cada pantalla, así baja con el scroll
/// en vez de quedar fijo.
Widget pieAviso(BuildContext c) {
  final p = Theme.of(c).extension<AppPalette>()!;
  final state = AppScope.of(c);
  return Padding(
    padding: const EdgeInsets.only(top: 18),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Container(
          decoration: BoxDecoration(color: p.amberBg, borderRadius: BorderRadius.circular(10)),
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
          child: Text(
            'Las cuotas caducan. Verifícalas en la casa justo antes de apostar; esta app no consulta cuotas en vivo.',
            style: TextStyle(color: p.amberFg, fontSize: 12),
          ),
        ),
        const SizedBox(height: 8),
        Row(
          children: [
            Icon(Icons.description_outlined, size: 15, color: p.ink3),
            const SizedBox(width: 6),
            Expanded(
              child: Text(
                'Cuotas: ${state.archivo} · ${state.sello}',
                overflow: TextOverflow.ellipsis,
                style: TextStyle(fontSize: 12, color: p.ink2),
              ),
            ),
          ],
        ),
      ],
    ),
  );
}

Widget avisoBox(BuildContext c, String texto) {
  final p = Theme.of(c).extension<AppPalette>()!;
  return Container(
    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
    decoration: BoxDecoration(color: p.amberBg, borderRadius: BorderRadius.circular(10)),
    child: Text(texto, style: TextStyle(color: p.amberFg, fontSize: 12)),
  );
}
