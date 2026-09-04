"""T5: marcado de partido incompleto (RF-9, RF-14)."""

from decimal import Decimal

from betting.core import es_incompleto, mejores_de_partido


def _partido(nombre: str, cuotas: list[dict]) -> dict:
    return {"partido": nombre, "cuotas": cuotas}


def _evaluar(partido: dict) -> bool:
    mejores, _ = mejores_de_partido(partido)
    return es_incompleto(partido, mejores)


def test_partido_completo_no_es_incompleto():
    partido = _partido(
        "A vs B",
        [
            {"casa": "Bet365", "1": Decimal("2.10"), "X": Decimal("3.30"), "2": Decimal("3.50")},
            {"casa": "Codere", "1": Decimal("2.05"), "X": Decimal("3.40"), "2": Decimal("3.60")},
        ],
    )
    assert _evaluar(partido) is False


def test_incompleto_si_falta_un_resultado_en_todas_las_casas():
    partido = _partido(
        "A vs B",
        [
            {"casa": "Bet365", "1": Decimal("2.10"), "2": Decimal("3.50")},  # sin X
            {"casa": "Codere", "1": Decimal("2.05"), "2": Decimal("3.60")},  # sin X
        ],
    )
    assert _evaluar(partido) is True


def test_incompleto_con_una_sola_casa_aunque_tenga_los_tres():
    partido = _partido(
        "A vs B",
        [{"casa": "Bet365", "1": Decimal("2.10"), "X": Decimal("3.30"), "2": Decimal("3.50")}],
    )
    assert _evaluar(partido) is True


def test_dos_casas_que_se_complementan_es_completo():
    partido = _partido(
        "A vs B",
        [
            {"casa": "Bet365", "1": Decimal("2.10"), "X": Decimal("3.30")},  # sin 2
            {"casa": "Codere", "2": Decimal("3.60")},  # solo 2
        ],
    )
    assert _evaluar(partido) is False


def test_incompleto_si_la_segunda_casa_solo_trae_cuota_invalida():
    partido = _partido(
        "A vs B",
        [
            {"casa": "Bet365", "1": Decimal("2.10"), "X": Decimal("3.30"), "2": Decimal("3.50")},
            {"casa": "Codere", "1": "N/A"},  # sin cuota válida -> no cuenta como 2ª casa
        ],
    )
    assert _evaluar(partido) is True
