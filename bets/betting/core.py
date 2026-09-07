"""Lógica pura del comparador de cuotas (sin IO, testeable sin la CLI)."""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation

from betting.storage import ErrorDatos

RESULTADOS: tuple[str, ...] = ("1", "X", "2")


@dataclass(frozen=True)
class MejorCuota:
    """La mejor cuota de un resultado y todas las casas que la ofrecen (RF-4, RF-5)."""

    cuota: Decimal
    casas: tuple[str, ...]


@dataclass(frozen=True)
class Descartada:
    """Una cuota inválida ignorada, para poder avisar de ella (RF-8)."""

    partido: str
    casa: str
    resultado: str
    valor: object


@dataclass
class PartidoEvaluado:
    """Resultado del comparador para un partido.

    `payout` va sin redondear (el redondeo a 2 decimales es cosa de la
    presentación) y es `None` cuando el partido es incompleto.
    """

    nombre: str
    mejores: dict[str, MejorCuota | None]
    incompleto: bool
    payout: Decimal | None
    descartes: list[Descartada]


def normalizar(nombre: str) -> str:
    """Clave para comparar nombres de casa o partido.

    Ignora mayúsculas/minúsculas y recorta los espacios exteriores; los
    espacios interiores se conservan (RF-13). Se usa solo para agrupar y
    detectar repetidos: el nombre original se conserva aparte para mostrarlo.
    """
    return nombre.strip().casefold()


def verificar_duplicados(partidos: list[dict]) -> None:
    """Aborta si hay partidos o casas repetidos (RF-15, RF-16).

    Un partido repetido en el archivo, o una misma casa repetida dentro de un
    partido (comparando con `normalizar`), lanza `ErrorDatos` identificando el
    conflicto. La CLI lo traducirá a un código de salida distinto de 0.
    """
    vistos: dict[str, str] = {}
    for partido in partidos:
        nombre = partido["partido"]
        clave = normalizar(nombre)
        anterior = vistos.get(clave)
        if anterior is not None:
            raise ErrorDatos(
                f"El partido '{nombre}' aparece más de una vez "
                f"(coincide con '{anterior}')."
            )
        vistos[clave] = nombre
        _verificar_casas_unicas(nombre, partido["cuotas"])


def _verificar_casas_unicas(nombre_partido: str, cuotas: list[dict]) -> None:
    vistas: dict[str, str] = {}
    for entrada in cuotas:
        casa = entrada["casa"]
        clave = normalizar(casa)
        anterior = vistas.get(clave)
        if anterior is not None:
            raise ErrorDatos(
                f"La casa '{casa}' aparece más de una vez en el partido "
                f"'{nombre_partido}' (coincide con '{anterior}')."
            )
        vistas[clave] = casa


def _a_cuota_valida(valor: object) -> Decimal | None:
    """Devuelve la cuota como `Decimal` si es un número mayor que 1, o `None`."""
    if isinstance(valor, bool):
        return None
    if isinstance(valor, int):
        valor = Decimal(valor)
    if isinstance(valor, Decimal) and valor > 1:
        return valor
    return None


def mejores_de_partido(
    partido: dict,
) -> tuple[dict[str, MejorCuota | None], list[Descartada]]:
    """Calcula la mejor cuota de cada resultado 1/X/2 de un partido.

    Para cada resultado devuelve la cuota más alta entre las casas y todas las
    casas que la igualan (RF-2, RF-4, RF-5). Los huecos por casa se ignoran
    (RF-7). Las cuotas inválidas (no numéricas, ≤ 1, cero o negativas) se
    descartan y se acumulan aparte para poder avisar de ellas (RF-8); una clave
    ausente o `null` es un hueco y no genera aviso.
    """
    nombre = partido["partido"]
    candidatos: dict[str, list[tuple[str, Decimal]]] = {r: [] for r in RESULTADOS}
    descartes: list[Descartada] = []

    for entrada in partido["cuotas"]:
        casa = entrada["casa"]
        for resultado in RESULTADOS:
            if resultado not in entrada or entrada[resultado] is None:
                continue  # hueco (RF-7)
            cuota = _a_cuota_valida(entrada[resultado])
            if cuota is None:
                descartes.append(Descartada(nombre, casa, resultado, entrada[resultado]))
                continue  # cuota inválida descartada (RF-8)
            candidatos[resultado].append((casa, cuota))

    mejores: dict[str, MejorCuota | None] = {}
    for resultado in RESULTADOS:
        opciones = candidatos[resultado]
        if not opciones:
            mejores[resultado] = None
            continue
        tope = max(cuota for _, cuota in opciones)
        casas = tuple(casa for casa, cuota in opciones if cuota == tope)
        mejores[resultado] = MejorCuota(tope, casas)

    return mejores, descartes


def _casas_con_cuota_valida(partido: dict) -> set[str]:
    """Claves normalizadas de las casas que aportan al menos una cuota válida."""
    casas: set[str] = set()
    for entrada in partido["cuotas"]:
        for resultado in RESULTADOS:
            valor = entrada.get(resultado)
            if valor is not None and _a_cuota_valida(valor) is not None:
                casas.add(normalizar(entrada["casa"]))
                break
    return casas


def es_incompleto(partido: dict, mejores: dict[str, MejorCuota | None]) -> bool:
    """Indica si un partido no puede compararse (RF-9, RF-14).

    Es incompleto si algún resultado carece de cuota válida en toda casa
    (RF-9) o si menos de dos casas distintas aportan alguna cuota válida
    (RF-14). En ambos casos no se calculará su % de pago.
    """
    if any(mejores[resultado] is None for resultado in RESULTADOS):
        return True
    if len(_casas_con_cuota_valida(partido)) < 2:
        return True
    return False


def calcular_payout(mejores: dict[str, MejorCuota | None]) -> Decimal | None:
    """% de pago = 100 / (1/mejor_1 + 1/mejor_X + 1/mejor_2) (RF-3).

    Se calcula en `Decimal` a máxima precisión, sin redondear (el redondeo a
    2 decimales ocurre solo al presentar). Devuelve `None` si falta la mejor
    cuota de algún resultado.
    """
    if any(mejores[resultado] is None for resultado in RESULTADOS):
        return None
    inversa = sum(
        (Decimal(1) / mejores[resultado].cuota for resultado in RESULTADOS),
        Decimal(0),
    )
    return Decimal(100) / inversa


def evaluar_partido(partido: dict) -> PartidoEvaluado:
    """Evalúa un partido completo: mejores cuotas, incompleto, payout y descartes."""
    mejores, descartes = mejores_de_partido(partido)
    incompleto = es_incompleto(partido, mejores)
    payout = None if incompleto else calcular_payout(mejores)
    return PartidoEvaluado(
        nombre=partido["partido"],
        mejores=mejores,
        incompleto=incompleto,
        payout=payout,
        descartes=descartes,
    )


def ordenar(evaluados: list[PartidoEvaluado]) -> list[PartidoEvaluado]:
    """Ordena los partidos para mostrarlos (RF-6, RF-10, RF-17).

    Primero los completos, por % de pago descendente (orden estable ante
    empates); después los incompletos, en su orden de entrada. Los partidos con
    payout superior a 100 % no reciben ningún trato especial: se ordenan por su
    payout como cualquier otro (RF-17).
    """
    completos = [ev for ev in evaluados if not ev.incompleto]
    incompletos = [ev for ev in evaluados if ev.incompleto]
    completos.sort(key=lambda ev: ev.payout, reverse=True)
    return completos + incompletos


def comparar(partidos: list[dict]) -> list[PartidoEvaluado]:
    """Compara todos los partidos: verifica duplicados, evalúa y ordena."""
    verificar_duplicados(partidos)
    evaluados = [evaluar_partido(partido) for partido in partidos]
    return ordenar(evaluados)


# --- Spec 002: reparto de stake sobre arbitraje (surebet) ---


@dataclass(frozen=True)
class Pata:
    """Una pata del reparto: cuánto apostar a un resultado y en qué casa(s).

    `importe` va sin redondear (el redondeo a 2 decimales es cosa de la
    presentación). `casas` son todas las que ofrecen esa mejor cuota; el importe
    se apuesta íntegro en una cualquiera de ellas, no se divide (RF-8).
    """

    importe: Decimal
    cuota: Decimal
    casas: tuple[str, ...]


@dataclass
class Reparto:
    """Reparto de una inversión total entre los tres resultados de un partido.

    `retorno`, `beneficio` y `patas` van sin redondear y son `None` cuando el
    partido no es calculable (llegó incompleto del comparador). `payout` es el
    del comparador y solo se usa para mostrar; la señal `surebet` se decide por
    el signo del beneficio, calculado desde las cuotas exactas.
    """

    nombre: str
    no_calculable: bool
    surebet: bool
    payout: Decimal | None
    inversion: Decimal
    retorno: Decimal | None
    beneficio: Decimal | None
    patas: dict[str, Pata] | None


def repartir_partido(partido: dict, inversion: Decimal) -> Reparto:
    """Reparte `inversion` entre 1/X/2 igualando el retorno gane quien gane.

    Para cada resultado el importe es `inversion · (1/cuota) / Σ(1/cuota)`, de
    modo que `importe · cuota` (el retorno) es el mismo en los tres resultados
    (RF-2) y los tres importes suman la inversión (RF-3). El beneficio es
    `retorno − inversion`: positivo es surebet (RF-6), ≤ 0 es pérdida garantizada
    (RF-7). Un partido incompleto en la entrada no se reparte (RF-9).
    """
    mejores = partido["mejores"]
    cuotas = {r: mejores[r]["cuota"] for r in RESULTADOS}
    if partido["incompleto"] or any(cuotas[r] is None for r in RESULTADOS):
        return Reparto(
            nombre=partido["partido"],
            no_calculable=True,
            surebet=False,
            payout=partido["payout"],
            inversion=inversion,
            retorno=None,
            beneficio=None,
            patas=None,
        )

    inversa = sum((Decimal(1) / cuotas[r] for r in RESULTADOS), Decimal(0))
    retorno = inversion / inversa
    patas = {
        r: Pata(
            importe=inversion * (Decimal(1) / cuotas[r]) / inversa,
            cuota=cuotas[r],
            casas=tuple(mejores[r]["casas"]),
        )
        for r in RESULTADOS
    }
    beneficio = retorno - inversion
    return Reparto(
        nombre=partido["partido"],
        no_calculable=False,
        surebet=beneficio > 0,
        payout=partido["payout"],
        inversion=inversion,
        retorno=retorno,
        beneficio=beneficio,
        patas=patas,
    )


def ordenar_repartos(repartos: list[Reparto]) -> list[Reparto]:
    """Ordena por beneficio garantizado descendente; no calculables al final (RF-10).

    Entre los calculables el orden es estable ante empates de beneficio; los no
    calculables se dejan en su orden de entrada, después de todos los demás.
    """
    calculables = [r for r in repartos if not r.no_calculable]
    no_calculables = [r for r in repartos if r.no_calculable]
    calculables.sort(key=lambda r: r.beneficio, reverse=True)
    return calculables + no_calculables


def repartir(partidos: list[dict], inversion: Decimal) -> list[Reparto]:
    """Reparte la inversión en cada partido de forma independiente y los ordena."""
    repartos = [repartir_partido(partido, inversion) for partido in partidos]
    return ordenar_repartos(repartos)


# --- Spec 003: conversión de freebets (dónde cubrir y cuánto) ---


@dataclass(frozen=True)
class Bono:
    """Una freebet a convertir: casa que la otorga, importe y sus términos.

    `fecha_limite` es la fecha máxima para apostar/saldar; `cuota_min`/`cuota_max`
    acotan la cuota de la pata gratis; `partido`/`resultado` fijan la jugada si el
    usuario lo pide. Importes y cuotas en `Decimal`, fecha en `datetime`.
    """

    casa: str
    importe: Decimal
    fecha_limite: datetime | None = None
    cuota_min: Decimal | None = None
    cuota_max: Decimal | None = None
    partido: str | None = None
    resultado: str | None = None


def construir_bono(dato: dict) -> Bono:
    """Valida un bono (de `--bonos` o de los flags de la CLI) y lo normaliza.

    Comprueba que el importe sea un número mayor que 0 (RF-17), que el resultado
    fijado sea 1/X/2, que el rango de cuota sea coherente y que la fecha límite
    sea interpretable. Lanza `ErrorDatos` con un mensaje en español si algo falla.
    """
    casa = dato.get("casa")
    if not isinstance(casa, str) or not casa.strip():
        raise ErrorDatos("Un bono no tiene una 'casa' válida.")

    importe = _bono_decimal(dato.get("importe"), "importe", casa)
    if importe is None or importe <= 0:
        raise ErrorDatos(f"El importe del bono de '{casa}' debe ser un número mayor que 0.")

    cuota_min = _bono_decimal(dato.get("min"), "cuota mínima", casa)
    cuota_max = _bono_decimal(dato.get("max"), "cuota máxima", casa)
    if cuota_min is not None and cuota_max is not None and cuota_min > cuota_max:
        raise ErrorDatos(
            f"En el bono de '{casa}', la cuota mínima ({cuota_min}) supera a la máxima ({cuota_max})."
        )

    resultado = dato.get("resultado")
    if resultado is not None and resultado not in RESULTADOS:
        raise ErrorDatos(
            f"En el bono de '{casa}', el resultado fijado '{resultado}' no es 1, X ni 2."
        )

    partido = dato.get("partido")
    if partido is not None and (not isinstance(partido, str) or not partido.strip()):
        raise ErrorDatos(f"En el bono de '{casa}', el 'partido' fijado no es un nombre válido.")

    return Bono(
        casa=casa,
        importe=importe,
        fecha_limite=_parse_fecha(dato.get("fecha_limite"), f"la fecha límite del bono de '{casa}'"),
        cuota_min=cuota_min,
        cuota_max=cuota_max,
        partido=partido,
        resultado=resultado,
    )


def _bono_decimal(valor: object, campo: str, casa: str) -> Decimal | None:
    """Convierte a `Decimal` un número dado como int/Decimal/str; `None` se conserva."""
    if valor is None:
        return None
    if isinstance(valor, bool):
        raise ErrorDatos(f"En el bono de '{casa}', {campo} no es un número válido: {valor!r}.")
    if isinstance(valor, Decimal):
        return valor
    if isinstance(valor, int):
        return Decimal(valor)
    if isinstance(valor, str):
        try:
            return Decimal(valor)
        except InvalidOperation as exc:
            raise ErrorDatos(
                f"En el bono de '{casa}', {campo} no es un número válido: {valor!r}."
            ) from exc
    raise ErrorDatos(f"En el bono de '{casa}', {campo} no es un número válido: {valor!r}.")


def _parse_fecha(valor: object, contexto: str) -> datetime | None:
    """Interpreta una fecha ISO 8601 (date o datetime); `None` se conserva."""
    if valor is None:
        return None
    if not isinstance(valor, str):
        raise ErrorDatos(f"{contexto} debe ser una fecha en texto (ISO 8601).")
    try:
        return datetime.fromisoformat(valor)
    except ValueError as exc:
        raise ErrorDatos(f"{contexto} no es una fecha válida (usa ISO 8601): {valor!r}.") from exc


@dataclass(frozen=True)
class PataFreebet:
    """Una apuesta de la jugada: la freebet (`tipo="gratis"`) o una cobertura.

    `importe` va sin redondear; el importe de la pata gratis es el de la freebet.
    """

    tipo: str  # "gratis" | "cobertura"
    resultado: str
    importe: Decimal
    cuota: Decimal
    casa: str


@dataclass(frozen=True)
class Jugada:
    """Conversión de una freebet en un partido: sus patas y el valor que deja.

    `valor_extraido` es el beneficio neto garantizado (igual gane quien gane) y
    `conversion` es ese valor sobre el importe de la freebet. Ambos sin redondear.
    """

    partido: str
    resultado_gratis: str
    patas: tuple[PataFreebet, ...]
    valor_extraido: Decimal
    conversion: Decimal


def calcular_jugada(
    partido: str,
    importe: Decimal,
    resultado_gratis: str,
    cuota_gratis: Decimal,
    casa_bono: str,
    coberturas: dict[str, tuple[Decimal, str]],
) -> Jugada:
    """Reparte la cobertura de una freebet para igualar el beneficio neto (RF-2, RF-3).

    Con la freebet `importe` jugada al `resultado_gratis` a `cuota_gratis` en
    `casa_bono`, cubre los otros dos resultados con las cuotas/casas de
    `coberturas` de modo que el neto sea el mismo pase lo que pase: el retorno de
    cobertura común es `R = importe·(cuota_gratis−1)` y cada cobertura apuesta
    `R/cuota`. El valor extraído es `R` menos lo apostado en cobertura (RF-4).
    """
    retorno = importe * (cuota_gratis - Decimal(1))
    patas = [PataFreebet("gratis", resultado_gratis, importe, cuota_gratis, casa_bono)]
    for r in RESULTADOS:
        if r == resultado_gratis:
            continue
        cuota, casa = coberturas[r]
        patas.append(PataFreebet("cobertura", r, retorno / cuota, cuota, casa))

    invertido_cobertura = sum(
        (p.importe for p in patas if p.tipo == "cobertura"), Decimal(0)
    )
    valor_extraido = retorno - invertido_cobertura
    return Jugada(
        partido=partido,
        resultado_gratis=resultado_gratis,
        patas=tuple(patas),
        valor_extraido=valor_extraido,
        conversion=valor_extraido / importe,
    )


def _entrada_de_casa(partido: dict, casa_norm: str) -> dict | None:
    """La entrada de cuotas de una casa dentro de un partido, o `None` si no está."""
    for entrada in partido["cuotas"]:
        if normalizar(entrada["casa"]) == casa_norm:
            return entrada
    return None


def _en_rango(cuota: Decimal, bono: Bono) -> bool:
    """Comprueba que la cuota de la pata gratis esté dentro del rango del bono (RF-9)."""
    if bono.cuota_min is not None and cuota < bono.cuota_min:
        return False
    if bono.cuota_max is not None and cuota > bono.cuota_max:
        return False
    return True


def _mejor_cobertura(
    partido: dict, resultado: str, casa_bono_norm: str
) -> tuple[Decimal, str] | None:
    """Mejor cuota de un resultado entre las casas distintas de la del bono (RF-11, RF-12).

    Devuelve `(cuota, casa)` con la cuota más alta; ante empate, la primera por
    orden de entrada (determinista). `None` si ninguna casa distinta de la del
    bono ofrece una cuota válida para ese resultado (no cubrible, RF-13).
    """
    mejor: tuple[Decimal, str] | None = None
    for entrada in partido["cuotas"]:
        if normalizar(entrada["casa"]) == casa_bono_norm:
            continue
        cuota = _a_cuota_valida(entrada.get(resultado))
        if cuota is None:
            continue
        if mejor is None or cuota > mejor[0]:
            mejor = (cuota, entrada["casa"])
    return mejor


def _jugada_para_resultado(
    partido: dict, bono: Bono, casa_bono_norm: str, entrada_bono: dict, resultado_gratis: str
) -> Jugada | None:
    """Jugada de la freebet en un resultado concreto, o `None` si no es viable.

    No es viable si la casa del bono no ofrece cuota válida en ese resultado, si
    la cuota queda fuera del rango (RF-9) o si algún resultado a cubrir no tiene
    casa distinta de la del bono (RF-13).
    """
    cuota_gratis = _a_cuota_valida(entrada_bono.get(resultado_gratis))
    if cuota_gratis is None or not _en_rango(cuota_gratis, bono):
        return None
    coberturas: dict[str, tuple[Decimal, str]] = {}
    for r in RESULTADOS:
        if r == resultado_gratis:
            continue
        cobertura = _mejor_cobertura(partido, r, casa_bono_norm)
        if cobertura is None:
            return None
        coberturas[r] = cobertura
    return calcular_jugada(
        partido["partido"], bono.importe, resultado_gratis, cuota_gratis, entrada_bono["casa"], coberturas
    )


def mejor_jugada(partido: dict, bono: Bono) -> Jugada | None:
    """La jugada de mayor valor extraído de un bono en un partido (RF-6, RF-7).

    Sin resultado fijado prueba 1/X/2 y devuelve la de mayor valor extraído; con
    resultado fijado solo prueba ese. `None` si la casa del bono no está en el
    partido o ningún resultado da una jugada viable.
    """
    casa_norm = normalizar(bono.casa)
    entrada_bono = _entrada_de_casa(partido, casa_norm)
    if entrada_bono is None:
        return None
    resultados = [bono.resultado] if bono.resultado is not None else list(RESULTADOS)
    candidatas = [
        j
        for r in resultados
        if (j := _jugada_para_resultado(partido, bono, casa_norm, entrada_bono, r)) is not None
    ]
    if not candidatas:
        return None
    return max(candidatas, key=lambda j: j.valor_extraido)


@dataclass
class EvalPartido:
    """Un partido evaluado para un bono: su jugada o el motivo de no ser jugable."""

    partido: str
    fecha: str | None
    jugable: bool
    motivo: str | None
    jugada: Jugada | None
    aviso_sin_fecha: bool


@dataclass
class ResultadoBono:
    """El listado de partidos de un bono, ordenado, con su jugada recomendada.

    `valor_extraido` es el de la jugada recomendada (o `None` si no hay plan);
    `sin_plan` indica que ningún partido dio una jugada viable (RF-32).
    """

    bono: Bono
    partidos: list[EvalPartido]
    recomendada: EvalPartido | None
    valor_extraido: Decimal | None
    sin_plan: bool


def _motivo_no_jugable(partido: dict, bono: Bono) -> str:
    """Explica por qué un bono no tiene jugada en un partido (RF-10, RF-13, RF-14)."""
    casa_norm = normalizar(bono.casa)
    entrada = _entrada_de_casa(partido, casa_norm)
    if entrada is None:
        return f"La casa '{bono.casa}' no participa en este partido."
    if bono.resultado is not None:
        cuota = _a_cuota_valida(entrada.get(bono.resultado))
        if cuota is None:
            return f"La casa del bono no ofrece cuota válida para el resultado fijado ('{bono.resultado}')."
        if not _en_rango(cuota, bono):
            return f"La cuota del resultado fijado ('{bono.resultado}' = {cuota}) está fuera del rango."
        return f"El resultado fijado ('{bono.resultado}') no se puede cubrir en casa distinta a la del bono."
    return "Ningún resultado admite jugada (cuota fuera de rango o sin cobertura en casa distinta)."


def evaluar_partido_bono(partido: dict, bono: Bono) -> EvalPartido:
    """Evalúa un partido para un bono: plazo, jugada y motivo si no es jugable.

    Con fecha límite, un partido posterior es fuera de plazo (RF-24, RF-25) y uno
    sin fecha se evalúa igual pero con aviso (RF-26); sin fecha límite las fechas
    se ignoran (RF-27).
    """
    nombre = partido["partido"]
    fecha = partido.get("fecha")
    aviso_sin_fecha = False

    if bono.fecha_limite is not None:
        if fecha is None:
            aviso_sin_fecha = True
        else:
            fecha_partido = _parse_fecha(fecha, f"la fecha del partido '{nombre}'")
            if fecha_partido > bono.fecha_limite:
                return EvalPartido(
                    partido=nombre,
                    fecha=fecha,
                    jugable=False,
                    motivo="Se juega después de la fecha límite de la freebet (fuera de plazo).",
                    jugada=None,
                    aviso_sin_fecha=False,
                )

    jugada = mejor_jugada(partido, bono)
    if jugada is None:
        return EvalPartido(
            partido=nombre,
            fecha=fecha,
            jugable=False,
            motivo=_motivo_no_jugable(partido, bono),
            jugada=None,
            aviso_sin_fecha=aviso_sin_fecha,
        )
    return EvalPartido(
        partido=nombre,
        fecha=fecha,
        jugable=True,
        motivo=None,
        jugada=jugada,
        aviso_sin_fecha=aviso_sin_fecha,
    )


def evaluar_bono(partidos: list[dict], bono: Bono) -> ResultadoBono:
    """Evalúa un bono en todos los partidos, ordena y marca la recomendada.

    Los jugables van por valor extraído descendente (orden estable ante empates);
    los no jugables al final (RF-15). La recomendada es la primera jugable (RF-33).
    Si el bono fija un partido, solo se evalúa ese (RF-8).
    """
    if bono.partido is not None:
        clave = normalizar(bono.partido)
        partidos = [p for p in partidos if normalizar(p["partido"]) == clave]
    evals = [evaluar_partido_bono(partido, bono) for partido in partidos]
    jugables = [e for e in evals if e.jugable]
    no_jugables = [e for e in evals if not e.jugable]
    jugables.sort(key=lambda e: e.jugada.valor_extraido, reverse=True)
    recomendada = jugables[0] if jugables else None
    return ResultadoBono(
        bono=bono,
        partidos=jugables + no_jugables,
        recomendada=recomendada,
        valor_extraido=recomendada.jugada.valor_extraido if recomendada else None,
        sin_plan=not jugables,
    )


@dataclass(frozen=True)
class Colision:
    """Dos bonos recomiendan apostar en la misma apuesta (partido+resultado+casa)."""

    partido: str
    resultado: str
    casa: str


@dataclass
class ResultadoLote:
    """Resultado de evaluar un lote de bonos independientes (RF-28..RF-32).

    `valor_total` suma el valor extraído recomendado de cada bono (0 los que no
    tienen plan); `conversion_total` es ese valor sobre la suma de importes.
    """

    resultados: list[ResultadoBono]
    valor_total: Decimal
    conversion_total: Decimal | None
    colisiones: list[Colision]


def _detectar_colisiones(resultados: list[ResultadoBono]) -> list[Colision]:
    """Busca patas compartidas (partido+resultado+casa) entre jugadas recomendadas (RF-31)."""
    por_apuesta: dict[tuple[str, str, str], str] = {}
    repetidas: dict[tuple[str, str, str], str] = {}
    for resultado in resultados:
        if resultado.recomendada is None:
            continue
        for pata in resultado.recomendada.jugada.patas:
            clave = (resultado.recomendada.partido, pata.resultado, normalizar(pata.casa))
            if clave in por_apuesta:
                repetidas[clave] = por_apuesta[clave]
            else:
                por_apuesta[clave] = pata.casa
    return [
        Colision(partido=partido, resultado=resultado, casa=casa)
        for (partido, resultado, _casa_norm), casa in repetidas.items()
    ]


def evaluar_lote(partidos: list[dict], bonos: list[Bono]) -> ResultadoLote:
    """Evalúa cada bono del lote de forma independiente y agrega el total (RF-28..RF-32)."""
    resultados = [evaluar_bono(partidos, bono) for bono in bonos]
    valor_total = sum(
        (r.valor_extraido for r in resultados if r.valor_extraido is not None), Decimal(0)
    )
    importe_total = sum((bono.importe for bono in bonos), Decimal(0))
    conversion_total = valor_total / importe_total if importe_total > 0 else None
    return ResultadoLote(
        resultados=resultados,
        valor_total=valor_total,
        conversion_total=conversion_total,
        colisiones=_detectar_colisiones(resultados),
    )


# --- Spec 004: apuesta de menor coste para cumplir el rollover (bonus) ---


@dataclass(frozen=True)
class ConfigBonus:
    """Parámetros de un bono con rollover: casa, importe a apostar y cuota mínima.

    `cuota_minima` es la cuota mínima exigida para que la apuesta cuente;
    `fecha_limite` es el plazo opcional. Importe y cuota en `Decimal`.
    """

    casa: str
    importe: Decimal
    cuota_minima: Decimal
    fecha_limite: datetime | None = None


def construir_config_bonus(dato: dict) -> ConfigBonus:
    """Valida los parámetros del bono y los normaliza (RF-18, RF-19, RF-20).

    Exige casa indicada, importe mayor que 0 y cuota mínima mayor que 1, y una
    fecha límite interpretable si se da. Lanza `ErrorDatos` en español si falla.
    """
    casa = dato.get("casa")
    if not isinstance(casa, str) or not casa.strip():
        raise ErrorDatos("No se indicó la casa del bono.")

    importe = _bono_decimal(dato.get("importe"), "importe", casa)
    if importe is None or importe <= 0:
        raise ErrorDatos(f"El importe a apostar con el bono de '{casa}' debe ser mayor que 0.")

    cuota_minima = _bono_decimal(dato.get("cuota_minima"), "cuota mínima", casa)
    if cuota_minima is None or cuota_minima <= 1:
        raise ErrorDatos(f"La cuota mínima del bono de '{casa}' debe ser un número mayor que 1.")

    return ConfigBonus(
        casa=casa,
        importe=importe,
        cuota_minima=cuota_minima,
        fecha_limite=_parse_fecha(
            dato.get("fecha_limite"), f"la fecha límite del bono de '{casa}'"
        ),
    )


@dataclass(frozen=True)
class Cobertura:
    """Una pata de cobertura: cuánto apostar a un resultado y en qué casa."""

    resultado: str
    importe: Decimal
    cuota: Decimal
    casa: str


@dataclass(frozen=True)
class Opcion:
    """Anclar el bono en un resultado de un partido, con su cobertura y su coste.

    `coste` va sin redondear; es lo apostado (bono + coberturas) menos el retorno
    garantizado. Positivo es pérdida; negativo es arbitraje (RF-10).
    """

    partido: str
    resultado: str
    importe: Decimal
    cuota: Decimal
    casa: str
    coberturas: tuple[Cobertura, ...]
    coste: Decimal


def calcular_opcion(
    partido: str,
    resultado: str,
    importe: Decimal,
    cuota_bono: Decimal,
    casa_bono: str,
    coberturas: dict[str, tuple[Decimal, str]],
) -> Opcion:
    """Cubre los otros dos resultados igualando el retorno y calcula el coste.

    El retorno garantizado es `importe·cuota_bono`; cada cobertura apuesta
    `retorno/cuota` para devolver ese mismo retorno (RF-5). El coste es lo
    apostado (bono + coberturas) menos el retorno (RF-7).
    """
    retorno = importe * cuota_bono
    patas: list[Cobertura] = []
    total_cobertura = Decimal(0)
    for r in RESULTADOS:
        if r == resultado:
            continue
        cuota, casa = coberturas[r]
        stake = retorno / cuota
        total_cobertura += stake
        patas.append(Cobertura(r, stake, cuota, casa))
    coste = (importe + total_cobertura) - retorno
    return Opcion(partido, resultado, importe, cuota_bono, casa_bono, tuple(patas), coste)


@dataclass(frozen=True)
class Descarte:
    """Una opción o partido no propuesto y por qué (`resultado` None = todo el partido)."""

    partido: str
    resultado: str | None
    motivo: str


def _opciones_de_partido(partido: dict, config: ConfigBonus) -> tuple[list[Opcion], list[Descarte]]:
    """Opciones válidas de un partido y sus descartes (RF-2, RF-6, RF-11, RF-12, RF-13)."""
    casa_norm = normalizar(config.casa)
    entrada_bono = _entrada_de_casa(partido, casa_norm)
    if entrada_bono is None:
        motivo = f"La casa '{config.casa}' no participa en este partido."
        return [], [Descarte(partido["partido"], None, motivo)]

    opciones: list[Opcion] = []
    descartes: list[Descarte] = []
    for resultado in RESULTADOS:
        cuota = _a_cuota_valida(entrada_bono.get(resultado))
        if cuota is None or cuota < config.cuota_minima:
            continue  # sin cuota válida o bajo la mínima (RF-11): se omite sin ruido
        coberturas: dict[str, tuple[Decimal, str]] = {}
        cubrible = True
        for otro in RESULTADOS:
            if otro == resultado:
                continue
            cobertura = _mejor_cobertura(partido, otro, casa_norm)
            if cobertura is None:
                descartes.append(
                    Descarte(
                        partido["partido"],
                        resultado,
                        f"El resultado '{otro}' no se puede cubrir en casa distinta a la del bono.",
                    )
                )
                cubrible = False
                break
            coberturas[otro] = cobertura
        if not cubrible:
            continue
        opciones.append(
            calcular_opcion(
                partido["partido"], resultado, config.importe, cuota, entrada_bono["casa"], coberturas
            )
        )
    return opciones, descartes


@dataclass
class ResultadoBonus:
    """Opciones válidas de un bono (ordenadas por coste), descartes y avisos."""

    config: ConfigBonus
    opciones: list[Opcion]
    descartes: list[Descarte]
    avisos_sin_fecha: list[str]


def evaluar_bonus(partidos: list[dict], config: ConfigBonus) -> ResultadoBonus:
    """Genera todas las opciones del bono, aplica el plazo y las ordena por coste.

    Con fecha límite, un partido posterior se descarta (RF-15) y uno sin fecha se
    evalúa igual pero con aviso (RF-16); sin fecha límite las fechas se ignoran
    (RF-17). Todas las opciones válidas se ordenan por coste ascendente, con las
    de coste negativo (arbitraje) en el mismo orden (RF-9, RF-10).
    """
    opciones: list[Opcion] = []
    descartes: list[Descarte] = []
    avisos_sin_fecha: list[str] = []

    for partido in partidos:
        nombre = partido["partido"]
        fecha = partido.get("fecha")
        if config.fecha_limite is not None:
            if fecha is None:
                avisos_sin_fecha.append(nombre)
            else:
                fecha_partido = _parse_fecha(fecha, f"la fecha del partido '{nombre}'")
                if fecha_partido > config.fecha_limite:
                    descartes.append(
                        Descarte(
                            nombre,
                            None,
                            "Se juega después de la fecha límite del bono (fuera de plazo).",
                        )
                    )
                    continue

        opciones_partido, descartes_partido = _opciones_de_partido(partido, config)
        opciones.extend(opciones_partido)
        descartes.extend(descartes_partido)

    opciones.sort(key=lambda o: o.coste)
    return ResultadoBonus(config, opciones, descartes, avisos_sin_fecha)


# --- Spec 006: rollover coordinado de varios bonos (multibono) ---


@dataclass(frozen=True)
class ConfigMulti:
    """Parámetros del multibono: 2 o 3 bonos en casas distintas y el plazo.

    Cada bono es un `ConfigBonus` (casa, importe y cuota mínima; sin fecha
    propia). `fecha_apalancamiento` es el plazo global: los partidos de bono
    deben saldarse antes de que se salde la apuesta de apalancamiento.
    """

    bonos: tuple[ConfigBonus, ...]
    fecha_apalancamiento: datetime | None = None


def _construir_bono_multi(dato: dict) -> ConfigBonus:
    """Valida y normaliza un bono del multibono (RF-3).

    Exige casa indicada, importe mayor que 0 y cuota mínima mayor que 1. La
    cuota mínima se lee de 'cuota_minima' o de 'min' (formato del archivo de
    bonos que reutiliza `cargar_bonos`). Lanza `ErrorDatos` en español si falla.
    """
    casa = dato.get("casa")
    if not isinstance(casa, str) or not casa.strip():
        raise ErrorDatos("Un bono del multibono no tiene una 'casa' válida.")

    importe = _bono_decimal(dato.get("importe"), "importe", casa)
    if importe is None or importe <= 0:
        raise ErrorDatos(f"El importe del bono de '{casa}' debe ser un número mayor que 0.")

    bruto_min = dato.get("cuota_minima")
    if bruto_min is None:
        bruto_min = dato.get("min")
    cuota_minima = _bono_decimal(bruto_min, "cuota mínima", casa)
    if cuota_minima is None or cuota_minima <= 1:
        raise ErrorDatos(f"La cuota mínima del bono de '{casa}' debe ser un número mayor que 1.")

    return ConfigBonus(casa=casa, importe=importe, cuota_minima=cuota_minima)


def construir_config_multi(datos: list[dict], fecha_apalancamiento: object = None) -> ConfigMulti:
    """Valida y normaliza la configuración del multibono (RF-2, RF-3, RF-4).

    Exige de 2 a 3 bonos (con 1 la herramienta es `bonus`), cada uno válido
    (casa, importe > 0, cuota mínima > 1) y en una casa distinta de los demás
    (comparando con `normalizar`). La fecha de apalancamiento, si se da, debe ser
    interpretable. Lanza `ErrorDatos` en español si algo falla.
    """
    if not isinstance(datos, list) or not 2 <= len(datos) <= 3:
        raise ErrorDatos("El multibono necesita 2 o 3 bonos (con 1 bono usa 'bonus').")

    bonos: list[ConfigBonus] = []
    vistas: dict[str, str] = {}
    for dato in datos:
        bono = _construir_bono_multi(dato)
        clave = normalizar(bono.casa)
        anterior = vistas.get(clave)
        if anterior is not None:
            raise ErrorDatos(
                f"La casa '{bono.casa}' aparece en más de un bono "
                f"(coincide con '{anterior}'); cada bono va en una casa distinta."
            )
        vistas[clave] = bono.casa
        bonos.append(bono)

    return ConfigMulti(
        bonos=tuple(bonos),
        fecha_apalancamiento=_parse_fecha(
            fecha_apalancamiento, "la fecha del partido de apalancamiento"
        ),
    )


@dataclass(frozen=True)
class PataMulti:
    """Una pata del multibono: apuesta de bono (`tipo="bono"`) o de relleno con
    dinero real (`tipo="relleno"`). `importe` va sin redondear."""

    tipo: str  # "bono" | "relleno"
    resultado: str
    importe: Decimal
    cuota: Decimal
    casa: str


@dataclass(frozen=True)
class OpcionMulti:
    """Colocación de los bonos en un partido, con su relleno y sus métricas.

    Todo va sin redondear. `retorno` es el techo `R = máx(importe·cuota)` de las
    patas de bono; `perdida` = (bonos + dinero real) − R (positiva es pérdida,
    negativa es arbitraje); `perdida_pct` es esa pérdida sobre el total de bono,
    en tanto por ciento; `neto` = R − dinero real (lo que acabas teniendo).
    """

    partido: str
    retorno: Decimal
    patas: tuple[PataMulti, ...]
    dinero_real: Decimal
    perdida: Decimal
    perdida_pct: Decimal
    neto: Decimal


def calcular_opcion_multi(
    partido: str,
    asignacion: dict[str, tuple[ConfigBonus, Decimal] | None],
    rellenos: dict[str, tuple[Decimal, str]],
) -> OpcionMulti:
    """Calcula la opción de un partido dada una asignación bono→resultado.

    `asignacion[r]` es `(bono, cuota_bono)` si un bono se ancla en el resultado
    `r`, o `None` si ese resultado va solo con dinero real (caso de 2 bonos).
    `rellenos[r]` es `(cuota, casa)` de la mejor cuota de `r` en casa distinta de
    las de bono, usada cuando ese resultado necesita dinero real.

    El techo es `R = máx(importe·cuota)` de las patas de bono (RF-12). Cada
    resultado por debajo de `R` se rellena con `(R−B)/cuota` (RF-13), y el
    resultado sin bono se cubre entero con `R/cuota` (RF-14). Con eso se calculan
    la pérdida (€ y %), el dinero real y el neto (RF-18..RF-21). Todo en
    `Decimal`, sin redondear.
    """
    anclados = [v for v in asignacion.values() if v is not None]
    retorno = max(bono.importe * cuota for bono, cuota in anclados)

    patas: list[PataMulti] = []
    dinero_real = Decimal(0)
    total_bono = Decimal(0)
    for r in RESULTADOS:
        anclado = asignacion.get(r)
        if anclado is not None:
            bono, cuota_bono = anclado
            total_bono += bono.importe
            patas.append(PataMulti("bono", r, bono.importe, cuota_bono, bono.casa))
            falta = retorno - bono.importe * cuota_bono
        else:
            falta = retorno  # resultado sin bono: se cubre entero (RF-14)
        if falta > 0:
            cuota_r, casa_r = rellenos[r]
            stake = falta / cuota_r
            dinero_real += stake
            patas.append(PataMulti("relleno", r, stake, cuota_r, casa_r))

    total = total_bono + dinero_real
    perdida = total - retorno
    return OpcionMulti(
        partido=partido,
        retorno=retorno,
        patas=tuple(patas),
        dinero_real=dinero_real,
        perdida=perdida,
        perdida_pct=perdida / total_bono * Decimal(100),
        neto=retorno - dinero_real,
    )


def _mejor_cuota_excluyendo(
    partido: dict, resultado: str, casas_excluidas: set[str]
) -> tuple[Decimal, str] | None:
    """Mejor cuota de un resultado entre las casas NO excluidas (RF-15, RF-16).

    Generaliza `_mejor_cobertura` a excluir un conjunto de casas (todas las de
    bono). Devuelve `(cuota, casa)` con la cuota más alta; ante empate, la primera
    por orden de entrada. `None` si ninguna casa fuera del conjunto ofrece cuota
    válida para ese resultado.
    """
    mejor: tuple[Decimal, str] | None = None
    for entrada in partido["cuotas"]:
        if normalizar(entrada["casa"]) in casas_excluidas:
            continue
        cuota = _a_cuota_valida(entrada.get(resultado))
        if cuota is None:
            continue
        if mejor is None or cuota > mejor[0]:
            mejor = (cuota, entrada["casa"])
    return mejor


def _opcion_de_partido_multi(
    partido: dict, config: ConfigMulti
) -> tuple[OpcionMulti | None, Descarte | None]:
    """Mejor opción de un partido para el multibono, o el motivo del descarte.

    Comprueba que todas las casas de bono participan (RF-17); prueba las
    asignaciones válidas bono→resultado (cuota anclada ≥ mínima, RF-8;
    resultados rellenables en casa distinta a todas las de bono, RF-16) y devuelve
    la de menor pérdida (RF-9), o un `Descarte` si ninguna es válida. Ante empate
    de pérdida, la primera por orden de permutación (determinista).
    """
    nombre = partido["partido"]
    casas_bono = {normalizar(b.casa) for b in config.bonos}

    entradas: dict[str, dict] = {}
    for bono in config.bonos:
        clave = normalizar(bono.casa)
        entrada = _entrada_de_casa(partido, clave)
        if entrada is None:
            return None, Descarte(nombre, None, f"La casa '{bono.casa}' no participa en este partido.")
        entradas[clave] = entrada

    opciones: list[OpcionMulti] = []
    motivo: str | None = None
    for perm in itertools.permutations(RESULTADOS, len(config.bonos)):
        asignacion: dict[str, tuple[ConfigBonus, Decimal] | None] = {r: None for r in RESULTADOS}
        valida = True
        for bono, resultado in zip(config.bonos, perm):
            cuota = _a_cuota_valida(entradas[normalizar(bono.casa)].get(resultado))
            if cuota is None or cuota < bono.cuota_minima:
                valida = False
                break
            asignacion[resultado] = (bono, cuota)
        if not valida:
            continue

        retorno = max(b.importe * c for b, c in (v for v in asignacion.values() if v is not None))
        rellenos: dict[str, tuple[Decimal, str]] = {}
        cubrible = True
        for r in RESULTADOS:
            anclado = asignacion[r]
            falta = retorno if anclado is None else retorno - anclado[0].importe * anclado[1]
            if falta > 0:
                cobertura = _mejor_cuota_excluyendo(partido, r, casas_bono)
                if cobertura is None:
                    cubrible = False
                    motivo = (
                        f"El resultado '{r}' no se puede rellenar con dinero real "
                        "en una casa distinta a las de los bonos."
                    )
                    break
                rellenos[r] = cobertura
        if cubrible:
            opciones.append(calcular_opcion_multi(nombre, asignacion, rellenos))

    if opciones:
        return min(opciones, key=lambda o: o.perdida), None
    if motivo is None:
        motivo = "Ningún bono admite una asignación válida (cuota por debajo de la mínima exigida)."
    return None, Descarte(nombre, None, motivo)


@dataclass
class ResultadoMulti:
    """Opciones del multibono (ordenadas por pérdida), descartes y avisos."""

    config: ConfigMulti
    opciones: list[OpcionMulti]
    descartes: list[Descarte]
    avisos_sin_fecha: list[str]


def evaluar_multibono(partidos: list[dict], config: ConfigMulti) -> ResultadoMulti:
    """Genera la mejor opción de cada partido, aplica el plazo y ordena por pérdida.

    Con fecha de apalancamiento, un partido que se juega en esa fecha o después se
    descarta (RF-26) y uno sin fecha se evalúa igual pero con aviso (RF-27); sin
    apalancamiento las fechas se ignoran (RF-28). Las opciones válidas se ordenan
    por pérdida ascendente, con las de pérdida negativa (arbitraje) en el mismo
    orden (RF-22, RF-24). Archivo sin partidos u opciones → listas vacías (RF-33,
    RF-34).
    """
    opciones: list[OpcionMulti] = []
    descartes: list[Descarte] = []
    avisos_sin_fecha: list[str] = []

    for partido in partidos:
        nombre = partido["partido"]
        fecha = partido.get("fecha")
        if config.fecha_apalancamiento is not None:
            if fecha is None:
                avisos_sin_fecha.append(nombre)
            else:
                fecha_partido = _parse_fecha(fecha, f"la fecha del partido '{nombre}'")
                if fecha_partido >= config.fecha_apalancamiento:
                    descartes.append(
                        Descarte(
                            nombre,
                            None,
                            "Se juega en la fecha del apalancamiento o después (fuera de plazo).",
                        )
                    )
                    continue

        opcion, descarte = _opcion_de_partido_multi(partido, config)
        if opcion is not None:
            opciones.append(opcion)
        else:
            descartes.append(descarte)

    opciones.sort(key=lambda o: o.perdida)
    return ResultadoMulti(config, opciones, descartes, avisos_sin_fecha)


# --- Spec 005: filtro de promo "ventaja de 2 goles" ---


@dataclass(frozen=True)
class FiltroPromo:
    """Casas con la promo de ventaja de 2 goles (claves normalizadas)."""

    casas: frozenset[str]


def construir_filtro_promo(casas: list[str]) -> FiltroPromo:
    """Valida y normaliza la lista de casas con promo (RF-1, RF-3, RF-5).

    Ignora entradas vacías; si no queda ninguna casa, lanza `ErrorDatos`.
    """
    normalizadas = frozenset(
        normalizar(c) for c in casas if isinstance(c, str) and c.strip()
    )
    if not normalizadas:
        raise ErrorDatos("El filtro de promo necesita al menos una casa.")
    return FiltroPromo(casas=normalizadas)


@dataclass(frozen=True)
class PataPromo:
    """Una pata de ganar (1 o 2) posicionada en una casa de la promo.

    `casa`/`cuota` son la mejor cuota de ese resultado **entre las casas de la
    promo**; `casa_referencia`/`cuota_referencia` son la mejor cuota **sin
    restricción** (para medir el coste). El coste y el windfall en euros se
    calculan con `coste_promo`/`windfall_promo` cuando hay importe.
    """

    resultado: str
    casa: str
    cuota: Decimal
    casa_referencia: str
    cuota_referencia: Decimal


@dataclass(frozen=True)
class OpcionPromo:
    """Una opción de posicionamiento: `"asegurar_1"`, `"asegurar_2"` o `"asegurar_ambos"`."""

    nombre: str
    patas: tuple[PataPromo, ...]


@dataclass
class PromoPartido:
    """Las opciones de promo de un partido y sus avisos (RF-4, RF-10, RF-15, RF-17)."""

    partido: str
    opciones: tuple[OpcionPromo, ...]
    avisos: list[str]


def _mejor_cuota(
    partido: dict, resultado: str, casas_incluidas: frozenset[str] | None = None
) -> tuple[Decimal, str] | None:
    """Mejor cuota de un resultado, opcionalmente solo entre `casas_incluidas`.

    Con `casas_incluidas=None` mira todas las casas (referencia). Devuelve
    `(cuota, casa)` con la cuota más alta; ante empate, la primera por orden de
    entrada. `None` si ninguna casa considerada ofrece cuota válida.
    """
    mejor: tuple[Decimal, str] | None = None
    for entrada in partido["cuotas"]:
        if casas_incluidas is not None and normalizar(entrada["casa"]) not in casas_incluidas:
            continue
        cuota = _a_cuota_valida(entrada.get(resultado))
        if cuota is None:
            continue
        if mejor is None or cuota > mejor[0]:
            mejor = (cuota, entrada["casa"])
    return mejor


def posicion_promo(partido: dict, resultado: str, filtro: FiltroPromo) -> PataPromo | None:
    """Posiciona una pata de ganar (RF-6, RF-8, RF-11, RF-12, RF-13).

    `None` si ninguna casa de la promo cotiza ese resultado (RF-10). La cuota de
    referencia sale de entre todas las casas; como las de promo son un subconjunto,
    `cuota_referencia >= cuota` (el coste nunca es negativo; es 0 si la mejor cuota
    ya es de la lista, RF-13).
    """
    promo = _mejor_cuota(partido, resultado, filtro.casas)
    if promo is None:
        return None
    cuota, casa = promo
    cuota_ref, casa_ref = _mejor_cuota(partido, resultado)
    return PataPromo(resultado, casa, cuota, casa_ref, cuota_ref)


def opciones_promo(partido: dict, filtro: FiltroPromo) -> PromoPartido:
    """Las tres opciones de posicionamiento de un partido (RF-4, RF-7, RF-17).

    Solo posiciona las patas de ganar (1 y 2); la X nunca se restringe (RF-7). Si
    una pata no puede asegurarse (ninguna casa de la promo la cotiza) se omite su
    opción y se avisa (RF-10). Con ambas patas asegurables se añade "asegurar
    ambos" y el aviso de que los windfalls pueden acumularse (RF-15).
    """
    pata_1 = posicion_promo(partido, "1", filtro)
    pata_2 = posicion_promo(partido, "2", filtro)

    opciones: list[OpcionPromo] = []
    avisos: list[str] = []
    if pata_1 is not None:
        opciones.append(OpcionPromo("asegurar_1", (pata_1,)))
    else:
        avisos.append("Ninguna casa de la promo cotiza el resultado 1; no se puede asegurar esa pata.")
    if pata_2 is not None:
        opciones.append(OpcionPromo("asegurar_2", (pata_2,)))
    else:
        avisos.append("Ninguna casa de la promo cotiza el resultado 2; no se puede asegurar esa pata.")
    if pata_1 is not None and pata_2 is not None:
        opciones.append(OpcionPromo("asegurar_ambos", (pata_1, pata_2)))
        avisos.append(
            "Con ambas patas aseguradas, los dos windfalls pueden acumularse "
            "(doble remontada que acaba en empate)."
        )

    return PromoPartido(partido["partido"], tuple(opciones), avisos)


def coste_promo(pata: PataPromo, importe: Decimal) -> Decimal:
    """Coste relativo en euros de asegurar una pata: `importe·(ref − promo)` (RF-11)."""
    return importe * (pata.cuota_referencia - pata.cuota)


def windfall_promo(pata: PataPromo, importe: Decimal) -> Decimal:
    """Windfall en euros si salta la ventaja de 2 goles: `importe·cuota` (RF-14)."""
    return importe * pata.cuota


def payout_de_cuotas(cuotas: dict[str, Decimal]) -> Decimal:
    """% de pago a partir de las cuotas 1/X/2, sin redondear (RF-18)."""
    inversa = sum((Decimal(1) / cuotas[r] for r in RESULTADOS), Decimal(0))
    return Decimal(100) / inversa


def payout_asegurado(mejores: dict[str, MejorCuota | None], opcion: OpcionPromo) -> Decimal | None:
    """% de pago sustituyendo las patas aseguradas por su cuota de promo (RF-18).

    `mejores` son las mejores cuotas del comparador (sin restricción). Devuelve
    `None` si el partido está incompleto (falta alguna mejor cuota).
    """
    if any(mejores[r] is None for r in RESULTADOS):
        return None
    cuotas = {r: mejores[r].cuota for r in RESULTADOS}
    for pata in opcion.patas:
        cuotas[pata.resultado] = pata.cuota
    return payout_de_cuotas(cuotas)


def posicion_promo_cobertura(
    partido: dict, resultado: str, filtro: FiltroPromo, casa_bono: str
) -> tuple[Decimal, str] | None:
    """Mejor cuota de un resultado de ganar entre las casas de la promo,
    **excluyendo la del bono** (constitución nº 10), para posicionar coberturas en
    freebet/bonus (RF-20, RF-21). `None` si ninguna casa de la promo distinta de la
    del bono la cotiza.
    """
    casas = filtro.casas - {normalizar(casa_bono)}
    if not casas:
        return None
    return _mejor_cuota(partido, resultado, casas)
