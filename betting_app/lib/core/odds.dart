import 'dart:convert';

import 'package:decimal/decimal.dart';

import 'money.dart';

/// Modelos y carga del "Formato A" (cuotas por casa), el mismo JSON que usa el
/// comparador de la CLI de Python. Port de `storage.cargar` + validación.

const resultados = ['1', 'X', '2'];

/// El archivo/entrada no es válido o su estructura no es la esperada.
class ErrorDatos implements Exception {
  final String mensaje;
  ErrorDatos(this.mensaje);
  @override
  String toString() => mensaje;
}

/// Clave para comparar nombres de casa/partido: sin espacios exteriores y sin
/// distinguir mayúsculas (equivale a `str.strip().casefold()` de Python).
String normalizar(String s) => s.trim().toLowerCase();

/// Cuota válida = número mayor que 1. Cualquier otra cosa (nula, ≤ 1, no
/// numérica) es un hueco → `null`.
Decimal? cuotaValida(Object? v) {
  if (v == null) return null;
  Decimal? d;
  if (v is num) {
    // El shortest-toString de Dart preserva la cuota (2.10 -> "2.1", 1.28 -> "1.28").
    d = Decimal.tryParse(v.toString());
  } else if (v is String) {
    d = Decimal.tryParse(v.replaceAll(',', '.').trim());
  }
  if (d == null) return null;
  return d > uno ? d : null;
}

/// Cuotas 1/X/2 de una casa en un partido. Un resultado ausente es `null`.
class CuotaCasa {
  final String casa;
  final Map<String, Decimal?> cuotas;
  CuotaCasa(this.casa, this.cuotas);

  Decimal? operator [](String resultado) => cuotas[resultado];
}

/// Un partido con su fecha opcional (ISO 8601) y sus cuotas por casa.
class Partido {
  final String nombre;
  final String? fecha;
  final List<CuotaCasa> casas;
  Partido(this.nombre, this.fecha, this.casas);

  CuotaCasa? casa(String nombreCasa) {
    final clave = normalizar(nombreCasa);
    for (final c in casas) {
      if (normalizar(c.casa) == clave) return c;
    }
    return null;
  }
}

/// Carga el Formato A desde un texto JSON. Acepta la forma canónica
/// (`cuotas` como lista de `{casa, "1","X","2"}`) y la forma por objeto
/// (`cuotas: {casa: {"1","X","2"}}`). Lanza [ErrorDatos] si no es válido.
List<Partido> parsearFormatoA(String texto) {
  Object? datos;
  try {
    datos = jsonDecode(texto);
  } catch (e) {
    throw ErrorDatos('El texto no es JSON válido: $e');
  }

  final lista = datos is List
      ? datos
      : (datos is Map && datos['partidos'] is List ? datos['partidos'] as List : null);
  if (lista == null) {
    throw ErrorDatos('Se esperaba una lista de partidos (Formato A).');
  }

  final partidos = <Partido>[];
  for (final p in lista) {
    if (p is! Map) throw ErrorDatos('Cada partido debe ser un objeto.');
    final nombre = p['partido'] ?? p['nombre'] ?? p['name'];
    if (nombre is! String || nombre.trim().isEmpty) {
      throw ErrorDatos('Un partido no tiene un nombre válido.');
    }
    final fecha = p['fecha'] is String ? p['fecha'] as String : null;
    final src = p['cuotas'] ?? p['odds'];
    final casas = <CuotaCasa>[];

    if (src is List) {
      for (final e in src) {
        if (e is! Map) throw ErrorDatos("Entrada de 'cuotas' inválida en '$nombre'.");
        final casa = e['casa'];
        if (casa is! String || casa.trim().isEmpty) {
          throw ErrorDatos("Una casa de '$nombre' no tiene nombre válido.");
        }
        casas.add(CuotaCasa(casa, {for (final r in resultados) r: cuotaValida(e[r])}));
      }
    } else if (src is Map) {
      src.forEach((casa, c) {
        final m = c is Map ? c : const {};
        casas.add(CuotaCasa(casa.toString(), {
          for (final r in resultados) r: cuotaValida(m[r] ?? (r == 'X' ? m['x'] : null)),
        }));
      });
    } else {
      throw ErrorDatos("El partido '$nombre' no tiene 'cuotas'.");
    }

    partidos.add(Partido(nombre, fecha, casas));
  }
  return partidos;
}

/// Mejor cuota de un resultado en un partido, opcionalmente restringida a un
/// conjunto de casas (`soloEn`) o excluyendo otras (`excluir`); los conjuntos van
/// con claves ya normalizadas. Ante empate, la primera por orden de entrada.
/// Base común de coberturas (freebet/bonus/multibono) y del filtro de promo.
({Decimal cuota, String casa})? mejorCuota(
  Partido p,
  String resultado, {
  Set<String>? soloEn,
  Set<String>? excluir,
}) {
  Decimal? tope;
  String? casa;
  for (final c in p.casas) {
    final k = normalizar(c.casa);
    if (soloEn != null && !soloEn.contains(k)) continue;
    if (excluir != null && excluir.contains(k)) continue;
    final v = c[resultado];
    if (v == null) continue;
    if (tope == null || v > tope) {
      tope = v;
      casa = c.casa;
    }
  }
  return tope == null ? null : (cuota: tope, casa: casa!);
}

/// Aborta si hay partidos repetidos o una casa repetida dentro de un partido
/// (comparando con [normalizar]). Port de `core.verificar_duplicados`.
void verificarDuplicados(List<Partido> partidos) {
  final vistos = <String, String>{};
  for (final p in partidos) {
    final clave = normalizar(p.nombre);
    final anterior = vistos[clave];
    if (anterior != null) {
      throw ErrorDatos("El partido '${p.nombre}' aparece más de una vez (coincide con '$anterior').");
    }
    vistos[clave] = p.nombre;

    final casasVistas = <String, String>{};
    for (final c in p.casas) {
      final ck = normalizar(c.casa);
      final ant = casasVistas[ck];
      if (ant != null) {
        throw ErrorDatos("La casa '${c.casa}' aparece más de una vez en '${p.nombre}' (coincide con '$ant').");
      }
      casasVistas[ck] = c.casa;
    }
  }
}
