"""T5: CLI del comando multibonus (RF-1, RF-5, RF-29, RF-30, RF-31, RF-32)."""

import json
from pathlib import Path

from betting.cli import main

CUOTAS = """
{"partidos": [
  {"partido": "A vs B", "fecha": "2026-09-10", "cuotas": [
     {"casa": "Luckia",  "1": 2.0, "X": 3.0, "2": 4.0},
     {"casa": "Bet365",  "1": 2.0, "X": 3.0, "2": 4.0},
     {"casa": "Winamax", "1": 2.0, "X": 3.0, "2": 4.0},
     {"casa": "Codere",  "1": 2.0, "X": 3.0, "2": 4.0}]},
  {"partido": "E vs F", "fecha": "2026-09-11", "cuotas": [
     {"casa": "Luckia",  "1": 2.6, "X": 2.6, "2": 2.6},
     {"casa": "Bet365",  "1": 2.6, "X": 2.6, "2": 2.6},
     {"casa": "Winamax", "1": 2.6, "X": 2.6, "2": 2.6}]},
  {"partido": "C vs D", "cuotas": [
     {"casa": "Luckia",  "1": 2.0, "X": 3.0, "2": 4.0},
     {"casa": "Bet365",  "1": 2.0, "X": 3.0, "2": 4.0}]}
]}
"""


def _cuotas(tmp_path: Path) -> str:
    ruta = tmp_path / "cuotas.json"
    ruta.write_text(CUOTAS, encoding="utf-8")
    return str(ruta)


def _args(tmp_path, *extra):
    return [
        "multibonus",
        _cuotas(tmp_path),
        "--bono",
        "Luckia:100:1.5",
        "--bono",
        "Bet365:100:1.5",
        "--bono",
        "Winamax:100:1.5",
        *extra,
    ]


def test_tabla_con_patas_y_descartes(tmp_path, capsys):
    codigo = main(_args(tmp_path))
    salida = capsys.readouterr().out
    assert codigo == 0
    assert "Multibono" in salida
    assert "Opciones" in salida
    assert "pérdida" in salida
    assert "bono" in salida and "relleno" in salida
    assert "Descartados" in salida  # C vs D: falta Winamax


def test_json_parseable_y_coherente(tmp_path, capsys):
    codigo = main(_args(tmp_path, "--json"))
    salida = capsys.readouterr().out
    assert codigo == 0

    datos = json.loads(salida)
    assert datos["version"] == 1
    assert len(datos["bonos"]) == 3
    # Opciones ordenadas por pérdida ascendente (A vs B < E vs F).
    perdidas = [float(o["perdida"]) for o in datos["opciones"]]
    assert perdidas == sorted(perdidas)
    opcion = datos["opciones"][0]
    for clave in ("partido", "R", "dinero_real", "perdida", "perdida_pct", "neto", "patas"):
        assert clave in opcion
    assert any(d["partido"] == "C vs D" for d in datos["descartes"])


def test_bonos_por_archivo(tmp_path, capsys):
    bonos = tmp_path / "bonos.json"
    bonos.write_text(
        '{"bonos": ['
        '{"casa": "Luckia", "importe": 100, "min": 1.5},'
        '{"casa": "Bet365", "importe": 100, "min": 1.5},'
        '{"casa": "Winamax", "importe": 100, "min": 1.5}]}',
        encoding="utf-8",
    )
    codigo = main(["multibonus", _cuotas(tmp_path), "--bonos", str(bonos)])
    salida = capsys.readouterr().out
    assert codigo == 0
    assert "Multibono" in salida


def test_menos_de_dos_bonos_error_y_salida_1(tmp_path, capsys):
    codigo = main(["multibonus", _cuotas(tmp_path), "--bono", "Luckia:100:1.5"])
    assert codigo == 1
    assert "Error" in capsys.readouterr().err


def test_mas_de_tres_bonos_error_y_salida_1(tmp_path, capsys):
    codigo = main(
        [
            "multibonus",
            _cuotas(tmp_path),
            "--bono",
            "Luckia:100:1.5",
            "--bono",
            "Bet365:100:1.5",
            "--bono",
            "Winamax:100:1.5",
            "--bono",
            "Codere:100:1.5",
        ]
    )
    assert codigo == 1
    assert "Error" in capsys.readouterr().err


def test_bono_y_bonos_a_la_vez_error_y_salida_1(tmp_path, capsys):
    bonos = tmp_path / "bonos.json"
    bonos.write_text('{"bonos": []}', encoding="utf-8")
    codigo = main(_args(tmp_path, "--bonos", str(bonos)))
    assert codigo == 1
    assert "Error" in capsys.readouterr().err


def test_sin_bonos_error_y_salida_1(tmp_path, capsys):
    codigo = main(["multibonus", _cuotas(tmp_path)])
    assert codigo == 1
    assert "Error" in capsys.readouterr().err


def test_bono_mal_formado_error_y_salida_1(tmp_path, capsys):
    codigo = main(
        ["multibonus", _cuotas(tmp_path), "--bono", "Luckia-100-1.5", "--bono", "Bet365:100:1.5"]
    )
    assert codigo == 1
    assert "Error" in capsys.readouterr().err


def test_archivo_corrupto_error_y_salida_1(tmp_path, capsys):
    ruta = tmp_path / "roto.json"
    ruta.write_text("{ no es json", encoding="utf-8")
    codigo = main(
        ["multibonus", str(ruta), "--bono", "Luckia:100:1.5", "--bono", "Bet365:100:1.5"]
    )
    assert codigo == 1
    assert "Error" in capsys.readouterr().err


def test_sin_partidos_mensaje_y_salida_0(tmp_path, capsys):
    ruta = tmp_path / "vacio.json"
    ruta.write_text('{"partidos": []}', encoding="utf-8")
    codigo = main(
        ["multibonus", str(ruta), "--bono", "Luckia:100:1.5", "--bono", "Bet365:100:1.5"]
    )
    assert codigo == 0
    assert "No hay partidos" in capsys.readouterr().out


def test_sin_opciones_validas_mensaje_y_salida_0(tmp_path, capsys):
    # Falta Winamax en el único partido → sin opciones válidas.
    ruta = tmp_path / "solo.json"
    ruta.write_text(
        '{"partidos": [{"partido": "Solo", "cuotas": ['
        '{"casa": "Luckia", "1": 2.0, "X": 3.0, "2": 4.0},'
        '{"casa": "Bet365", "1": 2.0, "X": 3.0, "2": 4.0}]}]}',
        encoding="utf-8",
    )
    codigo = main(
        [
            "multibonus",
            str(ruta),
            "--bono",
            "Luckia:100:1.5",
            "--bono",
            "Bet365:100:1.5",
            "--bono",
            "Winamax:100:1.5",
        ]
    )
    salida = capsys.readouterr().out
    assert codigo == 0
    assert "No hay opciones válidas" in salida


def test_apalancamiento_fuera_de_plazo(tmp_path, capsys):
    codigo = main(_args(tmp_path, "--apalancamiento", "2026-09-05"))
    salida = capsys.readouterr().out
    assert codigo == 0
    assert "plazo" in salida.lower()


def test_aviso_sin_fecha_por_stderr(tmp_path, capsys):
    # C vs D no tiene fecha; con apalancamiento se avisa.
    main(_args(tmp_path, "--apalancamiento", "2026-09-30"))
    assert "no tiene fecha" in capsys.readouterr().err


def test_recordatorio_de_cuotas_por_stderr(tmp_path, capsys):
    main(_args(tmp_path))
    assert "Recuerda" in capsys.readouterr().err
