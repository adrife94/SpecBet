"""T2: coste de una opción del bono (RF-3, RF-4, RF-5, RF-7)."""

from decimal import Decimal

from betting.core import calcular_opcion

DOS = Decimal("0.01")


def test_coste_verificado_mismo_retorno_en_los_tres():
    # Anclar 100 € al "2" a 2.10; cubrir 1 @3.80 y X @3.40.
    # R = 210; s_1 = 55.26…, s_X = 61.76… → coste = (100+117.02…) − 210 = 7.03.
    opcion = calcular_opcion(
        "A vs B",
        "2",
        Decimal("100"),
        Decimal("2.10"),
        "Luckia",
        {"1": (Decimal("3.80"), "Bet365"), "X": (Decimal("3.40"), "Winamax")},
    )
    assert opcion.coste.quantize(DOS) == Decimal("7.03")

    # el retorno es el mismo gane quien gane: 210 en las tres patas
    assert (opcion.importe * opcion.cuota).quantize(DOS) == Decimal("210.00")
    for cob in opcion.coberturas:
        assert (cob.importe * cob.cuota).quantize(DOS) == Decimal("210.00")

    # dos coberturas, en el orden 1, X (el resultado anclado "2" se excluye)
    assert [c.resultado for c in opcion.coberturas] == ["1", "X"]


def test_coste_negativo_cuando_hay_arbitraje():
    # Cuotas de cobertura altas → el conjunto es arbitraje, coste negativo.
    opcion = calcular_opcion(
        "A vs B",
        "2",
        Decimal("100"),
        Decimal("2.10"),
        "Luckia",
        {"1": (Decimal("4.20"), "Bet365"), "X": (Decimal("3.60"), "Winamax")},
    )
    assert opcion.coste.quantize(DOS) == Decimal("-1.67")
