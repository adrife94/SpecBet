import 'package:decimal/decimal.dart';

/// Utilidades de dinero/cuotas con precisión decimal (nunca `double`).
///
/// El core no redondea los cálculos intermedios; el redondeo a 2 decimales
/// (ROUND_HALF_UP, que es el que usa `Decimal.round`/`toStringAsFixed`) ocurre
/// solo en la capa de presentación. Equivale a la constitución nº 8 del proyecto.

final Decimal cero = Decimal.fromInt(0);
final Decimal uno = Decimal.fromInt(1);
final Decimal cien = Decimal.fromInt(100);

/// División `Decimal / Decimal` → `Decimal`. En `decimal` 3.x, `/` devuelve un
/// `Rational`; lo convertimos con precisión amplia para no perder exactitud
/// (equivalente al contexto Decimal de Python).
Decimal div(Decimal a, Decimal b) =>
    (a / b).toDecimal(scaleOnInfinitePrecision: 30);

/// Redondeo a 2 decimales (ROUND_HALF_UP). Solo para presentar.
Decimal round2(Decimal d) => d.round(scale: 2);

/// Importe en euros, formato español: "172,50 €".
String eur(Decimal d) => '${d.toStringAsFixed(2).replaceAll('.', ',')} €';

/// Porcentaje, formato español: "62,69 %".
String pct(Decimal d) => '${d.toStringAsFixed(2).replaceAll('.', ',')} %';

/// Cuota con punto decimal: "2.60", o "—" si no hay.
String cuotaStr(Decimal? d) => d == null ? '—' : d.toStringAsFixed(2);

/// Convierte texto del usuario a `Decimal` (acepta coma o punto); `null` si no
/// es un número válido.
Decimal? parseDec(String s) => Decimal.tryParse(s.replaceAll(',', '.').trim());
