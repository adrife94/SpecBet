"""Lógica pura del comparador de cuotas (sin IO, testeable sin la CLI)."""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal

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
