import 'package:flutter/material.dart';

import 'state/app_state.dart';
import 'ui/app_shell.dart';
import 'ui/theme.dart';

void main() => runApp(const BettingApp());

class BettingApp extends StatefulWidget {
  const BettingApp({super.key});
  @override
  State<BettingApp> createState() => _BettingAppState();
}

class _BettingAppState extends State<BettingApp> {
  final AppState state = AppState();

  @override
  void dispose() {
    state.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AppScope(
      notifier: state,
      child: ListenableBuilder(
        listenable: state,
        builder: (context, _) => MaterialApp(
          title: 'SpecBet',
          debugShowCheckedModeBanner: false,
          theme: buildTheme(false),
          darkTheme: buildTheme(true),
          themeMode: state.oscuro ? ThemeMode.dark : ThemeMode.light,
          home: const AppShell(),
        ),
      ),
    );
  }
}
