"""T3: filtro de promo en surebet sobre Formato A (RF-19, RF-22)."""

import json
from pathlib import Path

import pytest

from betting.cli import main

CUOTAS = """
{"partidos": [
  {"partido": "A vs B", "cuotas": [
     {"casa": "Bet365", "1": 2.00, "X": 3.40, "2": 3.50},
     {"casa": "Winamax", "1": 2.10, "X": 3.30, "2": 3.60},
     {"casa": "Codere", "1": 2.05, "X": 3.45, "2": 3.55}]}
]}
"""


def _cuotas(tmp_path: Path) -> str:
    ruta = tmp_path / "cuotas.json"
    ruta.write_text(CUOTAS, encoding="utf-8")
    return str(ruta)


def test_promo_tabla_con_coste_y_windfall(tmp_path, capsys):
    codigo = main(["surebet", _cuotas(tmp_path), "--inversion", "100", "--promo", "Bet365"])
    salida = capsys.readouterr().out
    assert codigo == 0
    assert "Promo" in salida
    assert "asegurar 1" in salida
    assert "coste" in salida and "windfall" in salida


def test_promo_json_reparto_asegurado(tmp_path, capsys):
    main(["surebet", _cuotas(tmp_path), "--inversion", "100", "--promo", "Bet365", "--json"])
    datos = json.loads(capsys.readouterr().out)

    ab = next(p for p in datos["partidos"] if p["partido"] == "A vs B")
    op1 = next(o for o in ab["promo"]["opciones"] if o["nombre"] == "asegurar_1")
    pata1 = next(p for p in op1["patas"] if p["resultado"] == "1")
    assert pata1["asegurada"] is True
    assert pata1["casas"] == ["Bet365"]
    assert pata1["casa_referencia"] == "Winamax"
    assert pata1["cuota_referencia"] == "2.10"
    # Reparto con la cuota asegurada (2.00): s1 = 100·(1/2.00)/Σ(1/c) ≈ 46.83.
    assert float(pata1["coste"]) == pytest.approx(4.68, abs=0.02)  # s1·(2.10−2.00)
    assert float(pata1["windfall"]) == pytest.approx(93.67, abs=0.05)  # s1·2.00

    # Las patas no aseguradas no llevan coste/windfall.
    pataX = next(p for p in op1["patas"] if p["resultado"] == "X")
    assert pataX["asegurada"] is False
    assert "coste" not in pataX


def test_lista_vacia_es_error(tmp_path, capsys):
    codigo = main(["surebet", _cuotas(tmp_path), "--inversion", "100", "--promo", ""])
    assert codigo == 1
    assert "Error" in capsys.readouterr().err


def test_sin_promo_sigue_leyendo_el_resumen_de_compare(tmp_path, capsys):
    # Sin --promo, surebet lee la salida de 'compare --json' como siempre.
    main(["compare", _cuotas(tmp_path), "--json"])
    resumen = capsys.readouterr().out
    ruta = tmp_path / "resumen.json"
    ruta.write_text(resumen, encoding="utf-8")

    codigo = main(["surebet", str(ruta), "--inversion", "100"])
    salida = capsys.readouterr().out
    assert codigo == 0
    assert "Promo" not in salida
