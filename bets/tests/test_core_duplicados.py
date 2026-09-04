"""T3: normalización de nombres y detección de repetidos (RF-13, RF-15, RF-16)."""

import pytest

from betting.core import normalizar, verificar_duplicados
from betting.storage import ErrorDatos


def _partido(nombre: str, *casas: str) -> dict:
    return {"partido": nombre, "cuotas": [{"casa": c, "1": 2, "X": 3, "2": 4} for c in casas]}


def test_normalizar_recorta_y_casefold():
    assert normalizar("  Bet365 ") == "bet365"
    assert normalizar("BET365") == normalizar("bet365")


def test_normalizar_conserva_espacios_interiores():
    assert normalizar("Bet 365") == "bet 365"
    assert normalizar("Bet 365") != normalizar("Bet365")


def test_sin_duplicados_no_lanza():
    partidos = [_partido("Madrid vs Barça", "Bet365", "Codere")]
    verificar_duplicados(partidos)  # no debe lanzar


def test_partido_duplicado_distinta_caja_y_espacios():
    partidos = [
        _partido("Real Madrid vs Barça", "Bet365"),
        _partido("real madrid vs barça ", "Codere"),
    ]
    with pytest.raises(ErrorDatos):
        verificar_duplicados(partidos)


def test_casa_duplicada_en_un_partido():
    partidos = [_partido("Madrid vs Barça", "Bet365", "bet365 ")]
    with pytest.raises(ErrorDatos):
        verificar_duplicados(partidos)


def test_misma_casa_en_partidos_distintos_es_valido():
    partidos = [
        _partido("Madrid vs Barça", "Bet365"),
        _partido("Sevilla vs Betis", "Bet365"),
    ]
    verificar_duplicados(partidos)  # no debe lanzar
