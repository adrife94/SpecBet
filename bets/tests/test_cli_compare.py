"""T8: comando `compare` — tabla, avisos, errores y códigos de salida
(RF-1, RF-8, RF-11, RF-12)."""

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


def test_tabla_basica(tmp_path, capsys):
    ruta = _escribir(tmp_path, '{"partidos": [' + COMPLETO + "]}")
    codigo = main(["compare", ruta])
    salida = capsys.readouterr().out
    assert codigo == 0
    assert "% pago" in salida
    assert "95.41" in salida
    assert "Madrid vs Barça" in salida
    assert "Codere" in salida


def test_incompleto_va_al_final_con_guion(tmp_path, capsys):
    ruta = _escribir(tmp_path, '{"partidos": [' + INCOMPLETO + "," + COMPLETO + "]}")
    codigo = main(["compare", ruta])
    salida = capsys.readouterr().out
    assert codigo == 0
    assert salida.index("Madrid vs Barça") < salida.index("Sevilla vs Betis")
    assert "—" in salida  # celdas/payout sin dato del incompleto


def test_empate_muestra_ambas_casas(tmp_path, capsys):
    partido = (
        '{"partido": "A vs B", "cuotas": ['
        '{"casa": "Bet365", "1": 2.10, "X": 3.30, "2": 3.50},'
        '{"casa": "Codere", "1": 2.10, "X": 3.20, "2": 3.60}]}'
    )
    ruta = _escribir(tmp_path, '{"partidos": [' + partido + "]}")
    main(["compare", ruta])
    salida = capsys.readouterr().out
    assert "Bet365/Codere" in salida


def test_archivo_vacio_mensaje_y_salida_0(tmp_path, capsys):
    ruta = _escribir(tmp_path, '{"partidos": []}')
    codigo = main(["compare", ruta])
    salida = capsys.readouterr().out
    assert codigo == 0
    assert "No hay partidos que comparar." in salida


def test_archivo_corrupto_error_y_salida_1(tmp_path, capsys):
    ruta = _escribir(tmp_path, "{ no es json")
    codigo = main(["compare", ruta])
    err = capsys.readouterr().err
    assert codigo == 1
    assert "Error" in err


def test_partido_duplicado_error_y_salida_1(tmp_path, capsys):
    ruta = _escribir(tmp_path, '{"partidos": [' + COMPLETO + "," + COMPLETO + "]}")
    codigo = main(["compare", ruta])
    err = capsys.readouterr().err
    assert codigo == 1
    assert "Error" in err


def test_cuota_invalida_avisa_por_stderr_y_sigue(tmp_path, capsys):
    partido = (
        '{"partido": "A vs B", "cuotas": ['
        '{"casa": "Bet365", "1": "N/A", "X": 3.30, "2": 3.50},'
        '{"casa": "Codere", "1": 2.05, "X": 3.40, "2": 3.60}]}'
    )
    ruta = _escribir(tmp_path, '{"partidos": [' + partido + "]}")
    codigo = main(["compare", ruta])
    capturado = capsys.readouterr()
    assert codigo == 0
    assert "Aviso" in capturado.err
    assert "Bet365" in capturado.err
    assert "A vs B" in capturado.out  # la tabla se sigue mostrando
