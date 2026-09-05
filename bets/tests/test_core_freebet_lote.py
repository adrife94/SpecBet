"""T5: lote de bonos independientes (RF-28, RF-29, RF-30, RF-31, RF-32)."""

from decimal import Decimal

from betting.core import Bono, evaluar_lote

DOS = Decimal("0.01")


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


def _bono(casa, importe, **kwargs):
    return Bono(casa=casa, importe=_c(importe), **kwargs)


PARTIDO = _partido(
    "A vs B",
    _entrada("Luckia", 3.60, 3.30, 2.10),
    _entrada("Sportium", 3.55, 3.20, 2.05),
    _entrada("Bet365", 3.50, 3.40, 2.20),
    _entrada("Winamax", 3.45, 3.25, 2.15),
)


def test_valor_total_y_conversion_total():
    lote = evaluar_lote([PARTIDO], [_bono("Luckia", 10), _bono("Sportium", 20)])
    r0, r1 = lote.resultados
    assert lote.valor_total == r0.valor_extraido + r1.valor_extraido
    # conversión total = valor total / (10 + 20)
    assert lote.conversion_total == lote.valor_total / Decimal("30")


def test_bono_sin_plan_cuenta_cero_y_no_tumba_el_lote():
    # "Retabet" no participa en ningún partido → sin plan; Luckia sí.
    lote = evaluar_lote([PARTIDO], [_bono("Luckia", 10), _bono("Retabet", 50)])
    r_luckia, r_retabet = lote.resultados
    assert r_retabet.sin_plan is True
    assert r_retabet.valor_extraido is None
    assert lote.valor_total == r_luckia.valor_extraido


def test_colision_detectada_entre_recomendadas():
    # Dos freebets al "1" (Luckia y Sportium) sobre el mismo partido cubren ambas
    # la X y el 2 en Bet365 (mejor cuota entre las otras casas) → colisión.
    lote = evaluar_lote(
        [PARTIDO],
        [_bono("Luckia", 10, resultado="1"), _bono("Sportium", 10, resultado="1")],
    )
    apuestas = {(c.resultado, c.casa) for c in lote.colisiones}
    assert ("X", "Bet365") in apuestas
    assert ("2", "Bet365") in apuestas


def test_sin_colision_cuando_no_comparten_apuesta():
    lote = evaluar_lote([PARTIDO], [_bono("Luckia", 10, resultado="1")])
    assert lote.colisiones == []
