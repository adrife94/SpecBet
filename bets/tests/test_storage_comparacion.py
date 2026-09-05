"""T1: carga y validación de la salida de `compare --json` (RF-13, RF-14)."""

from decimal import Decimal
from pathlib import Path

import pytest

from betting.storage import ErrorDatos, cargar_comparacion


def _escribir(tmp_path: Path, contenido: str) -> Path:
    ruta = tmp_path / "comparacion.json"
    ruta.write_text(contenido, encoding="utf-8")
    return ruta


COMPLETO = (
    '{"partido": "Madrid vs Barça", "payout": "101.50", "incompleto": false,'
    ' "mejores": {'
    ' "1": {"cuota": "2.10", "casas": ["Bet365"]},'
    ' "X": {"cuota": "3.60", "casas": ["Codere", "Winamax"]},'
    ' "2": {"cuota": "4.20", "casas": ["Bet365"]}}}'
)
INCOMPLETO = (
    '{"partido": "Sevilla vs Betis", "payout": null, "incompleto": true,'
    ' "mejores": {'
    ' "1": {"cuota": "1.90", "casas": ["Bet365"]},'
    ' "X": {"cuota": null, "casas": []},'
    ' "2": {"cuota": null, "casas": []}}}'
)


def test_archivo_inexistente(tmp_path):
    with pytest.raises(ErrorDatos):
        cargar_comparacion(tmp_path / "no_existe.json")


def test_json_invalido(tmp_path):
    ruta = _escribir(tmp_path, "{ esto no es json")
    with pytest.raises(ErrorDatos):
        cargar_comparacion(ruta)


def test_estructura_ajena_al_comparador(tmp_path):
    # El JSON crudo de partidos (entrada de compare) no vale como entrada de surebet.
    ruta = _escribir(
        tmp_path,
        '{"partidos": [{"partido": "A vs B",'
        ' "cuotas": [{"casa": "Bet365", "1": 2.10, "X": 3.30, "2": 3.50}]}]}',
    )
    with pytest.raises(ErrorDatos):
        cargar_comparacion(ruta)


def test_falta_mejores(tmp_path):
    ruta = _escribir(
        tmp_path,
        '{"partidos": [{"partido": "A vs B", "payout": "95.00", "incompleto": false}]}',
    )
    with pytest.raises(ErrorDatos):
        cargar_comparacion(ruta)


def test_entrada_sin_partidos_devuelve_lista_vacia(tmp_path):
    ruta = _escribir(tmp_path, '{"version": 1, "partidos": []}')
    assert cargar_comparacion(ruta) == []


def test_cuotas_y_payout_se_reconvierten_a_decimal(tmp_path):
    ruta = _escribir(tmp_path, '{"partidos": [' + COMPLETO + "]}")
    partidos = cargar_comparacion(ruta)
    partido = partidos[0]
    assert isinstance(partido["payout"], Decimal)
    assert partido["payout"] == Decimal("101.50")
    cuota = partido["mejores"]["1"]["cuota"]
    assert isinstance(cuota, Decimal)
    assert str(cuota) == "2.10"
    assert partido["mejores"]["X"]["casas"] == ["Codere", "Winamax"]


def test_incompleto_conserva_payout_null_y_cuotas_null(tmp_path):
    ruta = _escribir(tmp_path, '{"partidos": [' + INCOMPLETO + "]}")
    partido = cargar_comparacion(ruta)[0]
    assert partido["incompleto"] is True
    assert partido["payout"] is None
    assert partido["mejores"]["X"]["cuota"] is None
    assert partido["mejores"]["X"]["casas"] == []
