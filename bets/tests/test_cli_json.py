"""T9: salida `--json` reutilizable (RF-18)."""

import json
from pathlib import Path

from betting.cli import main


def _escribir(tmp_path: Path, contenido: str) -> str:
    ruta = tmp_path / "partidos.json"
    ruta.write_text(contenido, encoding="utf-8")
    return str(ruta)


COMPLETO = (
    '{"partido": "Madrid vs Barça", "cuotas": ['
    '{"casa": "Bet365", "1": 2.10, "X": 3.30, "2": 3.50},'
    '{"casa": "Codere", "1": 2.05, "X": 3.40, "2": 3.60}]}'
)
INCOMPLETO = '{"partido": "Sevilla vs Betis", "cuotas": [{"casa": "Bet365", "1": 1.90}]}'


def test_json_parseable_y_coherente(tmp_path, capsys):
    ruta = _escribir(tmp_path, '{"partidos": [' + COMPLETO + "," + INCOMPLETO + "]}")
    codigo = main(["compare", ruta, "--json"])
    salida = capsys.readouterr().out
    assert codigo == 0

    datos = json.loads(salida)  # debe ser JSON válido
    assert datos["version"] == 1
    # orden: completo primero, incompleto al final (igual que la tabla)
    completo, incompleto = datos["partidos"]

    assert completo["partido"] == "Madrid vs Barça"
    assert completo["incompleto"] is False
    assert completo["payout"] == "95.41"
    assert completo["mejores"]["1"] == {"cuota": "2.10", "casas": ["Bet365"]}
    assert completo["mejores"]["2"] == {"cuota": "3.60", "casas": ["Codere"]}

    assert incompleto["incompleto"] is True
    assert incompleto["payout"] is None
    assert incompleto["mejores"]["X"] == {"cuota": None, "casas": []}


def test_json_cuotas_y_payout_son_string(tmp_path, capsys):
    ruta = _escribir(tmp_path, '{"partidos": [' + COMPLETO + "]}")
    main(["compare", ruta, "--json"])
    datos = json.loads(capsys.readouterr().out)
    partido = datos["partidos"][0]
    assert isinstance(partido["payout"], str)
    assert isinstance(partido["mejores"]["1"]["cuota"], str)


def test_json_empate_lista_ambas_casas(tmp_path, capsys):
    partido = (
        '{"partido": "A vs B", "cuotas": ['
        '{"casa": "Bet365", "1": 2.10, "X": 3.30, "2": 3.50},'
        '{"casa": "Codere", "1": 2.10, "X": 3.20, "2": 3.60}]}'
    )
    ruta = _escribir(tmp_path, '{"partidos": [' + partido + "]}")
    main(["compare", ruta, "--json"])
    datos = json.loads(capsys.readouterr().out)
    assert datos["partidos"][0]["mejores"]["1"]["casas"] == ["Bet365", "Codere"]


def test_json_vacio_es_json_valido(tmp_path, capsys):
    ruta = _escribir(tmp_path, '{"partidos": []}')
    codigo = main(["compare", ruta, "--json"])
    datos = json.loads(capsys.readouterr().out)
    assert codigo == 0
    assert datos["partidos"] == []


def test_json_stdout_limpio_con_avisos_en_stderr(tmp_path, capsys):
    partido = (
        '{"partido": "A vs B", "cuotas": ['
        '{"casa": "Bet365", "1": "N/A", "X": 3.30, "2": 3.50},'
        '{"casa": "Codere", "1": 2.05, "X": 3.40, "2": 3.60}]}'
    )
    ruta = _escribir(tmp_path, '{"partidos": [' + partido + "]}")
    main(["compare", ruta, "--json"])
    capturado = capsys.readouterr()
    json.loads(capturado.out)  # stdout es solo JSON, parseable
    assert "Aviso" in capturado.err
