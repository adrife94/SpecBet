"""T6/T7: CLI del comando freebet (RF-1, RF-5, RF-16..RF-22, RF-30, RF-31)."""

import json
from pathlib import Path

from betting.cli import main

CUOTAS = """
{"partidos": [
  {"partido": "A vs B", "fecha": "2026-09-10", "cuotas": [
     {"casa": "Luckia",   "1": 3.60, "X": 3.30, "2": 2.10},
     {"casa": "Sportium", "1": 3.55, "X": 3.20, "2": 2.05},
     {"casa": "Bet365",   "1": 3.50, "X": 3.40, "2": 2.20},
     {"casa": "Winamax",  "1": 3.45, "X": 3.25, "2": 2.15}]},
  {"partido": "C vs D", "cuotas": [
     {"casa": "Bet365",  "1": 2.0, "X": 3.0, "2": 4.0},
     {"casa": "Winamax", "1": 2.1, "X": 3.1, "2": 3.9}]}
]}
"""


def _cuotas(tmp_path: Path) -> str:
    ruta = tmp_path / "cuotas.json"
    ruta.write_text(CUOTAS, encoding="utf-8")
    return str(ruta)


def _bonos(tmp_path: Path, contenido: str) -> str:
    ruta = tmp_path / "bonos.json"
    ruta.write_text(contenido, encoding="utf-8")
    return str(ruta)


# --- T6: tabla de un bono por flags (RF-1, RF-5) ---


def test_tabla_un_bono_listado_con_valor_y_conversion(tmp_path, capsys):
    codigo = main(["freebet", _cuotas(tmp_path), "--casa", "Luckia", "--importe", "10"])
    salida = capsys.readouterr().out
    assert codigo == 0
    assert "Bono: Luckia" in salida
    assert "A vs B" in salida
    assert "conversión" in salida
    assert "★" in salida  # jugada recomendada marcada
    assert "gratis" in salida and "cobertura" in salida
    assert "no jugable" in salida  # C vs D: Luckia no participa
    assert "Valor total del lote" in salida


# --- T7: lote, json, validaciones y avisos ---


def test_lote_dos_bonos_valor_total(tmp_path, capsys):
    bonos = _bonos(
        tmp_path,
        '{"bonos": [{"casa": "Luckia", "importe": 10}, {"casa": "Sportium", "importe": 10}]}',
    )
    codigo = main(["freebet", _cuotas(tmp_path), "--bonos", bonos])
    salida = capsys.readouterr().out
    assert codigo == 0
    assert "Bono: Luckia" in salida
    assert "Bono: Sportium" in salida
    assert "Valor total del lote" in salida


def test_json_parseable_y_coherente(tmp_path, capsys):
    codigo = main(["freebet", _cuotas(tmp_path), "--casa", "Luckia", "--importe", "10", "--json"])
    salida = capsys.readouterr().out
    assert codigo == 0

    datos = json.loads(salida)
    assert datos["version"] == 1
    assert isinstance(datos["valor_total"], str)
    bono = datos["bonos"][0]
    assert bono["casa"] == "Luckia"
    assert bono["recomendada"] == "A vs B"
    # primer partido: jugable con 3 patas (1 gratis + 2 cobertura)
    jugable = bono["partidos"][0]
    assert jugable["jugable"] is True
    assert jugable["patas"][0]["tipo"] == "gratis"
    assert len(jugable["patas"]) == 3
    # último partido: no jugable, patas null
    no_jugable = bono["partidos"][-1]
    assert no_jugable["jugable"] is False
    assert no_jugable["patas"] is None


def test_importe_invalido_error_y_salida_1(tmp_path, capsys):
    codigo = main(["freebet", _cuotas(tmp_path), "--casa", "Luckia", "--importe", "0"])
    assert codigo == 1
    assert "Error" in capsys.readouterr().err


def test_sin_casa_ni_bonos_error_y_salida_1(tmp_path, capsys):
    codigo = main(["freebet", _cuotas(tmp_path)])
    assert codigo == 1
    assert "Error" in capsys.readouterr().err


def test_archivo_corrupto_error_y_salida_1(tmp_path, capsys):
    ruta = tmp_path / "roto.json"
    ruta.write_text("{ no es json", encoding="utf-8")
    codigo = main(["freebet", str(ruta), "--casa", "Luckia", "--importe", "10"])
    assert codigo == 1
    assert "Error" in capsys.readouterr().err


def test_sin_partidos_mensaje_y_salida_0(tmp_path, capsys):
    ruta = tmp_path / "vacio.json"
    ruta.write_text('{"partidos": []}', encoding="utf-8")
    codigo = main(["freebet", str(ruta), "--casa", "Luckia", "--importe", "10"])
    assert codigo == 0
    assert "No hay partidos" in capsys.readouterr().out


def test_fuera_de_plazo_marca_no_jugable(tmp_path, capsys):
    # A vs B se juega 2026-09-10; con límite 2026-09-01 queda fuera de plazo.
    codigo = main(
        ["freebet", _cuotas(tmp_path), "--casa", "Luckia", "--importe", "10",
         "--fecha-limite", "2026-09-01"]
    )
    salida = capsys.readouterr().out
    assert codigo == 0
    assert "plazo" in salida.lower()


def test_aviso_sin_fecha_por_stderr(tmp_path, capsys):
    # C vs D no tiene fecha; con límite se evalúa igual pero avisa.
    main(
        ["freebet", _cuotas(tmp_path), "--casa", "Bet365", "--importe", "10",
         "--fecha-limite", "2026-09-30"]
    )
    assert "no tiene fecha" in capsys.readouterr().err


def test_recordatorio_de_cuotas_por_stderr(tmp_path, capsys):
    main(["freebet", _cuotas(tmp_path), "--casa", "Luckia", "--importe", "10"])
    assert "Recuerda" in capsys.readouterr().err


def test_colision_entre_dos_bonos_avisa(tmp_path, capsys):
    bonos = _bonos(
        tmp_path,
        '{"bonos": [{"casa": "Luckia", "importe": 10, "resultado": "1"},'
        ' {"casa": "Sportium", "importe": 10, "resultado": "1"}]}',
    )
    main(["freebet", _cuotas(tmp_path), "--bonos", bonos])
    assert "consolidar" in capsys.readouterr().err
