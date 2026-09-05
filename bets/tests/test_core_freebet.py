"""T2: conversión de una colocación de freebet (RF-2, RF-3, RF-4, RF-11)."""

from decimal import Decimal

from betting.core import calcular_jugada

DOS = Decimal("0.01")


def test_conversion_verificada_neto_igual_en_los_tres():
    # Freebet de 10 al "1" a 3.60; cobertura X=3.40, 2=2.10.
    # R = 10·2.60 = 26.00; s_X = 26/3.40 = 7.6470…; s_2 = 26/2.10 = 12.3809…
    # V = 26 − 20.0280… = 5.9719… → conversión 59.72 %.
    jugada = calcular_jugada(
        "A vs B",
        Decimal("10"),
        "1",
        Decimal("3.60"),
        "Luckia",
        {"X": (Decimal("3.40"), "Bet365"), "2": (Decimal("2.10"), "Winamax")},
    )

    assert jugada.valor_extraido.quantize(DOS) == Decimal("5.97")
    assert (jugada.conversion * 100).quantize(DOS) == Decimal("59.72")

    patas = {p.resultado: p for p in jugada.patas}
    assert patas["1"].tipo == "gratis"
    assert patas["1"].importe == Decimal("10")
    assert patas["1"].casa == "Luckia"

    # el retorno de cada cobertura iguala R = 26.00
    for r in ("X", "2"):
        assert (patas[r].importe * patas[r].cuota).quantize(DOS) == Decimal("26.00")

    # beneficio neto idéntico gane quien gane
    invertido = patas["X"].importe + patas["2"].importe
    retorno = Decimal("10") * (Decimal("3.60") - 1)
    neto_gana_gratis = retorno - invertido
    neto_gana_X = patas["X"].importe * patas["X"].cuota - invertido
    neto_gana_2 = patas["2"].importe * patas["2"].cuota - invertido
    assert neto_gana_gratis.quantize(DOS) == Decimal("5.97")
    assert neto_gana_X.quantize(DOS) == Decimal("5.97")
    assert neto_gana_2.quantize(DOS) == Decimal("5.97")


def test_patas_una_gratis_y_dos_cobertura_en_orden():
    jugada = calcular_jugada(
        "A vs B",
        Decimal("10"),
        "X",
        Decimal("3.30"),
        "Luckia",
        {"1": (Decimal("2.10"), "Bet365"), "2": (Decimal("4.00"), "Winamax")},
    )
    tipos = [(p.tipo, p.resultado) for p in jugada.patas]
    assert tipos == [("gratis", "X"), ("cobertura", "1"), ("cobertura", "2")]
