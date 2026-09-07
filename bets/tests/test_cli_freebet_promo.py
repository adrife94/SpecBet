"""T4: filtro de promo en freebet (RF-20, RF-22)."""

import json
from pathlib import Path

import pytest

from betting.cli import main

# Luckia (bono): mejor cuota en la X → pata gratis X; el 1 y el 2 son coberturas.
CUOTAS = """
{"partidos": [
  {"partido": "A vs B", "cuotas": [
     {"casa": "Luckia",  "1": 2.00, "X": 3.50, "2": 2.20},
     {"casa": "Bet365",  "1": 2.60, "X": 3.30, "2": 3.40},
     {"casa": "Winamax", "1": 2.70, "X": 3.20, "2": 3.50}]}
]}
"""


def _cuotas(tmp_path: Path, contenido: str = CUOTAS) -> str:
    ruta = tmp_path / "cuotas.json"
    ruta.write_text(contenido, encoding="utf-8")
    return str(ruta)


def _args(tmp_path, *extra):
    return ["freebet", _cuotas(tmp_path), "--casa", "Luckia", "--importe", "10", *extra]


def test_promo_tabla_coberturas_de_ganar(tmp_path, capsys):
    codigo = main(_args(tmp_path, "--promo", "Bet365"))
    salida = capsys.readouterr().out
    assert codigo == 0
    assert "Promo" in salida
    assert "cobertura 1" in salida and "cobertura 2" in salida
    assert "Bet365" in salida
    assert "coste" in salida and "windfall" in salida
    assert "acumul" in salida  # ambas patas de ganar son coberturas (RF-15)


def test_promo_json_coste_y_windfall(tmp_path, capsys):
    main(_args(tmp_path, "--promo", "Bet365", "--json"))
    datos = json.loads(capsys.readouterr().out)

    partido = datos["bonos"][0]["partidos"][0]
    cob = {c["resultado"]: c for c in partido["promo"]["coberturas"]}
    assert cob["1"]["casa"] == "Bet365"
    assert cob["1"]["casa_referencia"] == "Winamax"  # mejor casa distinta sin promo
    assert cob["1"]["cuota_referencia"] == "2.70"
    # R = 10·(3.50−1) = 25; s = 25/2.60 ≈ 9.62; coste = s·(2.70−2.60); windfall = s·2.60 = 25.
    assert float(cob["1"]["coste"]) == pytest.approx(0.96, abs=0.03)
    assert float(cob["1"]["windfall"]) == pytest.approx(25.00, abs=0.02)
    assert partido["promo"]["acumulable"] is True


def test_promo_excluye_la_casa_del_bono(tmp_path, capsys):
    # Luckia (bono) está en la lista de promo y tiene la mejor cuota del "1" (3.00),
    # pero la cobertura no puede ir en la casa del bono → usa Bet365 (constitución nº 10).
    contenido = """
    {"partidos": [
      {"partido": "A vs B", "cuotas": [
         {"casa": "Luckia",  "1": 3.00, "X": 3.50, "2": 2.20},
         {"casa": "Bet365",  "1": 2.60, "X": 3.30, "2": 3.40},
         {"casa": "Winamax", "1": 2.70, "X": 3.20, "2": 3.50}]}
    ]}
    """
    main(
        ["freebet", _cuotas(tmp_path, contenido), "--casa", "Luckia", "--importe", "10",
         "--promo", "Luckia,Bet365", "--json"]
    )
    datos = json.loads(capsys.readouterr().out)
    cob = {c["resultado"]: c for c in datos["bonos"][0]["partidos"][0]["promo"]["coberturas"]}
    assert cob["1"]["casa"] == "Bet365"  # nunca Luckia (la del bono)


def test_lista_vacia_es_error(tmp_path, capsys):
    codigo = main(_args(tmp_path, "--promo", ""))
    assert codigo == 1
    assert "Error" in capsys.readouterr().err


def test_sin_promo_identico(tmp_path, capsys):
    codigo = main(_args(tmp_path))
    salida = capsys.readouterr().out
    assert codigo == 0
    assert "Promo" not in salida
