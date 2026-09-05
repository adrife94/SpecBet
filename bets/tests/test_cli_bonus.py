"""T5: CLI del comando bonus (RF-1, RF-8, RF-21..RF-27)."""

import json
from pathlib import Path

from betting.cli import main

CUOTAS = """
{"partidos": [
  {"partido": "A vs B", "fecha": "2026-09-10", "cuotas": [
     {"casa": "Luckia",  "1": 2.10, "X": 3.30, "2": 2.50},
     {"casa": "Bet365",  "1": 4.20, "X": 3.60, "2": 3.90},
     {"casa": "Winamax", "1": 4.10, "X": 3.55, "2": 3.95}]},
  {"partido": "C vs D", "cuotas": [
     {"casa": "Bet365",  "1": 2.0, "X": 3.3, "2": 3.8},
     {"casa": "Winamax", "1": 2.05, "X": 3.2, "2": 3.9}]}
]}
"""


def _cuotas(tmp_path: Path) -> str:
    ruta = tmp_path / "cuotas.json"
    ruta.write_text(CUOTAS, encoding="utf-8")
    return str(ruta)


def _args(tmp_path, *extra):
    return ["bonus", _cuotas(tmp_path), "--casa", "Luckia", "--importe", "100", "--min", "1.5", *extra]


def test_tabla_opciones_ordenadas_con_cuota_anclada(tmp_path, capsys):
    codigo = main(_args(tmp_path))
    salida = capsys.readouterr().out
    assert codigo == 0
    assert "Bono: Luckia" in salida
    assert "Opciones" in salida
    assert "anclar" in salida and "cobertura" in salida
    assert "coste" in salida
    assert "Descartados" in salida  # C vs D: Luckia no participa


def test_json_parseable_y_coherente(tmp_path, capsys):
    codigo = main(_args(tmp_path, "--json"))
    salida = capsys.readouterr().out
    assert codigo == 0

    datos = json.loads(salida)
    assert datos["version"] == 1
    assert datos["casa"] == "Luckia"
    assert datos["importe"] == "100.00"
    # opciones ordenadas por coste ascendente
    costes = [float(o["coste"]) for o in datos["opciones"]]
    assert costes == sorted(costes)
    opcion = datos["opciones"][0]
    assert len(opcion["cobertura"]) == 2
    assert any(d["partido"] == "C vs D" for d in datos["descartes"])


def test_importe_invalido_error_y_salida_1(tmp_path, capsys):
    codigo = main(["bonus", _cuotas(tmp_path), "--casa", "Luckia", "--importe", "0", "--min", "1.5"])
    assert codigo == 1
    assert "Error" in capsys.readouterr().err


def test_cuota_minima_invalida_error_y_salida_1(tmp_path, capsys):
    codigo = main(["bonus", _cuotas(tmp_path), "--casa", "Luckia", "--importe", "100", "--min", "1"])
    assert codigo == 1
    assert "Error" in capsys.readouterr().err


def test_casa_no_indicada_error_y_salida_1(tmp_path, capsys):
    codigo = main(["bonus", _cuotas(tmp_path), "--importe", "100", "--min", "1.5"])
    assert codigo == 1
    assert "Error" in capsys.readouterr().err


def test_archivo_corrupto_error_y_salida_1(tmp_path, capsys):
    ruta = tmp_path / "roto.json"
    ruta.write_text("{ no es json", encoding="utf-8")
    codigo = main(["bonus", str(ruta), "--casa", "Luckia", "--importe", "100", "--min", "1.5"])
    assert codigo == 1
    assert "Error" in capsys.readouterr().err


def test_sin_partidos_mensaje_y_salida_0(tmp_path, capsys):
    ruta = tmp_path / "vacio.json"
    ruta.write_text('{"partidos": []}', encoding="utf-8")
    codigo = main(["bonus", str(ruta), "--casa", "Luckia", "--importe", "100", "--min", "1.5"])
    assert codigo == 0
    assert "No hay partidos" in capsys.readouterr().out


def test_sin_opciones_validas_mensaje_y_salida_0(tmp_path, capsys):
    # Solo Luckia participa → ningún resultado es cubrible en casa distinta.
    ruta = tmp_path / "solo.json"
    ruta.write_text(
        '{"partidos": [{"partido": "Solo", "cuotas": [{"casa": "Luckia", "1": 2.1, "X": 3.3, "2": 2.5}]}]}',
        encoding="utf-8",
    )
    codigo = main(["bonus", str(ruta), "--casa", "Luckia", "--importe", "100", "--min", "1.5"])
    salida = capsys.readouterr().out
    assert codigo == 0
    assert "No hay opciones válidas" in salida


def test_fuera_de_plazo_aparece_en_descartes(tmp_path, capsys):
    codigo = main(_args(tmp_path, "--fecha-limite", "2026-09-01"))
    salida = capsys.readouterr().out
    assert codigo == 0
    assert "plazo" in salida.lower()


def test_aviso_sin_fecha_por_stderr(tmp_path, capsys):
    # C vs D no tiene fecha; con límite se avisa.
    main(_args(tmp_path, "--fecha-limite", "2026-09-30"))
    assert "no tiene fecha" in capsys.readouterr().err


def test_recordatorio_de_cuotas_por_stderr(tmp_path, capsys):
    main(_args(tmp_path))
    assert "Recuerda" in capsys.readouterr().err
