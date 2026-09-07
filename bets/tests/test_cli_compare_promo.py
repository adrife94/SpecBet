"""T2: filtro de promo en compare (RF-2, RF-4, RF-16, RF-18, RF-22, RF-23)."""

import json
from pathlib import Path

import pytest

from betting.cli import main

CUOTAS = """
{"partidos": [
  {"partido": "A vs B", "cuotas": [
     {"casa": "Bet365", "1": 2.00, "X": 3.40, "2": 3.50},
     {"casa": "Winamax", "1": 2.10, "X": 3.30, "2": 3.60}]},
  {"partido": "C vs D", "cuotas": [
     {"casa": "Bet365", "1": 2.15, "X": 3.40, "2": 3.50},
     {"casa": "Winamax", "1": 2.10, "X": 3.30, "2": 3.60}]}
]}
"""


def _cuotas(tmp_path: Path) -> str:
    ruta = tmp_path / "cuotas.json"
    ruta.write_text(CUOTAS, encoding="utf-8")
    return str(ruta)


def test_promo_tabla_coste_referencia_y_tres_opciones(tmp_path, capsys):
    codigo = main(["compare", _cuotas(tmp_path), "--promo", "Bet365"])
    salida = capsys.readouterr().out
    assert codigo == 0
    assert "Promo" in salida
    assert "asegurar 1" in salida and "asegurar 2" in salida and "asegurar ambos" in salida
    assert "Winamax" in salida  # casa de referencia (RF-12)
    assert "coste" in salida
    assert "acumul" in salida  # aviso de windfalls acumulables (RF-15)


def test_promo_json_incluye_bloque_y_coste(tmp_path, capsys):
    codigo = main(["compare", _cuotas(tmp_path), "--promo", "Bet365", "--json"])
    salida = capsys.readouterr().out
    assert codigo == 0

    datos = json.loads(salida)
    ab = next(p for p in datos["partidos"] if p["partido"] == "A vs B")
    op1 = next(o for o in ab["promo"]["opciones"] if o["nombre"] == "asegurar_1")
    pata = op1["patas"][0]
    assert pata["casa"] == "Bet365"
    assert pata["cuota"] == "2.00"
    assert pata["casa_referencia"] == "Winamax"
    assert pata["cuota_referencia"] == "2.10"
    assert float(op1["coste"]) == pytest.approx(2.12, abs=0.01)  # caída de payout, sin windfall

    # C vs D: Bet365 ya es la mejor cuota del "1" → coste 0 (RF-13).
    cd = next(p for p in datos["partidos"] if p["partido"] == "C vs D")
    op1cd = next(o for o in cd["promo"]["opciones"] if o["nombre"] == "asegurar_1")
    assert op1cd["coste"] == "0.00"


def test_promo_sin_windfall_en_compare(tmp_path, capsys):
    main(["compare", _cuotas(tmp_path), "--promo", "Bet365", "--json"])
    datos = json.loads(capsys.readouterr().out)
    ab = next(p for p in datos["partidos"] if p["partido"] == "A vs B")
    for op in ab["promo"]["opciones"]:
        for pata in op["patas"]:
            assert "windfall" not in pata  # compare no maneja importes (RF-16)


def test_lista_vacia_es_error(tmp_path, capsys):
    codigo = main(["compare", _cuotas(tmp_path), "--promo", "  "])
    assert codigo == 1
    assert "Error" in capsys.readouterr().err


def test_sin_promo_identico_a_antes(tmp_path, capsys):
    codigo = main(["compare", _cuotas(tmp_path)])
    salida = capsys.readouterr().out
    assert codigo == 0
    assert "Promo" not in salida


def test_sin_promo_json_no_lleva_promo(tmp_path, capsys):
    main(["compare", _cuotas(tmp_path), "--json"])
    datos = json.loads(capsys.readouterr().out)
    assert all("promo" not in p for p in datos["partidos"])


def test_recordatorio_con_promo_por_stderr(tmp_path, capsys):
    main(["compare", _cuotas(tmp_path), "--promo", "Bet365"])
    assert "Recuerda" in capsys.readouterr().err  # RF-23
