import 'package:flutter/material.dart';

import '../state/app_state.dart';
import 'screens/bonus_screen.dart';
import 'screens/comparador_screen.dart';
import 'screens/cuotas_screen.dart';
import 'screens/freebet_screen.dart';
import 'screens/multibono_screen.dart';
import 'screens/surebet_screen.dart';
import 'theme.dart';
import 'widgets/app_sidebar.dart';

class AppShell extends StatefulWidget {
  const AppShell({super.key});
  @override
  State<AppShell> createState() => _AppShellState();
}

class _AppShellState extends State<AppShell> {
  int _sel = 0;

  void _select(int i) => setState(() => _sel = i);

  static const _items = [
    (label: 'Cuotas', icon: Icons.table_chart_outlined),
    (label: 'Comparador', icon: Icons.leaderboard_outlined),
    (label: 'Surebet', icon: Icons.balance_outlined),
    (label: 'Freebet', icon: Icons.card_giftcard_outlined),
    (label: 'Bonus', icon: Icons.savings_outlined),
    (label: 'Multibono', icon: Icons.account_tree_outlined),
  ];

  Widget _screen() => switch (_sel) {
        0 => const CuotasScreen(),
        1 => const ComparadorScreen(),
        2 => const SurebetScreen(),
        3 => const FreebetScreen(),
        4 => const BonusScreen(),
        _ => const MultibonoScreen(),
      };

  @override
  Widget build(BuildContext context) {
    final state = AppScope.of(context);
    final p = Theme.of(context).extension<AppPalette>()!;

    return Scaffold(
      appBar: AppBar(
        backgroundColor: p.panel,
        elevation: 0,
        shape: Border(bottom: BorderSide(color: p.line)),
        titleSpacing: 14,
        title: Row(
          children: [
            Container(
              width: 27,
              height: 27,
              decoration: BoxDecoration(color: p.accent, borderRadius: BorderRadius.circular(6)),
              alignment: Alignment.center,
              child: Text('1X2', style: mono.copyWith(color: p.panel, fontSize: 12, fontWeight: FontWeight.w700)),
            ),
            const SizedBox(width: 10),
            const Text('Betting Calculator', style: TextStyle(fontSize: 15, fontWeight: FontWeight.w600)),
          ],
        ),
        actions: [
          IconButton(
            tooltip: 'Cambiar tema',
            onPressed: state.alternarTema,
            icon: Icon(state.oscuro ? Icons.light_mode_outlined : Icons.dark_mode_outlined),
          ),
          const SizedBox(width: 4),
        ],
      ),
      body: Column(
        children: [
          Container(
            width: double.infinity,
            color: p.amberBg,
            padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 7),
            child: Text(
              'Las cuotas caducan. Verifícalas en la casa justo antes de apostar; esta app no consulta cuotas en vivo.',
              style: TextStyle(color: p.amberFg, fontSize: 12),
            ),
          ),
          Container(
            width: double.infinity,
            color: p.panel2,
            padding: const EdgeInsets.fromLTRB(18, 4, 8, 4),
            child: Row(
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
                TextButton(onPressed: state.verificar, child: const Text('Verificar cuotas')),
              ],
            ),
          ),
          Expanded(
            child: LayoutBuilder(
              builder: (context, constraints) {
                if (constraints.maxWidth >= 760) {
                  return Row(
                    children: [
                      AppSidebar(selected: _sel, onSelect: _select, items: _items),
                      VerticalDivider(width: 1, color: p.line),
                      Expanded(child: _screen()),
                    ],
                  );
                }
                return Column(
                  children: [
                    TopNav(selected: _sel, onSelect: _select, items: _items),
                    Divider(height: 1, color: p.line),
                    ExpansionTile(
                      title: const Text('Filtro promo · ventaja de 2 goles',
                          style: TextStyle(fontSize: 13, fontWeight: FontWeight.w600)),
                      childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 12),
                      children: const [PromoControls()],
                    ),
                    Divider(height: 1, color: p.line),
                    Expanded(child: _screen()),
                  ],
                );
              },
            ),
          ),
        ],
      ),
    );
  }
}
