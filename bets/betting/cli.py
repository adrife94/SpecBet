"""Interfaz de línea de comandos de betting-cli."""

from __future__ import annotations

import argparse
import json
import sys
from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

from betting import core, storage
from betting.core import MejorCuota, PartidoEvaluado, Reparto
from betting.storage import ErrorDatos

SIN_DATO = "—"
RECORDATORIO_CUOTAS = (
    "Recuerda: las cuotas caducan. Verifícalas en cada casa justo antes de apostar."
)


def build_parser() -> argparse.ArgumentParser:
    """Construye el parser con el subcomando `compare`."""
    parser = argparse.ArgumentParser(
        prog="betting",
        description="Herramienta de apoyo a decisiones de apuestas deportivas.",
    )
    sub = parser.add_subparsers(dest="comando", required=True)

    compare = sub.add_parser(
        "compare",
        help="Compara cuotas 1X2 de un archivo JSON y calcula el % de pago.",
    )
    compare.add_argument(
        "archivo",
        help="Ruta al archivo JSON con los partidos y sus cuotas.",
    )
    compare.add_argument(
        "--json",
        action="store_true",
        help="Emite el resultado como JSON reutilizable en vez de la tabla.",
    )
    compare.set_defaults(func=_compare)

    surebet = sub.add_parser(
        "surebet",
        help="Reparte una inversión entre 1/X/2 sobre la salida de 'compare --json'.",
    )
    surebet.add_argument(
        "archivo",
        help="Ruta al JSON producido por 'compare --json'.",
    )
    surebet.add_argument(
        "--inversion",
        required=True,
        metavar="IMPORTE",
        help="Inversión total a repartir en cada partido (número mayor que 0).",
    )
    surebet.add_argument(
        "--json",
        action="store_true",
        help="Emite el resultado como JSON reutilizable en vez de la tabla.",
    )
    surebet.set_defaults(func=_surebet)
    return parser


def _compare(args: argparse.Namespace) -> int:
    try:
        partidos = storage.cargar(args.archivo)
        evaluados = core.comparar(partidos)
    except ErrorDatos as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    _avisar_descartes(evaluados)

    if args.json:
        print(_json_salida(evaluados))
        return 0

    if not evaluados:
        print("No hay partidos que comparar.")
        return 0

    print(_tabla(evaluados))
    return 0


def _avisar_descartes(evaluados: list[PartidoEvaluado]) -> None:
    """Avisa por stderr de cada cuota inválida ignorada (RF-8)."""
    for ev in evaluados:
        for d in ev.descartes:
            print(
                f"Aviso: cuota inválida ignorada en '{d.partido}' / {d.casa} "
                f"({d.resultado} = {d.valor!r}).",
                file=sys.stderr,
            )


def _fmt_payout(payout: Decimal | None) -> str:
    if payout is None:
        return SIN_DATO
    return str(payout.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _celda(mejor: MejorCuota | None) -> str:
    if mejor is None:
        return SIN_DATO
    return f"{mejor.cuota} {'/'.join(mejor.casas)}"


def _tabla(evaluados: list[PartidoEvaluado]) -> str:
    encabezados = ["Partido", "% pago", "1", "X", "2"]
    filas = [
        [
            ev.nombre,
            _fmt_payout(ev.payout),
            _celda(ev.mejores["1"]),
            _celda(ev.mejores["X"]),
            _celda(ev.mejores["2"]),
        ]
        for ev in evaluados
    ]

    anchos = [
        max(len(encabezados[col]), *(len(fila[col]) for fila in filas))
        for col in range(len(encabezados))
    ]

    def linea(campos: list[str]) -> str:
        return "  ".join(campo.ljust(anchos[col]) for col, campo in enumerate(campos))

    separador = "  ".join("-" * ancho for ancho in anchos)
    return "\n".join([linea(encabezados), separador, *(linea(fila) for fila in filas)])


def _payout_json(payout: Decimal | None) -> str | None:
    if payout is None:
        return None
    return str(payout.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _mejor_json(mejor: MejorCuota | None) -> dict:
    if mejor is None:
        return {"cuota": None, "casas": []}
    return {"cuota": str(mejor.cuota), "casas": list(mejor.casas)}


def _json_salida(evaluados: list[PartidoEvaluado]) -> str:
    """Serializa el resultado como JSON reutilizable (RF-18).

    Las cuotas y el payout van como string para no reintroducir `float`; un
    resultado sin cuota válida se representa con `cuota: null, casas: []`.
    """
    datos = {
        "version": 1,
        "partidos": [
            {
                "partido": ev.nombre,
                "payout": _payout_json(ev.payout),
                "incompleto": ev.incompleto,
                "mejores": {r: _mejor_json(ev.mejores[r]) for r in core.RESULTADOS},
            }
            for ev in evaluados
        ],
    }
    return json.dumps(datos, ensure_ascii=False, indent=2)


def _surebet(args: argparse.Namespace) -> int:
    inversion = _parsear_inversion(args.inversion)
    if inversion is None:
        print(
            f"Error: la inversión debe ser un número mayor que 0 (recibido {args.inversion!r}).",
            file=sys.stderr,
        )
        return 1

    try:
        partidos = storage.cargar_comparacion(args.archivo)
    except ErrorDatos as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    repartos = core.repartir(partidos, inversion)

    if args.json:
        print(_json_surebet(repartos, inversion))
    elif not repartos:
        print("No hay partidos que analizar.")
    else:
        print(_tabla_surebet(repartos, inversion))

    print(RECORDATORIO_CUOTAS, file=sys.stderr)
    return 0


def _parsear_inversion(texto: str) -> Decimal | None:
    """Convierte el argumento de inversión a `Decimal` > 0, o `None` si no vale."""
    try:
        valor = Decimal(texto)
    except InvalidOperation:
        return None
    if not valor.is_finite() or valor <= 0:
        return None
    return valor


def _dinero(valor: Decimal | None) -> str:
    if valor is None:
        return SIN_DATO
    return str(valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _estado(reparto: Reparto) -> str:
    if reparto.no_calculable:
        return "no calc."
    return "surebet" if reparto.surebet else "pérdida"


def _celda_pata(reparto: Reparto, resultado: str) -> str:
    if reparto.patas is None:
        return SIN_DATO
    pata = reparto.patas[resultado]
    return f"{_dinero(pata.importe)} {'/'.join(pata.casas)} ({pata.cuota})"


def _tabla_surebet(repartos: list[Reparto], inversion: Decimal) -> str:
    encabezados = ["Partido", "Estado", "% pago", "Retorno", "Beneficio", "1", "X", "2"]
    filas = [
        [
            r.nombre,
            _estado(r),
            _dinero(r.payout),
            _dinero(r.retorno),
            _dinero(r.beneficio),
            _celda_pata(r, "1"),
            _celda_pata(r, "X"),
            _celda_pata(r, "2"),
        ]
        for r in repartos
    ]

    anchos = [
        max(len(encabezados[col]), *(len(fila[col]) for fila in filas))
        for col in range(len(encabezados))
    ]

    def linea(campos: list[str]) -> str:
        return "  ".join(campo.ljust(anchos[col]) for col, campo in enumerate(campos))

    separador = "  ".join("-" * ancho for ancho in anchos)
    cabecera = f"Inversión por partido: {_dinero(inversion)} €"
    return "\n".join(
        [cabecera, "", linea(encabezados), separador, *(linea(fila) for fila in filas)]
    )


def _pata_json(reparto: Reparto, resultado: str) -> dict:
    pata = reparto.patas[resultado]
    return {
        "importe": _dinero(pata.importe),
        "cuota": str(pata.cuota),
        "casas": list(pata.casas),
    }


def _patas_json(reparto: Reparto) -> dict | None:
    if reparto.patas is None:
        return None
    return {r: _pata_json(reparto, r) for r in core.RESULTADOS}


def _json_surebet(repartos: list[Reparto], inversion: Decimal) -> str:
    """Serializa el reparto como JSON reutilizable (RF-15).

    Importes, retorno, beneficio y cuotas van como string para no reintroducir
    `float`; un partido no calculable lleva `retorno`, `beneficio` y `patas` a
    `null`.
    """
    datos = {
        "version": 1,
        "inversion": _dinero(inversion),
        "partidos": [
            {
                "partido": r.nombre,
                "payout": _dinero(r.payout) if r.payout is not None else None,
                "surebet": r.surebet,
                "no_calculable": r.no_calculable,
                "retorno": _dinero(r.retorno) if r.retorno is not None else None,
                "beneficio": _dinero(r.beneficio) if r.beneficio is not None else None,
                "patas": _patas_json(r),
            }
            for r in repartos
        ],
    }
    return json.dumps(datos, ensure_ascii=False, indent=2)


def _forzar_utf8() -> None:
    """Emite en UTF-8 aunque la consola use otra code page (evita mojibake y
    `UnicodeEncodeError` con acentos y con `—` en consolas Windows)."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8")
            except (ValueError, OSError):
                pass


def main(argv: list[str] | None = None) -> int:
    """Punto de entrada de la CLI. Devuelve el código de salida."""
    _forzar_utf8()
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)
