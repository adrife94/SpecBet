import 'package:flutter/widgets.dart';

import '../core/odds.dart';

/// Estado compartido de la app: la fuente única de cuotas + tema + filtro promo.
/// Sin dependencias externas: `ChangeNotifier` + `InheritedNotifier`.
class AppState extends ChangeNotifier {
  List<Partido> partidos = _seed();
  bool oscuro = false;

  bool promoOn = false;
  final Set<String> promoCasas = {'Bet365', 'Codere'}; // nombres tal cual

  String inversion = '200';
  String archivo = 'ejemplo.json';
  String sello = 'datos de ejemplo';

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
    m('Valencia vs FC Barcelona', '2026-09-12T21:00', {
      'Bet365': [10.50, 6.40, 1.25],
      'Winamax': [9.00, 6.00, 1.26],
      'Codere': [9.50, 6.25, 1.28],
      '20Bet': [9.75, 6.10, 1.27],
      'YoSports': [null, null, null],
    }),
    m('Alaves vs Osasuna', '2026-09-13T16:15', {
      'Bet365': [2.35, 3.15, 3.50],
      'Winamax': [2.25, 3.10, 3.35],
      'Codere': [2.25, 3.25, 3.45],
      '20Bet': [2.35, 3.20, 3.40],
      'YoSports': [2.30, 3.10, 3.35],
    }),
    m('Atleti vs Sevilla', '2026-09-13T18:30', {
      'Bet365': [2.55, 3.30, 2.50],
      'Winamax': [2.60, 3.20, 2.45],
      'Codere': [2.50, 3.35, 2.60],
      '20Bet': [2.45, 3.25, 2.55],
      'YoSports': [2.40, 2.60, 2.50],
    }),
  ];
}
