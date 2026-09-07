import 'package:flutter/material.dart';

import '../theme.dart';

class SlipBadge {
  final String? label;
  final String value;
  final String tono;
  const SlipBadge(this.value, {this.label, this.tono = 'gray'});
}

class SlipLeg {
  final String chip; // "1" | "X" | "2"
  final String chipTono;
  final String? icon; // 🎟 / 💶
  final String casa;
  final String? kind;
  final String odds; // "2.60"
  final String amount; // "10,00 €"
  const SlipLeg({
    required this.chip,
    this.chipTono = 'gray',
    this.icon,
    required this.casa,
    this.kind,
    required this.odds,
    required this.amount,
  });
}

/// Tarjeta reutilizable de "boleto": cabecera (título + badges), patas y pie.
class BetSlip extends StatelessWidget {
  final String title;
  final String? sub;
  final bool destacada;
  final String destacadaTono;
  final List<SlipBadge> badges;
  final List<SlipLeg> legs;
  final String? footer;

  const BetSlip({
    super.key,
    required this.title,
    this.sub,
    this.destacada = false,
    this.destacadaTono = 'green',
    this.badges = const [],
    required this.legs,
    this.footer,
  });

  @override
  Widget build(BuildContext context) {
    final p = Theme.of(context).extension<AppPalette>()!;
    final edge = destacada ? p.tono(destacadaTono).$2 : p.line;

    return Container(
      decoration: BoxDecoration(
        color: p.panel,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: edge, width: destacada ? 1.5 : 1),
      ),
      clipBehavior: Clip.antiAlias,
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Container(
            color: p.panel2,
            padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 11),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                if (destacada) const Padding(padding: EdgeInsets.only(right: 6), child: Text('★')),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(title, style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600)),
                      if (sub != null)
                        Text(sub!, style: TextStyle(fontSize: 11.5, color: p.ink3)),
                    ],
                  ),
                ),
                if (badges.isNotEmpty)
                  Flexible(
                    child: Wrap(
                      alignment: WrapAlignment.end,
                      spacing: 6,
                      runSpacing: 6,
                      children: [for (final b in badges) _badge(p, b)],
                    ),
                  ),
              ],
            ),
          ),
          for (final l in legs) _leg(p, l),
          if (footer != null)
            Container(
              color: p.panel2,
              padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 9),
              child: Text(footer!, style: TextStyle(fontSize: 11.5, color: p.ink2)),
            ),
        ],
      ),
    );
  }

  Widget _badge(AppPalette p, SlipBadge b) {
    final (bg, fg) = p.tono(b.tono);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
      decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(7)),
      child: Row(mainAxisSize: MainAxisSize.min, children: [
        if (b.label != null) ...[
          Text(b.label!, style: TextStyle(color: fg.withValues(alpha: 0.85), fontSize: 11, fontWeight: FontWeight.w500)),
          const SizedBox(width: 5),
        ],
        Text(b.value, style: mono.copyWith(color: fg, fontSize: 11.5, fontWeight: FontWeight.w600)),
      ]),
    );
  }

  Widget _leg(AppPalette p, SlipLeg l) {
    final (bg, fg) = p.tono(l.chipTono);
    return Container(
      decoration: BoxDecoration(border: Border(bottom: BorderSide(color: p.line))),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      child: Row(
        children: [
          Container(
            width: 22,
            height: 22,
            alignment: Alignment.center,
            decoration: BoxDecoration(color: bg, borderRadius: BorderRadius.circular(6)),
            child: Text(l.chip, style: TextStyle(color: fg, fontSize: 11, fontWeight: FontWeight.w700)),
          ),
          const SizedBox(width: 8),
          if (l.icon != null) ...[Text(l.icon!, style: const TextStyle(fontSize: 13)), const SizedBox(width: 8)],
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(l.casa, style: const TextStyle(fontSize: 12.5, fontWeight: FontWeight.w600)),
                if (l.kind != null) Text(l.kind!, style: TextStyle(fontSize: 10.5, color: p.ink3)),
              ],
            ),
          ),
          Text('@${l.odds}', style: mono.copyWith(fontSize: 12.5, color: p.ink2)),
          const SizedBox(width: 12),
          SizedBox(
            width: 88,
            child: Text(l.amount, textAlign: TextAlign.right, style: mono.copyWith(fontSize: 13.5, fontWeight: FontWeight.w700)),
          ),
        ],
      ),
    );
  }
}
