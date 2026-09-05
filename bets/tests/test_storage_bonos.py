"""T1: carga de bonos y construcción del modelo Bono (RF-17, RF-18, RF-19, RF-28)."""

from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest

from betting.core import construir_bono
from betting.storage import ErrorDatos, cargar_bonos


def _escribir(tmp_path: Path, contenido: str) -> Path:
    ruta = tmp_path / "bonos.json"
    ruta.write_text(contenido, encoding="utf-8")
    return ruta


def test_archivo_inexistente(tmp_path):
    with pytest.raises(ErrorDatos):
        cargar_bonos(tmp_path / "no_existe.json")


def test_json_invalido(tmp_path):
    with pytest.raises(ErrorDatos):
        cargar_bonos(_escribir(tmp_path, "{ no es json"))


def test_falta_lista_bonos(tmp_path):
    with pytest.raises(ErrorDatos):
        cargar_bonos(_escribir(tmp_path, '{"version": 1}'))


def test_bono_sin_casa(tmp_path):
    with pytest.raises(ErrorDatos):
        cargar_bonos(_escribir(tmp_path, '{"bonos": [{"importe": 10}]}'))


def test_bono_sin_importe(tmp_path):
    with pytest.raises(ErrorDatos):
        cargar_bonos(_escribir(tmp_path, '{"bonos": [{"casa": "Luckia"}]}'))


def test_importe_y_rango_se_cargan_como_decimal(tmp_path):
    ruta = _escribir(
        tmp_path,
        '{"bonos": [{"casa": "Luckia", "importe": 10, "min": 1.5, "max": 3.5,'
        ' "fecha_limite": "2026-09-12", "resultado": "1"}]}',
    )
    bonos = cargar_bonos(ruta)
    bono = construir_bono(bonos[0])
    assert bono.casa == "Luckia"
    assert isinstance(bono.importe, Decimal)
    assert bono.importe == Decimal("10")
    assert (bono.cuota_min, bono.cuota_max) == (Decimal("1.5"), Decimal("3.5"))
    assert bono.fecha_limite == datetime(2026, 9, 12)
    assert bono.resultado == "1"


def test_importe_no_positivo_es_error():
    with pytest.raises(ErrorDatos):
        construir_bono({"casa": "Luckia", "importe": Decimal("0")})


def test_resultado_invalido_es_error():
    with pytest.raises(ErrorDatos):
        construir_bono({"casa": "Luckia", "importe": Decimal("10"), "resultado": "3"})


def test_rango_min_mayor_que_max_es_error():
    with pytest.raises(ErrorDatos):
        construir_bono(
            {"casa": "Luckia", "importe": Decimal("10"), "min": Decimal("4"), "max": Decimal("2")}
        )


def test_fecha_limite_invalida_es_error():
    with pytest.raises(ErrorDatos):
        construir_bono({"casa": "Luckia", "importe": Decimal("10"), "fecha_limite": "12/09/2026"})


def test_importe_desde_string_de_flag():
    # La CLI de un solo bono construye el dict con el importe como string.
    bono = construir_bono({"casa": "Luckia", "importe": "10.50"})
    assert bono.importe == Decimal("10.50")
