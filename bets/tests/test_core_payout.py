"""T6: cálculo del % de pago con Decimal (RF-3)."""

from decimal import ROUND_HALF_UP, Decimal

from betting.core import evaluar_partido


def _partido(nombre: str, cuotas: list[dict]) -> dict:
    return {"partido": nombre, "cuotas": cuotas}


def _dos_decimales(valor: Decimal) -> Decimal:
    return valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def test_caso_verificado_95_41():
    partido = _partido(
        "A vs B",
        [
            {"casa": "Bet365", "1": Decimal("2.10"), "X": Decimal("3.30"), "2": Decimal("3.50")},
            {"casa": "Codere", "1": Decimal("2.05"), "X": Decimal("3.40"), "2": Decimal("3.60")},
        ],
    )
    ev = evaluar_partido(partido)
    assert ev.incompleto is False
    # mejores: 2.10 / 3.40 / 3.60
    assert _dos_decimales(ev.payout) == Decimal("95.41")


def test_payout_no_se_redondea_en_el_core():
    partido = _partido(
        "A vs B",
        [
            {"casa": "Bet365", "1": Decimal("2.10"), "X": Decimal("3.30"), "2": Decimal("3.50")},
            {"casa": "Codere", "1": Decimal("2.05"), "X": Decimal("3.40"), "2": Decimal("3.60")},
        ],
    )
    ev = evaluar_partido(partido)
    # conserva precisión: no coincide con su versión a dos decimales
    assert ev.payout != Decimal("95.41")
    assert Decimal("95.41") < ev.payout < Decimal("95.42")


def test_payout_exacto_100_sin_margen():
    partido = _partido(
        "A vs B",
        [
            {"casa": "Bet365", "1": Decimal("3.00"), "X": Decimal("3.00"), "2": Decimal("3.00")},
            {"casa": "Codere", "1": Decimal("3.00"), "X": Decimal("3.00"), "2": Decimal("3.00")},
        ],
    )
    ev = evaluar_partido(partido)
    assert _dos_decimales(ev.payout) == Decimal("100.00")


def test_partido_incompleto_no_tiene_payout():
    partido = _partido(
        "A vs B",
        [{"casa": "Bet365", "1": Decimal("2.10"), "X": Decimal("3.30"), "2": Decimal("3.50")}],
    )
    ev = evaluar_partido(partido)
    assert ev.incompleto is True
    assert ev.payout is None
