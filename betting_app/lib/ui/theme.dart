import 'package:flutter/material.dart';

/// Paleta semántica del diseño (tokens del mockup, oklch → sRGB aproximado).
/// Se expone como `ThemeExtension` para leerla con
/// `Theme.of(context).extension<AppPalette>()!`.
@immutable
class AppPalette extends ThemeExtension<AppPalette> {
  final Color bg, panel, panel2, panel3, line, line2;
  final Color ink, ink2, ink3, accent, accentSoft;
  final Color greenBg, greenFg, amberBg, amberFg, redBg, redFg, blueBg, blueFg, grayBg, grayFg;

  const AppPalette({
    required this.bg,
    required this.panel,
    required this.panel2,
    required this.panel3,
    required this.line,
    required this.line2,
    required this.ink,
    required this.ink2,
    required this.ink3,
    required this.accent,
    required this.accentSoft,
    required this.greenBg,
    required this.greenFg,
    required this.amberBg,
    required this.amberFg,
    required this.redBg,
    required this.redFg,
    required this.blueBg,
    required this.blueFg,
    required this.grayBg,
    required this.grayFg,
  });

  /// Devuelve (fondo, texto) del tono semántico: green/amber/red/blue/gray.
  (Color, Color) tono(String t) => switch (t) {
        'green' => (greenBg, greenFg),
        'amber' => (amberBg, amberFg),
        'red' => (redBg, redFg),
        'blue' => (blueBg, blueFg),
        _ => (grayBg, grayFg),
      };

  static const light = AppPalette(
    bg: Color(0xFFEFF1F4),
    panel: Color(0xFFFFFFFF),
    panel2: Color(0xFFF7F8FA),
    panel3: Color(0xFFE9EBEF),
    line: Color(0xFFE1E4E9),
    line2: Color(0xFFC9CFD8),
    ink: Color(0xFF2A2F37),
    ink2: Color(0xFF6C727C),
    ink3: Color(0xFF969CA6),
    accent: Color(0xFF2E6E9E),
    accentSoft: Color(0xFFDDE9F5),
    greenBg: Color(0xFFD6F0E1),
    greenFg: Color(0xFF1E8A5A),
    amberBg: Color(0xFFF6EAC9),
    amberFg: Color(0xFF8F6410),
    redBg: Color(0xFFF7DED9),
    redFg: Color(0xFFB83A2C),
    blueBg: Color(0xFFDEE8F7),
    blueFg: Color(0xFF35569E),
    grayBg: Color(0xFFE9EBEF),
    grayFg: Color(0xFF6C727C),
  );

  static const dark = AppPalette(
    bg: Color(0xFF202430),
    panel: Color(0xFF262B36),
    panel2: Color(0xFF2D323E),
    panel3: Color(0xFF353B48),
    line: Color(0xFF383E4B),
    line2: Color(0xFF4A505E),
    ink: Color(0xFFF1F2F4),
    ink2: Color(0xFFB4B9C2),
    ink3: Color(0xFF8A909B),
    accent: Color(0xFF7FB2D8),
    accentSoft: Color(0xFF2B4257),
    greenBg: Color(0xFF22503B),
    greenFg: Color(0xFF7FD9A8),
    amberBg: Color(0xFF4A3A1A),
    amberFg: Color(0xFFE0B86A),
    redBg: Color(0xFF4A2822),
    redFg: Color(0xFFE39187),
    blueBg: Color(0xFF26364F),
    blueFg: Color(0xFF9FBDE8),
    grayBg: Color(0xFF353B48),
    grayFg: Color(0xFFB4B9C2),
  );

  @override
  AppPalette copyWith() => this;

  @override
  AppPalette lerp(ThemeExtension<AppPalette>? other, double t) =>
      t < 0.5 ? this : (other as AppPalette? ?? this);
}

/// Estilo monoespaciado con cifras tabulares (para cuotas/importes).
const TextStyle mono = TextStyle(
  fontFamily: 'monospace',
  fontFeatures: [FontFeature.tabularFigures()],
);

ThemeData buildTheme(bool dark) {
  final p = dark ? AppPalette.dark : AppPalette.light;
  final scheme = (dark ? const ColorScheme.dark() : const ColorScheme.light()).copyWith(
    primary: p.accent,
    surface: p.panel,
    onSurface: p.ink,
  );
  return ThemeData(
    useMaterial3: true,
    brightness: dark ? Brightness.dark : Brightness.light,
    scaffoldBackgroundColor: p.bg,
    colorScheme: scheme,
    extensions: [p],
    dividerColor: p.line,
  );
}
