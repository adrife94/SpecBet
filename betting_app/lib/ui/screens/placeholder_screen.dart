import 'package:flutter/material.dart';

import '../theme.dart';

/// Pantalla pendiente de implementar (Surebet/Freebet/Bonus/Multibono).
class PlaceholderScreen extends StatelessWidget {
  final String titulo;
  const PlaceholderScreen(this.titulo, {super.key});

  @override
  Widget build(BuildContext context) {
    final p = Theme.of(context).extension<AppPalette>()!;
    return Center(
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(Icons.construction_outlined, size: 40, color: p.ink3),
          const SizedBox(height: 10),
          Text(titulo, style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w600)),
          const SizedBox(height: 4),
          Text('En construcción — el cálculo ya está en el core.', style: TextStyle(color: p.ink2)),
        ],
      ),
    );
  }
}
