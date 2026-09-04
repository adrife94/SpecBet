"""Carga y validación del archivo JSON de entrada del comparador."""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path


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
