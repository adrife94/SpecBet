"""T3: elección del resultado y restricciones (RF-6, RF-7, RF-9, RF-10, RF-12, RF-13)."""

from decimal import Decimal

from betting.core import Bono, mejor_jugada


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


def _partido(nombre, *entradas):
    return {"partido": nombre, "cuotas": list(entradas)}


LUCKIA_TRES = _partido(
    "A vs B",
    _entrada("Luckia", 3.60, 3.30, 2.10),
    _entrada("Bet365", 3.50, 3.40, 2.05),
    _entrada("Winamax", 3.55, 3.25, 2.08),
)


def _bono(**kwargs):
    kwargs.setdefault("casa", "Luckia")
    kwargs.setdefault("importe", Decimal("10"))
    return Bono(**kwargs)


def test_auto_elige_el_resultado_de_mayor_valor():
    # Jugar la freebet al "1" (cuota 3.60 en Luckia) deja más valor que en X o 2.
    jugada = mejor_jugada(LUCKIA_TRES, _bono())
    assert jugada.resultado_gratis == "1"


def test_resultado_fijado_usa_solo_ese():
    jugada = mejor_jugada(LUCKIA_TRES, _bono(resultado="2"))
    assert jugada.resultado_gratis == "2"


def test_rango_maximo_descarta_resultados_fuera_de_rango():
    # Con máx 3.0, solo el "2" (2.10) es admisible para la pata gratis.
    jugada = mejor_jugada(LUCKIA_TRES, _bono(cuota_max=Decimal("3.0")))
    assert jugada.resultado_gratis == "2"


def test_resultado_fijado_fuera_de_rango_no_se_propone():
    jugada = mejor_jugada(LUCKIA_TRES, _bono(resultado="1", cuota_max=Decimal("3.0")))
    assert jugada is None


def test_cobertura_excluye_la_casa_del_bono():
    # Luckia tiene la mejor cuota del "2" (5.00) pero es la casa del bono:
    # la cobertura del "2" debe ir a otra casa (Bet365, 2.05).
    partido = _partido(
        "A vs B",
        _entrada("Luckia", 3.60, 3.30, 5.00),
        _entrada("Bet365", 3.50, 3.40, 2.05),
    )
    jugada = mejor_jugada(partido, _bono(resultado="1"))
    cobertura_2 = next(p for p in jugada.patas if p.resultado == "2")
    assert cobertura_2.casa == "Bet365"
    assert cobertura_2.cuota == Decimal("2.05")


def test_casa_del_bono_normalizada_por_caja_y_espacios():
    # "  luckia " debe casar con la entrada "Luckia" del archivo (RF-16).
    jugada = mejor_jugada(LUCKIA_TRES, _bono(casa="  luckia ", resultado="1"))
    assert jugada is not None
    assert jugada.resultado_gratis == "1"


def test_resultado_no_cubrible_no_da_jugada():
    # Solo Luckia (la casa del bono) ofrece el "2": no hay con qué cubrirlo.
    partido = _partido(
        "A vs B",
        _entrada("Luckia", 3.60, 3.30, 2.10),
        _entrada("Bet365", 3.50, 3.40),
    )
    assert mejor_jugada(partido, _bono(resultado="1")) is None
