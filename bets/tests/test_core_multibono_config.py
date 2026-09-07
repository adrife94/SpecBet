"""T1: configuración del multibono (RF-2, RF-3, RF-4)."""

from datetime import datetime
from decimal import Decimal

import pytest

from betting.core import construir_config_multi
from betting.storage import ErrorDatos


def _bono(casa, importe="100", cuota_minima="1.5"):
    return {"casa": casa, "importe": importe, "cuota_minima": cuota_minima}


def test_config_valida_normaliza_a_decimal_y_datetime():
    config = construir_config_multi(
        [_bono("Luckia"), _bono("Bet365"), _bono("Winamax")],
        fecha_apalancamiento="2026-09-20",
    )
    assert [b.casa for b in config.bonos] == ["Luckia", "Bet365", "Winamax"]
    assert all(b.importe == Decimal("100") for b in config.bonos)
    assert all(b.cuota_minima == Decimal("1.5") for b in config.bonos)
    assert config.fecha_apalancamiento == datetime(2026, 9, 20)


def test_dos_bonos_es_valido_sin_apalancamiento():
    config = construir_config_multi([_bono("Luckia"), _bono("Bet365")])
    assert len(config.bonos) == 2
    assert config.fecha_apalancamiento is None


def test_lee_cuota_minima_desde_clave_min_del_archivo_de_bonos():
    # cargar_bonos usa 'min' (formato de la spec 003); debe aceptarse.
    config = construir_config_multi(
        [
            {"casa": "Luckia", "importe": Decimal("100"), "min": Decimal("1.5")},
            {"casa": "Bet365", "importe": Decimal("50"), "min": Decimal("2.0")},
        ]
    )
    assert config.bonos[0].cuota_minima == Decimal("1.5")
    assert config.bonos[1].cuota_minima == Decimal("2.0")
    assert config.bonos[1].importe == Decimal("50")


def test_importes_distintos_permitidos():
    config = construir_config_multi(
        [_bono("Luckia", importe="100"), _bono("Bet365", importe="30"), _bono("Winamax", importe="75")]
    )
    assert [b.importe for b in config.bonos] == [Decimal("100"), Decimal("30"), Decimal("75")]


def test_menos_de_dos_bonos_es_error():
    with pytest.raises(ErrorDatos):
        construir_config_multi([_bono("Luckia")])


def test_mas_de_tres_bonos_es_error():
    with pytest.raises(ErrorDatos):
        construir_config_multi(
            [_bono("Luckia"), _bono("Bet365"), _bono("Winamax"), _bono("Codere")]
        )


def test_importe_no_positivo_es_error():
    with pytest.raises(ErrorDatos):
        construir_config_multi([_bono("Luckia", importe="0"), _bono("Bet365")])


def test_cuota_minima_no_mayor_que_1_es_error():
    with pytest.raises(ErrorDatos):
        construir_config_multi([_bono("Luckia", cuota_minima="1"), _bono("Bet365")])


def test_casas_repetidas_es_error():
    with pytest.raises(ErrorDatos):
        construir_config_multi([_bono("Luckia"), _bono(" luckia ")])


def test_fecha_apalancamiento_invalida_es_error():
    with pytest.raises(ErrorDatos):
        construir_config_multi(
            [_bono("Luckia"), _bono("Bet365")], fecha_apalancamiento="20-09-2026"
        )
