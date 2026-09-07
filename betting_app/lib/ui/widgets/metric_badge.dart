import 'package:flutter/material.dart';

import '../theme.dart';

/// Badge de métrica con tono semántico (green/amber/red/blue/gray).
class MetricBadge extends StatelessWidget {
  final String? label;
  final String value;
  final String tono;
  const MetricBadge({super.key, this.label, required this.value, this.tono = 'gray'});

  @override
  Widget build(BuildContext context) {
    final p = Theme.of(context).extension<AppPalette>()!;
    final (bg, fg) = p.tono(tono);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(7)),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (label != null) ...[
            Text(label!, style: TextStyle(color: fg.withValues(alpha: 0.85), fontSize: 11.5, fontWeight: FontWeight.w500)),
            const SizedBox(width: 6),
          ],
          Text(value, style: mono.copyWith(color: fg, fontSize: 12, fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }
}
