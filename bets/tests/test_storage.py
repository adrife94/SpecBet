"""T2: carga y validación del JSON de entrada (RF-11, RF-12)."""

from decimal import Decimal
from pathlib import Path

import pytest

from betting.storage import ErrorDatos, cargar


def _escribir(tmp_path: Path, contenido: str) -> Path:
    ruta = tmp_path / "partidos.json"
    ruta.write_text(contenido, encoding="utf-8")
    return ruta


def test_archivo_inexistente(tmp_path):
    with pytest.raises(ErrorDatos):
        cargar(tmp_path / "no_existe.json")


def test_json_invalido(tmp_path):
    ruta = _escribir(tmp_path, "{ esto no es json")
    with pytest.raises(ErrorDatos):
        cargar(ruta)


def test_raiz_no_es_objeto(tmp_path):
    ruta = _escribir(tmp_path, "[]")
    with pytest.raises(ErrorDatos):
        cargar(ruta)


def test_falta_clave_partidos(tmp_path):
    ruta = _escribir(tmp_path, '{"version": 1}')
    with pytest.raises(ErrorDatos):
        cargar(ruta)


def test_partidos_no_es_lista(tmp_path):
    ruta = _escribir(tmp_path, '{"partidos": 5}')
    with pytest.raises(ErrorDatos):
        cargar(ruta)


def test_partido_sin_cuotas_lista(tmp_path):
    ruta = _escribir(tmp_path, '{"partidos": [{"partido": "A vs B", "cuotas": 3}]}')
    with pytest.raises(ErrorDatos):
        cargar(ruta)


def test_archivo_valido_sin_partidos_devuelve_lista_vacia(tmp_path):
    ruta = _escribir(tmp_path, '{"version": 1, "partidos": []}')
    assert cargar(ruta) == []


def test_cuotas_se_cargan_como_decimal(tmp_path):
    ruta = _escribir(
        tmp_path,
        '{"version": 1, "partidos": [{"partido": "A vs B",'
        ' "cuotas": [{"casa": "Bet365", "1": 2.10, "X": 3.30, "2": 3.50}]}]}',
    )
    partidos = cargar(ruta)
    cuota = partidos[0]["cuotas"][0]["1"]
    assert isinstance(cuota, Decimal)
    assert cuota == Decimal("2.10")
    assert str(cuota) == "2.10"
