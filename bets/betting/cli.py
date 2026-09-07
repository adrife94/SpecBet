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
    compare.add_argument(
        "--promo",
        metavar="CASA[,CASA...]",
        help="Casas con la promo 'ventaja de 2 goles' (separadas por comas); "
        "posiciona las patas de ganar y muestra el impacto en el %% de pago.",
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
    surebet.add_argument(
        "--promo",
        metavar="CASA[,CASA...]",
        help="Casas con la promo 'ventaja de 2 goles'. Con --promo, surebet lee el "
        "Formato A (cuotas por casa), no la salida de 'compare --json'.",
    )
    surebet.set_defaults(func=_surebet)

    freebet = sub.add_parser(
        "freebet",
        help="Convierte una o varias freebets: dónde cubrir, cuánto, valor y % de conversión.",
    )
    freebet.add_argument(
        "archivo",
        help="Ruta al JSON de cuotas por casa (Formato A, el mismo que compare).",
    )
    freebet.add_argument("--casa", help="Casa que otorga la freebet (para un solo bono).")
    freebet.add_argument("--importe", help="Importe de la freebet (número mayor que 0).")
    freebet.add_argument(
        "--fecha-limite",
        dest="fecha_limite",
        metavar="FECHA",
        help="Fecha límite de la freebet (ISO 8601); descarta los partidos posteriores.",
    )
    freebet.add_argument(
        "--min", dest="cuota_min", metavar="CUOTA", help="Cuota mínima de la pata gratis."
    )
    freebet.add_argument(
        "--max", dest="cuota_max", metavar="CUOTA", help="Cuota máxima de la pata gratis."
    )
    freebet.add_argument("--partido", help="Fijar el partido de la pata gratis.")
    freebet.add_argument("--resultado", metavar="1|X|2", help="Fijar el resultado de la pata gratis.")
    freebet.add_argument(
        "--bonos",
        metavar="ARCHIVO",
        help="JSON con varios bonos (lote), en vez de --casa/--importe.",
    )
    freebet.add_argument(
        "--json",
        action="store_true",
        help="Emite el resultado como JSON reutilizable en vez de la tabla.",
    )
    freebet.add_argument(
        "--promo",
        metavar="CASA[,CASA...]",
        help="Casas con la promo 'ventaja de 2 goles'; posiciona las coberturas de "
        "las patas de ganar (1/2) en esas casas y muestra coste y windfall.",
    )
    freebet.set_defaults(func=_freebet)

    bonus = sub.add_parser(
        "bonus",
        help="Apuesta de menor coste para cumplir el rollover de un bono (Caso 1).",
    )
    bonus.add_argument(
        "archivo",
        help="Ruta al JSON de cuotas por casa (Formato A, el mismo que compare).",
    )
    bonus.add_argument("--casa", help="Casa que da el bono.")
    bonus.add_argument("--importe", help="Importe a apostar con el bono (número mayor que 0).")
    bonus.add_argument(
        "--min",
        dest="cuota_minima",
        metavar="CUOTA",
        help="Cuota mínima exigida por el rollover (número mayor que 1).",
    )
    bonus.add_argument(
        "--fecha-limite",
        dest="fecha_limite",
        metavar="FECHA",
        help="Fecha límite del bono (ISO 8601); descarta los partidos posteriores.",
    )
    bonus.add_argument(
        "--json",
        action="store_true",
        help="Emite el resultado como JSON reutilizable en vez de la tabla.",
    )
    bonus.add_argument(
        "--promo",
        metavar="CASA[,CASA...]",
        help="Casas con la promo 'ventaja de 2 goles'; posiciona las coberturas de "
        "las patas de ganar (1/2) en esas casas y muestra coste y windfall.",
    )
    bonus.set_defaults(func=_bonus)

    multibonus = sub.add_parser(
        "multibonus",
        help="Rollover coordinado de 2 o 3 bonos: reparto, relleno con dinero real y pérdida.",
    )
    multibonus.add_argument(
        "archivo",
        help="Ruta al JSON de cuotas por casa (Formato A, el mismo que compare).",
    )
    multibonus.add_argument(
        "--bono",
        action="append",
        metavar="CASA:IMPORTE:MIN",
        help="Un bono: casa, importe y cuota mínima. Repite el flag 2 o 3 veces.",
    )
    multibonus.add_argument(
        "--bonos",
        metavar="ARCHIVO",
        help="JSON con los bonos (casa, importe, min), en vez de --bono.",
    )
    multibonus.add_argument(
        "--apalancamiento",
        metavar="FECHA",
        help="Fecha del partido de apalancamiento (ISO 8601); descarta los "
        "partidos que se saldan en esa fecha o después.",
    )
    multibonus.add_argument(
        "--json",
        action="store_true",
        help="Emite el resultado como JSON reutilizable en vez de la tabla.",
    )
    multibonus.set_defaults(func=_multibonus)
    return parser


def _compare(args: argparse.Namespace) -> int:
    try:
        partidos = storage.cargar(args.archivo)
        evaluados = core.comparar(partidos)
        filtro = _filtro_promo(args)
    except ErrorDatos as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    _avisar_descartes(evaluados)

    promo: list[dict] = []
    casas_promo: list[str] = []
    if filtro is not None:
        casas_promo = _parse_promo(args.promo)
        promo = _promo_compare(evaluados, partidos, filtro)

    if args.json:
        promo_map = _promo_map(promo, casas_promo) if filtro is not None else None
        print(_json_salida(evaluados, promo_map))
    elif not evaluados:
        print("No hay partidos que comparar.")
    else:
        print(_tabla(evaluados))
        if promo:
            print()
            print(_tabla_promo_compare(promo, casas_promo))

    if filtro is not None:
        print(RECORDATORIO_CUOTAS, file=sys.stderr)
    return 0


def _parse_promo(valor: str) -> list[str]:
    """Casas de --promo: separadas por comas, sin espacios ni vacías."""
    return [c.strip() for c in valor.split(",") if c.strip()]


def _filtro_promo(args: argparse.Namespace):
    """Construye el `FiltroPromo` desde --promo, o `None` si no se indicó (RF-2, RF-3)."""
    valor = getattr(args, "promo", None)
    if valor is None:
        return None
    return core.construir_filtro_promo(_parse_promo(valor))


def _promo_compare(evaluados, partidos, filtro) -> list[dict]:
    """Por cada partido completo, sus opciones de promo con el payout asegurado y su coste."""
    crudos = {core.normalizar(p["partido"]): p for p in partidos}
    registros: list[dict] = []
    for ev in evaluados:
        if ev.incompleto:
            continue
        raw = crudos.get(core.normalizar(ev.nombre))
        if raw is None:
            continue
        promo = core.opciones_promo(raw, filtro)
        if not promo.opciones:
            continue
        opciones = []
        for op in promo.opciones:
            pay = core.payout_asegurado(ev.mejores, op)
            coste = ev.payout - pay if (pay is not None and ev.payout is not None) else None
            opciones.append({"opcion": op, "payout": pay, "coste": coste})
        registros.append({"ev": ev, "promo": promo, "opciones": opciones})
    return registros


_NOMBRE_OPCION = {
    "asegurar_1": "asegurar 1",
    "asegurar_2": "asegurar 2",
    "asegurar_ambos": "asegurar ambos",
}


def _tabla_promo_compare(registros, casas) -> str:
    lineas = [f"Promo 'ventaja de 2 goles' (casas: {', '.join(casas)}):"]
    for reg in registros:
        ev = reg["ev"]
        lineas.append(f"  {ev.nombre}  (payout normal {_fmt_payout(ev.payout)} %)")
        for item in reg["opciones"]:
            op = item["opcion"]
            detalle = " · ".join(
                f"{p.resultado} @{p.cuota} {p.casa} (vs {p.cuota_referencia} {p.casa_referencia})"
                for p in op.patas
            )
            lineas.append(
                f"      {_NOMBRE_OPCION[op.nombre]}: payout {_fmt_payout(item['payout'])} % "
                f"(coste {_fmt_payout(item['coste'])} pp)  {detalle}"
            )
        for aviso in reg["promo"].avisos:
            lineas.append(f"      · {aviso}")
    return "\n".join(lineas)


def _promo_map(registros, casas) -> dict:
    """Bloque `promo` por partido para la salida JSON (RF-22)."""
    mapa: dict = {}
    for reg in registros:
        mapa[core.normalizar(reg["ev"].nombre)] = {
            "casas": casas,
            "opciones": [
                {
                    "nombre": item["opcion"].nombre,
                    "payout": _fmt_payout(item["payout"]),
                    "coste": _fmt_payout(item["coste"]),
                    "patas": [
                        {
                            "resultado": p.resultado,
                            "casa": p.casa,
                            "cuota": str(p.cuota),
                            "casa_referencia": p.casa_referencia,
                            "cuota_referencia": str(p.cuota_referencia),
                        }
                        for p in item["opcion"].patas
                    ],
                }
                for item in reg["opciones"]
            ],
            "avisos": reg["promo"].avisos,
        }
    return mapa


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


def _json_salida(evaluados: list[PartidoEvaluado], promo_map: dict | None = None) -> str:
    """Serializa el resultado como JSON reutilizable (RF-18, RF-22).

    Las cuotas y el payout van como string para no reintroducir `float`; un
    resultado sin cuota válida se representa con `cuota: null, casas: []`. Con el
    filtro de promo activo, cada partido con opciones lleva además un bloque
    `promo`.
    """
    partidos = []
    for ev in evaluados:
        partido = {
            "partido": ev.nombre,
            "payout": _payout_json(ev.payout),
            "incompleto": ev.incompleto,
            "mejores": {r: _mejor_json(ev.mejores[r]) for r in core.RESULTADOS},
        }
        if promo_map is not None:
            clave = core.normalizar(ev.nombre)
            if clave in promo_map:
                partido["promo"] = promo_map[clave]
        partidos.append(partido)
    return json.dumps({"version": 1, "partidos": partidos}, ensure_ascii=False, indent=2)


def _surebet(args: argparse.Namespace) -> int:
    inversion = _parsear_inversion(args.inversion)
    if inversion is None:
        print(
            f"Error: la inversión debe ser un número mayor que 0 (recibido {args.inversion!r}).",
            file=sys.stderr,
        )
        return 1

    try:
        filtro = _filtro_promo(args)
        if filtro is not None:
            partidos_raw = storage.cargar(args.archivo)
            core.verificar_duplicados(partidos_raw)
            comparados = [_a_comparado(core.evaluar_partido(p)) for p in partidos_raw]
        else:
            partidos_raw = None
            comparados = storage.cargar_comparacion(args.archivo)
    except ErrorDatos as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    repartos = core.repartir(comparados, inversion)
    promo = (
        _promo_surebet(repartos, comparados, partidos_raw, filtro, inversion)
        if filtro is not None
        else []
    )

    if args.json:
        promo_map = _promo_surebet_map(promo) if filtro is not None else None
        print(_json_surebet(repartos, inversion, promo_map))
    elif not repartos:
        print("No hay partidos que analizar.")
    else:
        print(_tabla_surebet(repartos, inversion))
        if promo:
            print()
            print(_tabla_promo_surebet(promo))

    print(RECORDATORIO_CUOTAS, file=sys.stderr)
    return 0


def _a_comparado(ev: PartidoEvaluado) -> dict:
    """Convierte un `PartidoEvaluado` al formato que consume `repartir_partido`."""
    return {
        "partido": ev.nombre,
        "payout": ev.payout,
        "incompleto": ev.incompleto,
        "mejores": {
            r: (
                {"cuota": ev.mejores[r].cuota, "casas": list(ev.mejores[r].casas)}
                if ev.mejores[r] is not None
                else {"cuota": None, "casas": []}
            )
            for r in core.RESULTADOS
        },
    }


def _comparado_asegurado(comparado: dict, opcion) -> dict:
    """Copia del comparado con las patas aseguradas puestas en su casa de promo."""
    mejores = {r: dict(comparado["mejores"][r]) for r in core.RESULTADOS}
    for pata in opcion.patas:
        mejores[pata.resultado] = {"cuota": pata.cuota, "casas": [pata.casa]}
    return {**comparado, "mejores": mejores}


def _promo_surebet(repartos, comparados, partidos_raw, filtro, inversion) -> list[dict]:
    """Por cada partido calculable, rehace el reparto con cada opción de promo."""
    crudos = {core.normalizar(p["partido"]): p for p in partidos_raw}
    comp_map = {core.normalizar(c["partido"]): c for c in comparados}
    registros: list[dict] = []
    for base in repartos:
        if base.no_calculable:
            continue
        raw = crudos.get(core.normalizar(base.nombre))
        if raw is None:
            continue
        promo = core.opciones_promo(raw, filtro)
        if not promo.opciones:
            continue
        comparado = comp_map[core.normalizar(base.nombre)]
        opciones = []
        for op in promo.opciones:
            rep = core.repartir_partido(_comparado_asegurado(comparado, op), inversion)
            asegurados = {}
            for pata in op.patas:
                s = rep.patas[pata.resultado].importe
                asegurados[pata.resultado] = {
                    "coste": core.coste_promo(pata, s),
                    "windfall": core.windfall_promo(pata, s),
                    "cuota_referencia": pata.cuota_referencia,
                    "casa_referencia": pata.casa_referencia,
                }
            opciones.append({"opcion": op, "reparto": rep, "asegurados": asegurados})
        registros.append({"base": base, "opciones": opciones, "avisos": promo.avisos})
    return registros


def _tabla_promo_surebet(registros) -> str:
    lineas = ["Promo 'ventaja de 2 goles':"]
    for reg in registros:
        base = reg["base"]
        lineas.append(f"  {base.nombre}  (beneficio base {_dinero(base.beneficio)} €)")
        for item in reg["opciones"]:
            op = item["opcion"]
            rep = item["reparto"]
            aseg = item["asegurados"]
            lineas.append(f"      {_NOMBRE_OPCION[op.nombre]}  (beneficio {_dinero(rep.beneficio)} €):")
            for res in core.RESULTADOS:
                pata = rep.patas[res]
                extra = ""
                if res in aseg:
                    a = aseg[res]
                    extra = (
                        f"   [promo: coste {_dinero(a['coste'])} €, "
                        f"windfall {_dinero(a['windfall'])} €]"
                    )
                lineas.append(
                    f"          {res}  {_dinero(pata.importe)} € @{pata.cuota} "
                    f"{'/'.join(pata.casas)}{extra}"
                )
        for aviso in reg["avisos"]:
            lineas.append(f"      · {aviso}")
    return "\n".join(lineas)


def _promo_surebet_map(registros) -> dict:
    """Bloque `promo` por partido para la salida JSON de surebet (RF-22)."""
    mapa: dict = {}
    for reg in registros:
        opciones = []
        for item in reg["opciones"]:
            op = item["opcion"]
            rep = item["reparto"]
            aseg = item["asegurados"]
            patas = []
            for res in core.RESULTADOS:
                pata = rep.patas[res]
                entrada = {
                    "resultado": res,
                    "importe": _dinero(pata.importe),
                    "cuota": str(pata.cuota),
                    "casas": list(pata.casas),
                    "asegurada": res in aseg,
                }
                if res in aseg:
                    a = aseg[res]
                    entrada["coste"] = _dinero(a["coste"])
                    entrada["windfall"] = _dinero(a["windfall"])
                    entrada["casa_referencia"] = a["casa_referencia"]
                    entrada["cuota_referencia"] = str(a["cuota_referencia"])
                patas.append(entrada)
            opciones.append(
                {"nombre": op.nombre, "beneficio": _dinero(rep.beneficio), "patas": patas}
            )
        mapa[core.normalizar(reg["base"].nombre)] = {"opciones": opciones, "avisos": reg["avisos"]}
    return mapa


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


def _json_surebet(repartos: list[Reparto], inversion: Decimal, promo_map: dict | None = None) -> str:
    """Serializa el reparto como JSON reutilizable (RF-15, RF-22).

    Importes, retorno, beneficio y cuotas van como string para no reintroducir
    `float`; un partido no calculable lleva `retorno`, `beneficio` y `patas` a
    `null`. Con el filtro de promo activo, cada partido con opciones lleva `promo`.
    """
    partidos = []
    for r in repartos:
        partido = {
            "partido": r.nombre,
            "payout": _dinero(r.payout) if r.payout is not None else None,
            "surebet": r.surebet,
            "no_calculable": r.no_calculable,
            "retorno": _dinero(r.retorno) if r.retorno is not None else None,
            "beneficio": _dinero(r.beneficio) if r.beneficio is not None else None,
            "patas": _patas_json(r),
        }
        if promo_map is not None:
            clave = core.normalizar(r.nombre)
            if clave in promo_map:
                partido["promo"] = promo_map[clave]
        partidos.append(partido)
    datos = {"version": 1, "inversion": _dinero(inversion), "partidos": partidos}
    return json.dumps(datos, ensure_ascii=False, indent=2)


def _freebet(args: argparse.Namespace) -> int:
    try:
        partidos = storage.cargar(args.archivo)
        core.verificar_duplicados(partidos)
        bonos = _construir_bonos(args)
        filtro = _filtro_promo(args)
    except ErrorDatos as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    if bonos is None:
        print(
            "Error: indica un bono con --casa e --importe, o un lote con --bonos.",
            file=sys.stderr,
        )
        return 1

    lote = core.evaluar_lote(partidos, bonos)
    promo = _promo_freebet(lote, partidos, filtro) if filtro is not None else []

    if args.json:
        print(_json_freebet(lote, _promo_freebet_map(promo) if filtro is not None else None))
    elif not partidos:
        print("No hay partidos que analizar.")
    else:
        print(_tabla_freebet(lote))
        if promo:
            print()
            print(_tabla_promo_freebet(promo))

    _avisar_freebet(lote)
    print(RECORDATORIO_CUOTAS, file=sys.stderr)
    return 0


def _promo_freebet(lote, partidos, filtro) -> list[dict]:
    """Por cada jugada jugable, posiciona sus coberturas de patas de ganar (1/2)
    en casas de la promo (≠ casa del bono), con coste y windfall (RF-20)."""
    crudos = {core.normalizar(p["partido"]): p for p in partidos}
    registros: list[dict] = []
    for resultado in lote.resultados:
        casa_bono = resultado.bono.casa
        for ev in resultado.partidos:
            if not ev.jugable:
                continue
            raw = crudos.get(core.normalizar(ev.partido))
            if raw is None:
                continue
            opciones = []
            for pata in ev.jugada.patas:
                if pata.tipo != "cobertura" or pata.resultado not in ("1", "2"):
                    continue
                pos = core.posicion_promo_cobertura(raw, pata.resultado, filtro, casa_bono)
                if pos is None:
                    continue
                cuota_promo, casa_promo = pos
                retorno = pata.importe * pata.cuota  # la cobertura devuelve este importe
                s = retorno / cuota_promo  # stake para devolver lo mismo en la casa de promo
                pp = core.PataPromo(pata.resultado, casa_promo, cuota_promo, pata.casa, pata.cuota)
                opciones.append(
                    {
                        "resultado": pata.resultado,
                        "casa": casa_promo,
                        "cuota": cuota_promo,
                        "importe": s,
                        "casa_referencia": pata.casa,
                        "cuota_referencia": pata.cuota,
                        "coste": core.coste_promo(pp, s),
                        "windfall": core.windfall_promo(pp, s),
                    }
                )
            if opciones:
                registros.append(
                    {
                        "bono": casa_bono,
                        "partido": ev.partido,
                        "recomendada": resultado.recomendada is ev,
                        "opciones": opciones,
                        "acumulable": len(opciones) == 2,
                    }
                )
    return registros


def _tabla_promo_freebet(registros) -> str:
    lineas = ["Promo 'ventaja de 2 goles' (coberturas de patas de ganar):"]
    for reg in registros:
        marca = " ★" if reg["recomendada"] else ""
        lineas.append(f"  {reg['bono']} — {reg['partido']}{marca}")
        for op in reg["opciones"]:
            lineas.append(
                f"      cobertura {op['resultado']}: {_eur(op['importe'])} € @{op['cuota']} "
                f"{op['casa']} (ref {op['cuota_referencia']} {op['casa_referencia']})  "
                f"coste {_eur(op['coste'])} €  windfall {_eur(op['windfall'])} €"
            )
        if reg["acumulable"]:
            lineas.append("      · los dos windfalls pueden acumularse")
    return "\n".join(lineas)


def _promo_freebet_map(registros) -> dict:
    """Bloque `promo` por (bono, partido) para la salida JSON (RF-22)."""
    mapa: dict = {}
    for reg in registros:
        clave = (core.normalizar(reg["bono"]), core.normalizar(reg["partido"]))
        mapa[clave] = {
            "coberturas": [
                {
                    "resultado": op["resultado"],
                    "casa": op["casa"],
                    "cuota": str(op["cuota"]),
                    "importe": _eur(op["importe"]),
                    "casa_referencia": op["casa_referencia"],
                    "cuota_referencia": str(op["cuota_referencia"]),
                    "coste": _eur(op["coste"]),
                    "windfall": _eur(op["windfall"]),
                }
                for op in reg["opciones"]
            ],
            "acumulable": reg["acumulable"],
        }
    return mapa


def _construir_bonos(args: argparse.Namespace) -> list | None:
    """Construye la lista de bonos desde `--bonos` o desde los flags de un bono.

    Devuelve `None` si no se indicó ni un bono (--casa) ni un lote (--bonos), para
    que la CLI lo traduzca al error de RF-18.
    """
    if args.bonos is not None:
        if args.casa is not None:
            raise ErrorDatos("Usa --bonos (lote) o --casa (un bono), no ambos.")
        return [core.construir_bono(dato) for dato in storage.cargar_bonos(args.bonos)]

    if args.casa is None and args.importe is None:
        return None

    dato: dict = {"casa": args.casa, "importe": args.importe}
    if args.fecha_limite is not None:
        dato["fecha_limite"] = args.fecha_limite
    if args.cuota_min is not None:
        dato["min"] = args.cuota_min
    if args.cuota_max is not None:
        dato["max"] = args.cuota_max
    if args.partido is not None:
        dato["partido"] = args.partido
    if args.resultado is not None:
        dato["resultado"] = args.resultado
    return [core.construir_bono(dato)]


def _eur(valor: Decimal | None) -> str:
    if valor is None:
        return SIN_DATO
    return str(valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _pct(valor: Decimal | None) -> str:
    if valor is None:
        return SIN_DATO
    return str((valor * 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _bloque_partido(ev, es_recomendada: bool) -> list[str]:
    marca = "★" if es_recomendada else " "
    fecha = ev.fecha if ev.fecha else SIN_DATO
    if not ev.jugable:
        return [f"  {marca} {ev.partido} ({fecha})  no jugable: {ev.motivo}"]
    jugada = ev.jugada
    lineas = [
        f"  {marca} {ev.partido} ({fecha})  valor {_eur(jugada.valor_extraido)} €  "
        f"conversión {_pct(jugada.conversion)} %"
    ]
    for pata in jugada.patas:
        etiqueta = "gratis   " if pata.tipo == "gratis" else "cobertura"
        lineas.append(
            f"        {etiqueta} {pata.resultado}  {_eur(pata.importe)} € @{pata.cuota}  {pata.casa}"
        )
    return lineas


def _tabla_freebet(lote) -> str:
    lineas: list[str] = []
    for resultado in lote.resultados:
        cabecera = f"Bono: {resultado.bono.casa} — {_eur(resultado.bono.importe)} €"
        if resultado.bono.fecha_limite is not None:
            cabecera += f" (límite {resultado.bono.fecha_limite.date().isoformat()})"
        if resultado.sin_plan:
            cabecera += "  [sin plan]"
        lineas.append(cabecera)
        for ev in resultado.partidos:
            lineas.extend(_bloque_partido(ev, resultado.recomendada is ev))
        lineas.append("")
    lineas.append(
        f"Valor total del lote: {_eur(lote.valor_total)} €  "
        f"(conversión total {_pct(lote.conversion_total)} %)"
    )
    return "\n".join(lineas)


def _avisar_freebet(lote) -> None:
    """Avisos por stderr: partidos sin fecha con límite (RF-26) y colisiones (RF-31)."""
    for resultado in lote.resultados:
        for ev in resultado.partidos:
            if ev.aviso_sin_fecha:
                print(
                    f"Aviso: '{ev.partido}' no tiene fecha; no se pudo comprobar el plazo "
                    f"del bono de '{resultado.bono.casa}'.",
                    file=sys.stderr,
                )
    for colision in lote.colisiones:
        print(
            f"Aviso: dos bonos coinciden en {colision.partido} / {colision.resultado} @ "
            f"{colision.casa}; puedes consolidar esa apuesta.",
            file=sys.stderr,
        )


def _pata_freebet_json(pata) -> dict:
    return {
        "tipo": pata.tipo,
        "resultado": pata.resultado,
        "importe": _eur(pata.importe),
        "cuota": str(pata.cuota),
        "casa": pata.casa,
    }


def _evalpartido_json(ev) -> dict:
    return {
        "partido": ev.partido,
        "fecha": ev.fecha,
        "jugable": ev.jugable,
        "motivo": ev.motivo,
        "aviso_sin_fecha": ev.aviso_sin_fecha,
        "valor_extraido": _eur(ev.jugada.valor_extraido) if ev.jugada else None,
        "conversion": _pct(ev.jugada.conversion) if ev.jugada else None,
        "patas": [_pata_freebet_json(p) for p in ev.jugada.patas] if ev.jugada else None,
    }


def _json_freebet(lote, promo_map: dict | None = None) -> str:
    """Serializa el lote como JSON reutilizable (RF-21, RF-22).

    Importes, cuotas, valor y % van como string para no reintroducir `float`; un
    partido no jugable lleva `patas`, `valor_extraido` y `conversion` a `null`. Con
    el filtro de promo activo, cada partido con coberturas de ganar aseguradas lleva
    un bloque `promo`.
    """
    bonos = []
    for resultado in lote.resultados:
        partidos = []
        for ev in resultado.partidos:
            partido = _evalpartido_json(ev)
            if promo_map is not None:
                clave = (core.normalizar(resultado.bono.casa), core.normalizar(ev.partido))
                if clave in promo_map:
                    partido["promo"] = promo_map[clave]
            partidos.append(partido)
        bonos.append(
            {
                "casa": resultado.bono.casa,
                "importe": _eur(resultado.bono.importe),
                "sin_plan": resultado.sin_plan,
                "recomendada": resultado.recomendada.partido if resultado.recomendada else None,
                "partidos": partidos,
            }
        )
    datos = {
        "version": 1,
        "valor_total": _eur(lote.valor_total),
        "conversion_total": _pct(lote.conversion_total) if lote.conversion_total is not None else None,
        "bonos": bonos,
        "colisiones": [
            {"partido": c.partido, "resultado": c.resultado, "casa": c.casa}
            for c in lote.colisiones
        ],
    }
    return json.dumps(datos, ensure_ascii=False, indent=2)


def _bonus(args: argparse.Namespace) -> int:
    try:
        partidos = storage.cargar(args.archivo)
        core.verificar_duplicados(partidos)
        config = core.construir_config_bonus(
            {
                "casa": args.casa,
                "importe": args.importe,
                "cuota_minima": args.cuota_minima,
                "fecha_limite": args.fecha_limite,
            }
        )
        filtro = _filtro_promo(args)
    except ErrorDatos as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    resultado = core.evaluar_bonus(partidos, config)
    promo = _promo_bonus(resultado, partidos, filtro) if filtro is not None else []

    if args.json:
        print(_json_bonus(resultado, _promo_bonus_map(promo) if filtro is not None else None))
    elif not partidos:
        print("No hay partidos que analizar.")
    elif not resultado.opciones:
        print("No hay opciones válidas para este bono.")
        if resultado.descartes:
            print(_descartes_texto(resultado.descartes))
    else:
        print(_tabla_bonus(resultado))
        if promo:
            print()
            print(_tabla_promo_bonus(promo))

    _avisar_bonus(resultado)
    print(RECORDATORIO_CUOTAS, file=sys.stderr)
    return 0


def _promo_bonus(resultado, partidos, filtro) -> list[dict]:
    """Por cada opción del bono, posiciona sus coberturas de patas de ganar (1/2)
    en casas de la promo (≠ casa del bono), con coste y windfall (RF-21)."""
    casa_bono = resultado.config.casa
    crudos = {core.normalizar(p["partido"]): p for p in partidos}
    registros: list[dict] = []
    for opcion in resultado.opciones:
        raw = crudos.get(core.normalizar(opcion.partido))
        if raw is None:
            continue
        coberturas = []
        for cob in opcion.coberturas:
            if cob.resultado not in ("1", "2"):
                continue
            pos = core.posicion_promo_cobertura(raw, cob.resultado, filtro, casa_bono)
            if pos is None:
                continue
            cuota_promo, casa_promo = pos
            retorno = cob.importe * cob.cuota
            s = retorno / cuota_promo
            pp = core.PataPromo(cob.resultado, casa_promo, cuota_promo, cob.casa, cob.cuota)
            coberturas.append(
                {
                    "resultado": cob.resultado,
                    "casa": casa_promo,
                    "cuota": cuota_promo,
                    "importe": s,
                    "casa_referencia": cob.casa,
                    "cuota_referencia": cob.cuota,
                    "coste": core.coste_promo(pp, s),
                    "windfall": core.windfall_promo(pp, s),
                }
            )
        if coberturas:
            registros.append(
                {
                    "partido": opcion.partido,
                    "anclado": opcion.resultado,
                    "opciones": coberturas,
                    "acumulable": len(coberturas) == 2,
                }
            )
    return registros


def _tabla_promo_bonus(registros) -> str:
    lineas = ["Promo 'ventaja de 2 goles' (coberturas de patas de ganar):"]
    for reg in registros:
        lineas.append(f"  {reg['partido']} — anclado en {reg['anclado']}")
        for op in reg["opciones"]:
            lineas.append(
                f"      cobertura {op['resultado']}: {_eur(op['importe'])} € @{op['cuota']} "
                f"{op['casa']} (ref {op['cuota_referencia']} {op['casa_referencia']})  "
                f"coste {_eur(op['coste'])} €  windfall {_eur(op['windfall'])} €"
            )
        if reg["acumulable"]:
            lineas.append("      · los dos windfalls pueden acumularse")
    return "\n".join(lineas)


def _promo_bonus_map(registros) -> dict:
    """Bloque `promo` por (partido, resultado anclado) para la salida JSON (RF-22)."""
    mapa: dict = {}
    for reg in registros:
        clave = (core.normalizar(reg["partido"]), reg["anclado"])
        mapa[clave] = {
            "coberturas": [
                {
                    "resultado": op["resultado"],
                    "casa": op["casa"],
                    "cuota": str(op["cuota"]),
                    "importe": _eur(op["importe"]),
                    "casa_referencia": op["casa_referencia"],
                    "cuota_referencia": str(op["cuota_referencia"]),
                    "coste": _eur(op["coste"]),
                    "windfall": _eur(op["windfall"]),
                }
                for op in reg["opciones"]
            ],
            "acumulable": reg["acumulable"],
        }
    return mapa


def _descartes_texto(descartes) -> str:
    lineas = ["Descartados:"]
    for d in descartes:
        etiqueta = d.partido if d.resultado is None else f"{d.partido} / {d.resultado}"
        lineas.append(f"  - {etiqueta}: {d.motivo}")
    return "\n".join(lineas)


def _tabla_bonus(resultado) -> str:
    config = resultado.config
    cabecera = (
        f"Bono: {config.casa} — apuesta {_eur(config.importe)} € "
        f"(cuota mínima {_eur(config.cuota_minima)})"
    )
    if config.fecha_limite is not None:
        cabecera += f" [límite {config.fecha_limite.date().isoformat()}]"
    lineas = [cabecera, "", "Opciones (de menor a mayor coste):"]
    for opcion in resultado.opciones:
        lineas.append(
            f"  {opcion.partido} — anclar {opcion.resultado} @{opcion.cuota} en {opcion.casa}  "
            f"coste {_eur(opcion.coste)} €"
        )
        for cobertura in opcion.coberturas:
            lineas.append(
                f"      cobertura {cobertura.resultado}  {_eur(cobertura.importe)} € "
                f"@{cobertura.cuota}  {cobertura.casa}"
            )
    if resultado.descartes:
        lineas.append("")
        lineas.append(_descartes_texto(resultado.descartes))
    return "\n".join(lineas)


def _avisar_bonus(resultado) -> None:
    """Avisa por stderr de los partidos sin fecha cuando hay fecha límite (RF-16)."""
    for nombre in resultado.avisos_sin_fecha:
        print(
            f"Aviso: '{nombre}' no tiene fecha; no se pudo comprobar el plazo del bono.",
            file=sys.stderr,
        )


def _json_bonus(resultado, promo_map: dict | None = None) -> str:
    """Serializa las opciones del bono como JSON reutilizable (RF-25, RF-22).

    Con el filtro de promo activo, cada opción con coberturas de ganar aseguradas
    lleva un bloque `promo`.
    """
    config = resultado.config
    opciones = []
    for opcion in resultado.opciones:
        dato = {
            "partido": opcion.partido,
            "resultado": opcion.resultado,
            "cuota": str(opcion.cuota),
            "importe": _eur(opcion.importe),
            "casa": opcion.casa,
            "coste": _eur(opcion.coste),
            "cobertura": [
                {
                    "resultado": cobertura.resultado,
                    "importe": _eur(cobertura.importe),
                    "cuota": str(cobertura.cuota),
                    "casa": cobertura.casa,
                }
                for cobertura in opcion.coberturas
            ],
        }
        if promo_map is not None:
            clave = (core.normalizar(opcion.partido), opcion.resultado)
            if clave in promo_map:
                dato["promo"] = promo_map[clave]
        opciones.append(dato)
    datos = {
        "version": 1,
        "casa": config.casa,
        "importe": _eur(config.importe),
        "cuota_minima": _eur(config.cuota_minima),
        "opciones": opciones,
        "descartes": [
            {"partido": d.partido, "resultado": d.resultado, "motivo": d.motivo}
            for d in resultado.descartes
        ],
    }
    return json.dumps(datos, ensure_ascii=False, indent=2)


def _multibonus(args: argparse.Namespace) -> int:
    try:
        partidos = storage.cargar(args.archivo)
        core.verificar_duplicados(partidos)
        datos = _datos_bonos_multi(args)
        config = core.construir_config_multi(datos, args.apalancamiento)
    except ErrorDatos as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    resultado = core.evaluar_multibono(partidos, config)

    if args.json:
        print(_json_multibono(resultado))
    elif not partidos:
        print("No hay partidos que analizar.")
    elif not resultado.opciones:
        print("No hay opciones válidas para el multibono.")
        if resultado.descartes:
            print(_descartes_texto(resultado.descartes))
    else:
        print(_tabla_multibono(resultado))

    _avisar_multibono(resultado)
    print(RECORDATORIO_CUOTAS, file=sys.stderr)
    return 0


def _datos_bonos_multi(args: argparse.Namespace) -> list[dict]:
    """Lista de dicts de bono desde --bono (repetible) o --bonos (archivo).

    El número de bonos (2 o 3) y su validez los comprueba `construir_config_multi`.
    """
    if args.bonos is not None:
        if args.bono:
            raise ErrorDatos("Usa --bono (uno o varios) o --bonos (archivo), no ambos.")
        return storage.cargar_bonos(args.bonos)
    if not args.bono:
        raise ErrorDatos(
            "Indica los bonos con --bono CASA:IMPORTE:MIN (2 o 3 veces) o con --bonos ARCHIVO."
        )
    return [_parsear_bono_flag(v) for v in args.bono]


def _parsear_bono_flag(valor: str) -> dict:
    """Interpreta un --bono con formato CASA:IMPORTE:MIN."""
    partes = valor.split(":")
    if len(partes) != 3:
        raise ErrorDatos(
            f"El bono '{valor}' no tiene el formato CASA:IMPORTE:MIN (p. ej. Luckia:100:1.5)."
        )
    casa, importe, minimo = (p.strip() for p in partes)
    return {"casa": casa, "importe": importe, "cuota_minima": minimo}


def _tabla_multibono(resultado) -> str:
    config = resultado.config
    lineas = [f"Multibono: {len(config.bonos)} bonos"]
    for bono in config.bonos:
        lineas.append(
            f"  - {bono.casa}: {_eur(bono.importe)} € (cuota mínima {_eur(bono.cuota_minima)})"
        )
    if config.fecha_apalancamiento is not None:
        lineas.append(f"  Apalancamiento: {config.fecha_apalancamiento.date().isoformat()}")
    lineas += ["", "Opciones (de menor a mayor pérdida):"]
    for opcion in resultado.opciones:
        lineas.append(
            f"  {opcion.partido} — pérdida {_eur(opcion.perdida)} € ({_eur(opcion.perdida_pct)} %)  "
            f"dinero real {_eur(opcion.dinero_real)} €  retorno {_eur(opcion.retorno)} €  "
            f"neto {_eur(opcion.neto)} €"
        )
        for pata in opcion.patas:
            etiqueta = "bono   " if pata.tipo == "bono" else "relleno"
            lineas.append(
                f"      {etiqueta} {pata.resultado}  {_eur(pata.importe)} € @{pata.cuota}  {pata.casa}"
            )
    if resultado.descartes:
        lineas += ["", _descartes_texto(resultado.descartes)]
    return "\n".join(lineas)


def _avisar_multibono(resultado) -> None:
    """Avisa por stderr de los partidos sin fecha cuando hay apalancamiento (RF-27)."""
    for nombre in resultado.avisos_sin_fecha:
        print(
            f"Aviso: '{nombre}' no tiene fecha; no se pudo comprobar el plazo del apalancamiento.",
            file=sys.stderr,
        )


def _json_multibono(resultado) -> str:
    """Serializa las opciones del multibono como JSON reutilizable (RF-30)."""
    config = resultado.config
    datos = {
        "version": 1,
        "bonos": [
            {"casa": b.casa, "importe": _eur(b.importe), "cuota_minima": _eur(b.cuota_minima)}
            for b in config.bonos
        ],
        "opciones": [
            {
                "partido": opcion.partido,
                "R": _eur(opcion.retorno),
                "dinero_real": _eur(opcion.dinero_real),
                "perdida": _eur(opcion.perdida),
                "perdida_pct": _eur(opcion.perdida_pct),
                "neto": _eur(opcion.neto),
                "patas": [
                    {
                        "tipo": pata.tipo,
                        "resultado": pata.resultado,
                        "importe": _eur(pata.importe),
                        "cuota": str(pata.cuota),
                        "casa": pata.casa,
                    }
                    for pata in opcion.patas
                ],
            }
            for opcion in resultado.opciones
        ],
        "descartes": [{"partido": d.partido, "motivo": d.motivo} for d in resultado.descartes],
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
