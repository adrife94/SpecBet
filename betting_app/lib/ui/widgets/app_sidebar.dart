import 'package:flutter/material.dart';

import '../../state/app_state.dart';
import '../theme.dart';

typedef NavItem = ({String label, IconData icon});

/// Barra lateral (pantallas anchas): navegación vertical + caja de promo.
class AppSidebar extends StatelessWidget {
  final int selected;
  final ValueChanged<int> onSelect;
  final List<NavItem> items;
  const AppSidebar({super.key, required this.selected, required this.onSelect, required this.items});

  @override
  Widget build(BuildContext context) {
    final p = Theme.of(context).extension<AppPalette>()!;
    return Container(
      width: 240,
      color: p.panel,
      child: SingleChildScrollView(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            for (var i = 0; i < items.length; i++)
              _NavButton(item: items[i], on: i == selected, onTap: () => onSelect(i)),
            const SizedBox(height: 16),
            Container(
              decoration: BoxDecoration(
                color: p.panel2,
                borderRadius: BorderRadius.circular(9),
                border: Border.all(color: p.line),
              ),
              padding: const EdgeInsets.all(12),
              child: const PromoControls(),
            ),
          ],
        ),
      ),
    );
  }
}

/// Navegación superior (pantallas estrechas / móvil): chips en fila horizontal.
class TopNav extends StatelessWidget {
  final int selected;
  final ValueChanged<int> onSelect;
  final List<NavItem> items;
  const TopNav({super.key, required this.selected, required this.onSelect, required this.items});

  @override
  Widget build(BuildContext context) {
    final p = Theme.of(context).extension<AppPalette>()!;
    return Container(
      color: p.panel,
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
        child: Row(
          children: [
            for (var i = 0; i < items.length; i++)
              Padding(
                padding: const EdgeInsets.only(right: 8),
                child: ChoiceChip(
                  avatar: Icon(items[i].icon, size: 16, color: i == selected ? p.accent : p.ink2),
                  label: Text(items[i].label),
                  selected: i == selected,
                  onSelected: (_) => onSelect(i),
                ),
              ),
          ],
        ),
      ),
    );
  }
}

class _NavButton extends StatelessWidget {
  final NavItem item;
  final bool on;
  final VoidCallback onTap;
  const _NavButton({required this.item, required this.on, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final p = Theme.of(context).extension<AppPalette>()!;
    return Padding(
      padding: const EdgeInsets.only(bottom: 2),
      child: Material(
        color: on ? p.accentSoft : Colors.transparent,
        borderRadius: BorderRadius.circular(7),
        child: InkWell(
          borderRadius: BorderRadius.circular(7),
          onTap: onTap,
          child: Container(
            decoration: BoxDecoration(
              border: Border(left: BorderSide(color: on ? p.accent : Colors.transparent, width: 2)),
            ),
            padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 10),
            child: Row(children: [
              Icon(item.icon, size: 18, color: on ? p.accent : p.ink2),
              const SizedBox(width: 10),
              Text(item.label,
                  style: TextStyle(fontSize: 13.5, fontWeight: FontWeight.w600, color: on ? p.accent : p.ink2)),
            ]),
          ),
        ),
      ),
    );
  }
}

/// Interruptor del filtro promo + chips de casas. Reutilizable en la barra
/// lateral (ancho) y en el desplegable superior (móvil).
class PromoControls extends StatelessWidget {
  const PromoControls({super.key});

  @override
  Widget build(BuildContext context) {
    final state = AppScope.of(context);
    final p = Theme.of(context).extension<AppPalette>()!;
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(children: [
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Filtro promo', style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
                Text('Ventaja de 2 goles', style: TextStyle(fontSize: 11.5, color: p.ink2)),
              ],
            ),
          ),
          Switch(value: state.promoOn, onChanged: (_) => state.alternarPromo()),
        ]),
        const Divider(height: 18),
        Text('CASAS CON PROMO',
            style: TextStyle(fontSize: 10.5, letterSpacing: 0.7, color: p.ink3, fontWeight: FontWeight.w600)),
        const SizedBox(height: 8),
        Wrap(
          spacing: 6,
          runSpacing: 6,
          children: [
            for (final casa in state.casas)
              FilterChip(
                label: Text(casa, style: const TextStyle(fontSize: 11.5)),
                selected: state.promoCasas.contains(casa),
                onSelected: (_) => state.alternarPromoCasa(casa),
                visualDensity: VisualDensity.compact,
                materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
              ),
          ],
        ),
      ],
    );
  }
}
