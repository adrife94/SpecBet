"""T1: el esqueleto de la CLI expone el subcomando `compare`."""

import pytest

from betting.cli import build_parser


def test_compare_parsea_archivo_y_json_por_defecto_false():
    parser = build_parser()
    args = parser.parse_args(["compare", "partidos.json"])
    assert args.comando == "compare"
    assert args.archivo == "partidos.json"
    assert args.json is False


def test_compare_acepta_flag_json():
    parser = build_parser()
    args = parser.parse_args(["compare", "partidos.json", "--json"])
    assert args.json is True


def test_compare_sin_archivo_muestra_error_de_uso():
    parser = build_parser()
    with pytest.raises(SystemExit):
        parser.parse_args(["compare"])
