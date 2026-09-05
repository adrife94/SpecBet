"""T5/T6/T7: CLI del comando surebet (RF-4, RF-11..RF-16)."""

import json
from pathlib import Path

import pytest

from betting.cli import main

SUREBET = (
    '{"partido": "Madrid vs Barça", "payout": "100.80", "incompleto": false,'
    ' "mejores": {'
    ' "1": {"cuota": "2.10", "casas": ["Bet365", "Codere"]},'
    ' "X": {"cuota": "3.60", "casas": ["Winamax"]},'
    ' "2": {"cuota": "4.20", "casas": ["Bet365"]}}}'
)
PERDIDA = (
    '{"partido": "Sevilla vs Betis", "payout": "85.71", "incompleto": false,'
    ' "mejores": {'
    ' "1": {"cuota": "2.00", "casas": ["Bet365"]},'
    ' "X": {"cuota": "3.00", "casas": ["Codere"]},'
    ' "2": {"cuota": "3.00", "casas": ["Winamax"]}}}'
)
INCOMPLETO = (
    '{"partido": "Cádiz vs Elche", "payout": null, "incompleto": true,'
    ' "mejores": {'
    ' "1": {"cuota": "1.90", "casas": ["Bet365"]},'
    ' "X": {"cuota": null, "casas": []},'
    ' "2": {"cuota": null, "casas": []}}}'
)


def _escribir(tmp_path: Path, *partidos: str) -> str:
    ruta = tmp_path / "comparacion.json"
    ruta.write_text('{"partidos": [' + ",".join(partidos) + "]}", encoding="utf-8")
    return str(ruta)


# --- T5: tabla legible (RF-4, RF-11) ---


def test_tabla_muestra_reparto_estado_e_importes(tmp_path, capsys):
    ruta = _escribir(tmp_path, SUREBET, PERDIDA)
    codigo = main(["surebet", ruta, "--inversion", "100"])
    salida = capsys.readouterr().out
    assert codigo == 0
    assert "surebet" in salida
    assert "pérdida" in salida
    # importe (cuánto) y casa (dónde) de la pata 1 del surebet: 48.00 en Bet365/Codere
    assert "48.00" in salida
    assert "Bet365/Codere" in salida
    assert "100.80" in salida  # retorno garantizado


# --- T6: validación de entrada, casos vacíos y recordatorio (RF-12..RF-14, RF-16) ---


@pytest.mark.parametrize("valor", ["0", "-5", "abc"])
def test_inversion_invalida_error_y_salida_1(tmp_path, capsys, valor):
    ruta = _escribir(tmp_path, SUREBET)
    codigo = main(["surebet", ruta, "--inversion", valor])
    assert codigo == 1
    assert "Error" in capsys.readouterr().err


def test_entrada_corrupta_error_y_salida_1(tmp_path, capsys):
    ruta = tmp_path / "roto.json"
    ruta.write_text("{ no es json", encoding="utf-8")
    codigo = main(["surebet", str(ruta), "--inversion", "100"])
    assert codigo == 1
    assert "Error" in capsys.readouterr().err


def test_entrada_sin_partidos_mensaje_y_salida_0(tmp_path, capsys):
    ruta = _escribir(tmp_path)  # sin partidos
    codigo = main(["surebet", ruta, "--inversion", "100"])
    assert codigo == 0
    assert "No hay partidos" in capsys.readouterr().out


def test_recordatorio_de_verificar_cuotas_por_stderr(tmp_path, capsys):
    ruta = _escribir(tmp_path, SUREBET)
    main(["surebet", ruta, "--inversion", "100"])
    assert "Recuerda" in capsys.readouterr().err


# --- T7: salida --json reutilizable (RF-15) ---


def test_json_parseable_coherente_y_ordenado(tmp_path, capsys):
    ruta = _escribir(tmp_path, PERDIDA, INCOMPLETO, SUREBET)
    codigo = main(["surebet", ruta, "--inversion", "100", "--json"])
    salida = capsys.readouterr().out
    assert codigo == 0

    datos = json.loads(salida)
    assert datos["version"] == 1
    assert datos["inversion"] == "100.00"

    nombres = [p["partido"] for p in datos["partidos"]]
    assert nombres == ["Madrid vs Barça", "Sevilla vs Betis", "Cádiz vs Elche"]

    surebet = datos["partidos"][0]
    assert surebet["surebet"] is True
    assert surebet["no_calculable"] is False
    assert surebet["retorno"] == "100.80"
    assert surebet["beneficio"] == "0.80"
    assert surebet["patas"]["1"] == {
        "importe": "48.00",
        "cuota": "2.10",
        "casas": ["Bet365", "Codere"],
    }


def test_json_partido_no_calculable_lleva_nulls(tmp_path, capsys):
    ruta = _escribir(tmp_path, INCOMPLETO)
    main(["surebet", ruta, "--inversion", "100", "--json"])
    datos = json.loads(capsys.readouterr().out)
    incompleto = datos["partidos"][0]
    assert incompleto["no_calculable"] is True
    assert incompleto["retorno"] is None
    assert incompleto["beneficio"] is None
    assert incompleto["patas"] is None
    assert incompleto["payout"] is None


def test_json_stdout_limpio_recordatorio_en_stderr(tmp_path, capsys):
    ruta = _escribir(tmp_path, SUREBET)
    main(["surebet", ruta, "--inversion", "100", "--json"])
    capturado = capsys.readouterr()
    json.loads(capturado.out)  # stdout es solo JSON parseable
    assert "Recuerda" in capturado.err
