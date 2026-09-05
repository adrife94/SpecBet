"""T4: evaluación por partido, plazo, orden y recomendada (RF-14, RF-15, RF-24..RF-27, RF-33)."""

from datetime import datetime
from decimal import Decimal

from betting.core import Bono, evaluar_bono, evaluar_partido_bono


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
        _entrada("Luckia", 3.60, 3.30, 2.10),
        _entrada("Bet365", 3.50, 3.40, 2.05),
        _entrada("Winamax", 3.55, 3.25, 2.08),
        fecha=fecha,
    )


def _bono(**kwargs):
    kwargs.setdefault("casa", "Luckia")
    kwargs.setdefault("importe", Decimal("10"))
    return Bono(**kwargs)


def test_casa_del_bono_ausente_no_jugable():
    partido = _partido("A vs B", _entrada("Bet365", 3.50, 3.40, 2.05))
    ev = evaluar_partido_bono(partido, _bono())
    assert ev.jugable is False
    assert "no participa" in ev.motivo


def test_fuera_de_plazo_no_jugable():
    partido = _tres("A vs B", fecha="2026-09-12")
    ev = evaluar_partido_bono(partido, _bono(fecha_limite=datetime(2026, 9, 10)))
    assert ev.jugable is False
    assert "plazo" in ev.motivo.lower()


def test_dentro_de_plazo_es_jugable():
    partido = _tres("A vs B", fecha="2026-09-08")
    ev = evaluar_partido_bono(partido, _bono(fecha_limite=datetime(2026, 9, 10)))
    assert ev.jugable is True
    assert ev.aviso_sin_fecha is False


def test_sin_fecha_con_limite_avisa_pero_se_evalua():
    partido = _tres("A vs B")  # sin fecha
    ev = evaluar_partido_bono(partido, _bono(fecha_limite=datetime(2026, 9, 10)))
    assert ev.jugable is True
    assert ev.aviso_sin_fecha is True


def test_sin_limite_ignora_fechas():
    partido = _tres("A vs B", fecha="2030-01-01")  # muy posterior, pero sin límite
    ev = evaluar_partido_bono(partido, _bono())
    assert ev.jugable is True
    assert ev.aviso_sin_fecha is False


def test_orden_por_valor_y_recomendada_primera():
    # Cuotas más altas en "Bueno" → mayor valor extraído que en "Malo".
    bueno = _partido(
        "Bueno",
        _entrada("Luckia", 5.00, 4.00, 3.50),
        _entrada("Bet365", 4.80, 4.20, 3.40),
    )
    malo = _tres("Malo")
    sin_casa = _partido("SinCasa", _entrada("Bet365", 2.0, 3.0, 4.0))

    resultado = evaluar_bono([malo, sin_casa, bueno], _bono())
    nombres = [e.partido for e in resultado.partidos]
    assert nombres == ["Bueno", "Malo", "SinCasa"]
    assert resultado.recomendada.partido == "Bueno"
    assert resultado.sin_plan is False


def test_partido_fijado_evalua_solo_ese():
    resultado = evaluar_bono(
        [_tres("Uno"), _tres("Dos"), _tres("Tres")], _bono(partido="Dos")
    )
    assert [e.partido for e in resultado.partidos] == ["Dos"]
    assert resultado.recomendada.partido == "Dos"


def test_sin_ninguna_jugada_marca_sin_plan():
    sin_casa = _partido("SinCasa", _entrada("Bet365", 2.0, 3.0, 4.0))
    resultado = evaluar_bono([sin_casa], _bono())
    assert resultado.sin_plan is True
    assert resultado.recomendada is None
    assert resultado.valor_extraido is None
