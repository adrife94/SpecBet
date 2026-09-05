"""T4: plazo y orden por coste (RF-9, RF-10, RF-14, RF-15, RF-16, RF-17)."""

from datetime import datetime
from decimal import Decimal

from betting.core import ConfigBonus, evaluar_bonus


def _c(v):
    return Decimal(str(v))


def _entrada(casa, uno=None, equis=None, dos=None):
    e = {"casa": casa}
    if uno is not None:
        e["1"] = _c(uno)
    if equis is not None:
        e["X"] = _c(equis)
    if dos is not None:
        e["2"] = _c(dos)
    return e


def _partido(nombre, *entradas, fecha=None):
    p = {"partido": nombre, "cuotas": list(entradas)}
    if fecha is not None:
        p["fecha"] = fecha
    return p


def _tres(nombre, fecha=None):
    return _partido(
        nombre,
        _entrada("Luckia", 2.10, 3.30, 2.50),
        _entrada("Bet365", 4.20, 3.60, 3.90),
        _entrada("Winamax", 4.10, 3.55, 3.95),
        fecha=fecha,
    )


def _config(**kwargs):
    kwargs.setdefault("casa", "Luckia")
    kwargs.setdefault("importe", _c("100"))
    kwargs.setdefault("cuota_minima", _c("1.5"))
    return ConfigBonus(**kwargs)


def test_fuera_de_plazo_descarta_el_partido():
    partido = _tres("A vs B", fecha="2026-09-20")
    resultado = evaluar_bonus([partido], _config(fecha_limite=datetime(2026, 9, 10)))
    assert resultado.opciones == []
    assert any(d.resultado is None and "plazo" in d.motivo.lower() for d in resultado.descartes)


def test_sin_fecha_con_limite_avisa_pero_evalua():
    partido = _tres("A vs B")  # sin fecha
    resultado = evaluar_bonus([partido], _config(fecha_limite=datetime(2026, 9, 10)))
    assert "A vs B" in resultado.avisos_sin_fecha
    assert resultado.opciones  # se evaluó igualmente


def test_sin_limite_ignora_fechas():
    partido = _tres("A vs B", fecha="2030-01-01")
    resultado = evaluar_bonus([partido], _config())
    assert resultado.avisos_sin_fecha == []
    assert resultado.opciones


def test_opciones_ordenadas_por_coste_ascendente():
    # "Barato" tiene cuotas de cobertura altas (coste menor/negativo) que "Caro".
    barato = _partido(
        "Barato",
        _entrada("Luckia", 2.10, 3.30, 2.50),
        _entrada("Bet365", 4.30, 3.80, 4.10),
    )
    caro = _partido(
        "Caro",
        _entrada("Luckia", 2.10, 3.30, 2.50),
        _entrada("Bet365", 3.20, 3.10, 2.90),
    )
    resultado = evaluar_bonus([caro, barato], _config())
    costes = [o.coste for o in resultado.opciones]
    assert costes == sorted(costes)
    assert costes[0] < costes[-1]
