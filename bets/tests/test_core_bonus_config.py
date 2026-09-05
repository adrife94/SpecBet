"""T1: configuración del bono (RF-18, RF-19, RF-20)."""

from datetime import datetime
from decimal import Decimal

import pytest

from betting.core import construir_config_bonus
from betting.storage import ErrorDatos


def test_config_valida_normaliza_a_decimal_y_datetime():
    config = construir_config_bonus(
        {"casa": "Luckia", "importe": "100", "cuota_minima": "1.5", "fecha_limite": "2026-09-12"}
    )
    assert config.casa == "Luckia"
    assert config.importe == Decimal("100")
    assert config.cuota_minima == Decimal("1.5")
    assert config.fecha_limite == datetime(2026, 9, 12)


def test_importe_no_positivo_es_error():
    with pytest.raises(ErrorDatos):
        construir_config_bonus({"casa": "Luckia", "importe": "0", "cuota_minima": "1.5"})


def test_cuota_minima_no_mayor_que_1_es_error():
    with pytest.raises(ErrorDatos):
        construir_config_bonus({"casa": "Luckia", "importe": "100", "cuota_minima": "1"})


def test_casa_no_indicada_es_error():
    with pytest.raises(ErrorDatos):
        construir_config_bonus({"casa": None, "importe": "100", "cuota_minima": "1.5"})


def test_fecha_limite_invalida_es_error():
    with pytest.raises(ErrorDatos):
        construir_config_bonus(
            {"casa": "Luckia", "importe": "100", "cuota_minima": "1.5", "fecha_limite": "12-09-2026"}
        )
