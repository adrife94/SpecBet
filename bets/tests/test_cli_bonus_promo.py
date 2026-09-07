"""T5: filtro de promo en bonus (RF-21, RF-22)."""

import json
from pathlib import Path

import pytest

from betting.cli import main

CUOTAS = """
{"partidos": [
  {"partido": "A vs B", "cuotas": [
     {"casa": "Luckia",  "1": 2.00, "X": 3.20, "2": 3.40},
     {"casa": "Bet365",  "1": 2.60, "X": 3.30, "2": 3.40},
     {"casa": "Winamax", "1": 2.70, "X": 3.20, "2": 3.50}]}
]}
"""


def _cuotas(tmp_path: Path) -> str:
    ruta = tmp_path / "cuotas.json"
    ruta.write_text(CUOTAS, encoding="utf-8")
    return str(ruta)


def _args(tmp_path, *extra):
    return ["bonus", _cuotas(tmp_path), "--casa", "Luckia", "--importe", "100", "--min", "1.5", *extra]


def test_promo_tabla_coberturas_de_ganar(tmp_path, capsys):
    codigo = main(_args(tmp_path, "--promo", "Bet365"))
    salida = capsys.readouterr().out
    assert codigo == 0
    assert "Promo" in salida
    assert "cobertura 1" in salida and "cobertura 2" in salida
    assert "Bet365" in salida
    assert "coste" in salida and "windfall" in salida
    assert "anclado en X" in salida
    assert "acumul" in salida


def test_promo_json_opcion_anclada_en_x(tmp_path, capsys):
    main(_args(tmp_path, "--promo", "Bet365", "--json"))
    datos = json.loads(capsys.readouterr().out)

    op_x = next(o for o in datos["opciones"] if o["resultado"] == "X")
    cob = {c["resultado"]: c for c in op_x["promo"]["coberturas"]}
    assert cob["1"]["casa"] == "Bet365"
    assert cob["1"]["casa_referencia"] == "Winamax"
    assert cob["1"]["cuota_referencia"] == "2.70"
    # R = 100·3.20 = 320; s = 320/2.60 ≈ 123.08; coste = s·(2.70−2.60); windfall = s·2.60 = 320.
    assert float(cob["1"]["coste"]) == pytest.approx(12.31, abs=0.05)
    assert float(cob["1"]["windfall"]) == pytest.approx(320.00, abs=0.05)
    assert op_x["promo"]["acumulable"] is True


def test_promo_excluye_la_casa_del_bono(tmp_path, capsys):
    # Luckia (bono) en la lista de promo: nunca se usa para cubrir (constitución nº 10).
    main(_args(tmp_path, "--promo", "Luckia,Bet365", "--json"))
    datos = json.loads(capsys.readouterr().out)
    op_x = next(o for o in datos["opciones"] if o["resultado"] == "X")
    cob = {c["resultado"]: c for c in op_x["promo"]["coberturas"]}
    assert cob["1"]["casa"] == "Bet365"


def test_lista_vacia_es_error(tmp_path, capsys):
    codigo = main(_args(tmp_path, "--promo", ""))
    assert codigo == 1
    assert "Error" in capsys.readouterr().err


def test_sin_promo_identico(tmp_path, capsys):
    codigo = main(_args(tmp_path))
    salida = capsys.readouterr().out
    assert codigo == 0
    assert "Promo" not in salida
