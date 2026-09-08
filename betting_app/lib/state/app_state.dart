import 'package:flutter/widgets.dart';

import '../core/odds.dart';
import '../core/promo.dart';

/// Estado compartido de la app: la fuente única de cuotas + tema + filtro promo.
/// Sin dependencias externas: `ChangeNotifier` + `InheritedNotifier`.
class AppState extends ChangeNotifier {
  List<Partido> partidos = _seed();
  bool oscuro = false;

  bool promoOn = false;
  final Set<String> promoCasas = <String>{}; // el usuario marca las casas con promo

  String inversion = '200';
  String archivo = 'ejemplo.json';
  String sello = 'datos de ejemplo';

  /// Filtro de promo activo, o `null` si está apagado o sin casas marcadas.
  /// Las herramientas lo pasan a su cálculo para reposicionar las patas de ganar.
  FiltroPromo? get filtroPromo =>
      (promoOn && promoCasas.isNotEmpty) ? FiltroPromo(promoCasas.map(normalizar).toSet()) : null;

  /// Casas presentes, en orden de primera aparición.
  List<String> get casas {
    final vistas = <String>{};
    final out = <String>[];
    for (final p in partidos) {
      for (final c in p.casas) {
        if (vistas.add(normalizar(c.casa))) out.add(c.casa);
      }
    }
    return out;
  }

  void alternarTema() {
    oscuro = !oscuro;
    notifyListeners();
  }

  void alternarPromo() {
    promoOn = !promoOn;
    notifyListeners();
  }

  void alternarPromoCasa(String casa) {
    if (!promoCasas.remove(casa)) promoCasas.add(casa);
    notifyListeners();
  }

  void setInversion(String v) {
    inversion = v;
    notifyListeners();
  }

  void verificar() {
    final t = DateTime.now();
    sello = 'verificadas ${t.hour.toString().padLeft(2, '0')}:${t.minute.toString().padLeft(2, '0')}';
    notifyListeners();
  }

  /// Importa Formato A desde texto JSON. Lanza [ErrorDatos] si no es válido.
  void importar(String texto) {
    final ps = parsearFormatoA(texto);
    verificarDuplicados(ps);
    partidos = ps;
    final t = DateTime.now();
    archivo = 'pegado.json';
    sello = 'importadas ${t.hour.toString().padLeft(2, '0')}:${t.minute.toString().padLeft(2, '0')}';
    notifyListeners();
  }
}

/// Provee el [AppState] al árbol de widgets. `AppScope.of(context)`.
class AppScope extends InheritedNotifier<AppState> {
  const AppScope({super.key, required AppState super.notifier, required super.child});

  static AppState of(BuildContext context) {
    final scope = context.dependOnInheritedWidgetOfExactType<AppScope>();
    assert(scope != null, 'No hay AppScope en el árbol');
    return scope!.notifier!;
  }
}

List<Partido> _seed() {
  Partido m(String nombre, String fecha, Map<String, List<num?>> odds) => Partido(
        nombre,
        fecha,
        [
          for (final e in odds.entries)
            CuotaCasa(e.key, {
              '1': cuotaValida(e.value[0]),
              'X': cuotaValida(e.value[1]),
              '2': cuotaValida(e.value[2]),
            }),
        ],
      );
  return [
    m('AEK Atenas vs LASK Linz', '2026-09-08T16:45', {
      'SpeedyBet': [1.79, 4.10, 4.40],
      'Winamax': [1.74, 4.10, 4.00],
      'Codere': [1.80, 4.10, 4.25],
      '20Bet': [1.80, 4.10, 4.30],
      'Kirolbet': [1.80, 4.00, 4.10],
    }),
    m('Club Brugge vs Aston Villa', '2026-09-08T16:45', {
      'SpeedyBet': [2.55, 3.55, 2.75],
      'Winamax': [2.45, 3.60, 2.60],
      'Codere': [2.55, 3.75, 2.60],
      '20Bet': [2.60, 3.60, 2.70],
      'Kirolbet': [2.55, 3.50, 2.70],
    }),
    m('Borussia Dortmund vs Villarreal', '2026-09-08T19:00', {
      'SpeedyBet': [1.76, 4.20, 4.30],
      'Winamax': [1.76, 4.10, 3.85],
      'Codere': [1.80, 4.25, 4.10],
      '20Bet': [1.80, 4.20, 4.20],
      'Kirolbet': [1.80, 4.10, 4.10],
    }),
    m('FC Porto vs Manchester City', '2026-09-08T19:00', {
      'SpeedyBet': [5.00, 3.95, 1.70],
      'Winamax': [4.60, 4.20, 1.64],
      'Codere': [4.80, 4.10, 1.70],
      '20Bet': [4.90, 4.20, 1.71],
      'Kirolbet': [4.60, 4.00, 1.70],
    }),
    m('Lille vs Real Betis', '2026-09-08T19:00', {
      'SpeedyBet': [2.18, 3.45, 3.45],
      'Winamax': [2.15, 3.50, 3.15],
      'Codere': [2.20, 3.60, 3.25],
      '20Bet': [2.25, 3.50, 3.35],
      'Kirolbet': [2.25, 3.45, 3.30],
    }),
    m('Real Madrid vs Inter', '2026-09-08T19:00', {
      'SpeedyBet': [1.57, 4.70, 5.60],
      'Winamax': [1.56, 4.70, 4.70],
      'Codere': [1.60, 4.50, 5.25],
      '20Bet': [1.61, 4.70, 5.00],
      'Kirolbet': [1.60, 4.60, 4.90],
    }),
    m('FC Barcelona vs Feyenoord', '2026-09-09T16:45', {
      'SpeedyBet': [1.09, 13.00, 25.00],
      'Winamax': [1.06, 14.00, 19.00],
      'Codere': [1.08, 10.00, 27.00],
      '20Bet': [1.10, 12.00, 23.00],
      'Kirolbet': [1.08, 11.00, 21.00],
    }),
    m('VfB Stuttgart vs Viking Stavanger', '2026-09-09T16:45', {
      'SpeedyBet': [1.23, 7.00, 12.00],
      'Winamax': [1.21, 7.50, 9.00],
      'Codere': [1.22, 7.00, 10.00],
      '20Bet': [1.24, 7.20, 11.00],
      'Kirolbet': [1.22, 7.00, 10.00],
    }),
    m('Liverpool vs Atlético Madrid', '2026-09-09T19:00', {
      'SpeedyBet': [1.70, 4.10, 4.80],
      'Winamax': [1.68, 4.10, 4.40],
      'Codere': [1.75, 3.90, 4.25],
      '20Bet': [1.73, 4.00, 4.70],
      'Kirolbet': [1.70, 3.95, 4.60],
    }),
    m('Nápoles vs Arsenal', '2026-09-09T19:00', {
      'SpeedyBet': [5.20, 3.70, 1.72],
      'Winamax': [4.50, 3.75, 1.74],
      'Codere': [4.60, 3.70, 1.75],
      '20Bet': [4.80, 3.70, 1.78],
      'Kirolbet': [4.60, 3.60, 1.75],
    }),
    m('PSG vs Slovan Bratislava', '2026-09-09T19:00', {
      'SpeedyBet': [1.04, 18.00, 51.00],
      'Winamax': [1.05, 18.00, 30.00],
      'Codere': [1.03, 14.00, 50.00],
      '20Bet': [1.05, 16.00, 45.00],
      'Kirolbet': [1.04, 14.00, 35.00],
    }),
    m('Sporting Lisboa vs Galatasaray', '2026-09-09T19:00', {
      'SpeedyBet': [1.83, 3.95, 4.20],
      'Winamax': [1.80, 4.00, 3.85],
      'Codere': [1.85, 3.80, 3.80],
      '20Bet': [1.88, 3.80, 4.10],
      'Kirolbet': [1.85, 3.75, 3.95],
    }),
    m('Fenerbahçe vs Roma', '2026-09-10T16:45', {
      'SpeedyBet': [3.35, 3.55, 2.16],
      'Winamax': [3.15, 3.55, 2.10],
      'Codere': [2.90, 3.50, 2.30],
      '20Bet': [3.30, 3.45, 2.25],
      'Kirolbet': [3.20, 3.40, 2.20],
    }),
    m('PSV Eindhoven vs Shakhtar Donetsk', '2026-09-10T16:45', {
      'SpeedyBet': [1.45, 5.00, 6.75],
      'Winamax': [1.41, 5.20, 6.00],
      'Codere': [1.40, 5.00, 6.50],
      '20Bet': [1.44, 5.20, 6.60],
      'Kirolbet': [1.42, 5.00, 6.50],
    }),
    m('Bayern Múnich vs Bodø/Glimt', '2026-09-10T19:00', {
      'SpeedyBet': [1.11, 11.00, 21.00],
      'Winamax': [1.09, 11.50, 15.00],
      'Codere': [1.09, 10.00, 22.00],
      '20Bet': [1.11, 11.00, 20.00],
      'Kirolbet': [1.10, 10.00, 18.00],
    }),
    m('Como vs RB Leipzig', '2026-09-10T19:00', {
      'SpeedyBet': [1.86, 3.90, 4.00],
      'Winamax': [1.84, 4.00, 3.70],
      'Codere': [1.90, 3.90, 3.50],
      '20Bet': [1.91, 3.90, 3.85],
      'Kirolbet': [1.90, 3.80, 3.75],
    }),
    m('Manchester United vs Sabah FK', '2026-09-10T19:00', {
      'SpeedyBet': [1.12, 10.00, 21.00],
      'Winamax': [1.11, 8.50, 19.00],
      'Codere': [1.09, 9.50, 27.00],
      '20Bet': [1.12, 10.00, 22.00],
      'Kirolbet': [1.10, 10.00, 21.00],
    }),
    m('Slavia Praga vs Lens', '2026-09-10T19:00', {
      'SpeedyBet': [2.65, 3.45, 2.65],
      'Winamax': [2.50, 3.50, 2.55],
      'Codere': [2.55, 3.50, 2.55],
      '20Bet': [2.65, 3.50, 2.70],
      'Kirolbet': [2.55, 3.45, 2.65],
    }),
  ];
}
