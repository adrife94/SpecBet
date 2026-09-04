"""T7: ordenación de partidos (RF-6, RF-10, RF-17)."""

from decimal import Decimal

from betting.core import comparar


def _uniforme(nombre: str, cuota: str, casas: tuple[str, ...] = ("Bet365", "Codere")) -> dict:
    """Partido completo con la misma cuota en 1/X/2 y en dos casas."""
    fila = {"1": Decimal(cuota), "X": Decimal(cuota), "2": Decimal(cuota)}
    return {"partido": nombre, "cuotas": [{"casa": c, **fila} for c in casas]}


def _incompleto(nombre: str) -> dict:
    return {"partido": nombre, "cuotas": [{"casa": "Bet365", "1": Decimal("2.00")}]}


def test_orden_completos_desc_luego_incompletos():
    partidos = [
        _uniforme("Bajo", "2.90"),        # payout ~96.67
        _incompleto("Inc1"),
        _uniforme("Alto", "3.10"),        # payout ~103.33 (>100)
        _incompleto("Inc2"),
        _uniforme("Medio", "3.00"),       # payout 100.00
    ]
    orden = [ev.nombre for ev in comparar(partidos)]
    assert orden == ["Alto", "Medio", "Bajo", "Inc1", "Inc2"]


def test_incompletos_conservan_orden_de_entrada():
    partidos = [_incompleto("Inc1"), _uniforme("Comp", "3.00"), _incompleto("Inc2")]
    orden = [ev.nombre for ev in comparar(partidos)]
    assert orden == ["Comp", "Inc1", "Inc2"]


def test_surebet_no_recibe_marca_especial_solo_se_ordena():
    partidos = [_uniforme("Normal", "2.90"), _uniforme("Surebet", "3.10")]
    resultado = comparar(partidos)
    primero = resultado[0]
    assert primero.nombre == "Surebet"
    assert primero.payout > Decimal("100")
    assert primero.incompleto is False
    # el partido no expone ninguna marca de arbitraje: es un PartidoEvaluado normal
    assert not hasattr(primero, "surebet")
