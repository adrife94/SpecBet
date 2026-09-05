"""Carga y validación del archivo JSON de entrada del comparador."""

from __future__ import annotations

import json
from decimal import Decimal, InvalidOperation
from pathlib import Path

_RESULTADOS: tuple[str, ...] = ("1", "X", "2")


class ErrorDatos(Exception):
    """El archivo de entrada no existe, no es JSON válido o su estructura no es la esperada."""


def cargar(ruta: str | Path) -> list[dict]:
    """Carga el JSON de entrada y devuelve la lista de partidos.

    Los números del JSON (las cuotas) se cargan como `Decimal`, nunca como
    `float`. Lanza `ErrorDatos` si el archivo no se puede leer, no es JSON
    válido o no tiene la estructura esperada. Un archivo válido sin partidos
    devuelve una lista vacía.
    """
    ruta = Path(ruta)
    try:
        texto = ruta.read_text(encoding="utf-8")
    except OSError as exc:
        raise ErrorDatos(f"No se pudo leer el archivo '{ruta}': {exc}") from exc

    try:
        datos = json.loads(texto, parse_float=Decimal)
    except json.JSONDecodeError as exc:
        raise ErrorDatos(f"El archivo '{ruta}' no es JSON válido: {exc}") from exc

    return _validar(datos, ruta)


def _validar(datos: object, ruta: Path) -> list[dict]:
    if not isinstance(datos, dict):
        raise ErrorDatos(f"El archivo '{ruta}' debe contener un objeto JSON en la raíz.")

    partidos = datos.get("partidos")
    if partidos is None:
        raise ErrorDatos(f"El archivo '{ruta}' no tiene la clave 'partidos'.")
    if not isinstance(partidos, list):
        raise ErrorDatos(f"En '{ruta}', 'partidos' debe ser una lista.")

    for indice, partido in enumerate(partidos):
        _validar_partido(partido, indice, ruta)
    return partidos


def _validar_partido(partido: object, indice: int, ruta: Path) -> None:
    posicion = f"el partido nº {indice + 1}"
    if not isinstance(partido, dict):
        raise ErrorDatos(f"En '{ruta}', {posicion} debe ser un objeto.")

    nombre = partido.get("partido")
    if not isinstance(nombre, str) or not nombre.strip():
        raise ErrorDatos(f"En '{ruta}', {posicion} no tiene un nombre válido en 'partido'.")

    cuotas = partido.get("cuotas")
    if not isinstance(cuotas, list):
        raise ErrorDatos(f"En '{ruta}', el partido '{nombre}' debe tener una lista 'cuotas'.")

    for entrada in cuotas:
        if not isinstance(entrada, dict):
            raise ErrorDatos(
                f"En '{ruta}', una entrada de 'cuotas' del partido '{nombre}' no es un objeto."
            )
        casa = entrada.get("casa")
        if not isinstance(casa, str) or not casa.strip():
            raise ErrorDatos(
                f"En '{ruta}', una entrada de 'cuotas' del partido '{nombre}' no tiene una 'casa' válida."
            )


def cargar_comparacion(ruta: str | Path) -> list[dict]:
    """Carga la salida de `compare --json` y devuelve la lista de partidos.

    Es la entrada del comando `surebet`: no el JSON crudo de partidos, sino el
    resultado del comparador (con `mejores`, `payout` e `incompleto`). Las cuotas
    y el payout, serializados como string por la spec 001, se reconvierten a
    `Decimal` para no pasar por `float`. Lanza `ErrorDatos` si el archivo no se
    puede leer, no es JSON válido o su estructura no es la del comparador. Una
    entrada válida sin partidos devuelve una lista vacía.
    """
    ruta = Path(ruta)
    try:
        texto = ruta.read_text(encoding="utf-8")
    except OSError as exc:
        raise ErrorDatos(f"No se pudo leer el archivo '{ruta}': {exc}") from exc

    try:
        datos = json.loads(texto)
    except json.JSONDecodeError as exc:
        raise ErrorDatos(f"El archivo '{ruta}' no es JSON válido: {exc}") from exc

    if not isinstance(datos, dict):
        raise ErrorDatos(f"El archivo '{ruta}' debe contener un objeto JSON en la raíz.")

    partidos = datos.get("partidos")
    if partidos is None:
        raise ErrorDatos(f"El archivo '{ruta}' no tiene la clave 'partidos'.")
    if not isinstance(partidos, list):
        raise ErrorDatos(f"En '{ruta}', 'partidos' debe ser una lista.")

    return [_validar_comparado(partido, indice, ruta) for indice, partido in enumerate(partidos)]


def _validar_comparado(partido: object, indice: int, ruta: Path) -> dict:
    """Valida un partido de la salida del comparador y normaliza sus números."""
    posicion = f"el partido nº {indice + 1}"
    if not isinstance(partido, dict):
        raise ErrorDatos(f"En '{ruta}', {posicion} debe ser un objeto.")

    nombre = partido.get("partido")
    if not isinstance(nombre, str) or not nombre.strip():
        raise ErrorDatos(f"En '{ruta}', {posicion} no tiene un nombre válido en 'partido'.")

    incompleto = partido.get("incompleto")
    if not isinstance(incompleto, bool):
        raise ErrorDatos(
            f"En '{ruta}', el partido '{nombre}' no tiene un 'incompleto' booleano; "
            "¿es la salida de 'compare --json'?"
        )

    payout = _a_decimal(partido.get("payout"), ruta, nombre, "payout")

    mejores = partido.get("mejores")
    if not isinstance(mejores, dict):
        raise ErrorDatos(
            f"En '{ruta}', el partido '{nombre}' no tiene 'mejores'; "
            "¿es la salida de 'compare --json'?"
        )

    return {
        "partido": nombre,
        "payout": payout,
        "incompleto": incompleto,
        "mejores": {r: _validar_mejor(mejores.get(r), ruta, nombre, r) for r in _RESULTADOS},
    }


def _validar_mejor(mejor: object, ruta: Path, nombre: str, resultado: str) -> dict:
    """Valida la mejor cuota de un resultado y reconvierte su cuota a `Decimal`."""
    if not isinstance(mejor, dict):
        raise ErrorDatos(
            f"En '{ruta}', el partido '{nombre}' no tiene el resultado '{resultado}' en 'mejores'."
        )
    casas = mejor.get("casas")
    if not isinstance(casas, list) or not all(isinstance(c, str) for c in casas):
        raise ErrorDatos(
            f"En '{ruta}', el resultado '{resultado}' del partido '{nombre}' "
            "no tiene una lista 'casas' de nombres."
        )
    cuota = _a_decimal(mejor.get("cuota"), ruta, nombre, f"cuota de '{resultado}'")
    return {"cuota": cuota, "casas": list(casas)}


def _a_decimal(valor: object, ruta: Path, nombre: str, campo: str) -> Decimal | None:
    """Convierte a `Decimal` un número serializado como string; `None` se conserva."""
    if valor is None:
        return None
    if not isinstance(valor, str):
        raise ErrorDatos(
            f"En '{ruta}', el {campo} del partido '{nombre}' debe ser un string numérico."
        )
    try:
        return Decimal(valor)
    except InvalidOperation as exc:
        raise ErrorDatos(
            f"En '{ruta}', el {campo} del partido '{nombre}' no es un número válido: {valor!r}."
        ) from exc
