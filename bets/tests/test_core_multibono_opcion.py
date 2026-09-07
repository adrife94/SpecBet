"""T2: cálculo de una opción del multibono dada una asignación
(RF-12, RF-13, RF-14, RF-15, RF-18, RF-19, RF-20, RF-21)."""

from decimal import Decimal

from betting.core import ConfigBonus, calcular_opcion_multi


def _bono(casa, importe):
    return ConfigBonus(casa=casa, importe=Decimal(importe), cuota_minima=Decimal("1.01"))


def _patas_por_clave(opcion):
    return {(p.tipo, p.resultado): p for p in opcion.patas}


def test_tres_bonos_caso_verificado_a_mano():
    # 3 bonos de 100; cuotas de bono 1=1.5, X=4, 2=6; relleno de 1 y X en casa
    # distinta a 1.5 y 4. Caso del plan: R=600, real=350, pérdida=50 (16.67%).
    asignacion = {
        "1": (_bono("Luckia", "100"), Decimal("1.5")),
        "X": (_bono("Bet365", "100"), Decimal("4")),
        "2": (_bono("Winamax", "100"), Decimal("6")),
    }
    rellenos = {
        "1": (Decimal("1.5"), "Codere"),
        "X": (Decimal("4"), "Pokerstars"),
        "2": (Decimal("6"), "Marca"),  # no se usa (la pata @6 marca el techo)
    }
    op = calcular_opcion_multi("A vs B", asignacion, rellenos)

    assert op.retorno == Decimal("600")
    assert op.dinero_real == Decimal("350")
    assert op.perdida == Decimal("50")
    assert op.perdida_pct == Decimal("50") / Decimal("300") * Decimal("100")
    assert op.neto == Decimal("250")

    patas = _patas_por_clave(op)
    # Relleno que iguala el retorno en los tres resultados: 150+450, 400+200, 600.
    assert patas[("bono", "1")].importe == Decimal("100")
    assert patas[("relleno", "1")].importe == Decimal("300")
    assert patas[("relleno", "1")].casa == "Codere"
    assert patas[("relleno", "X")].importe == Decimal("50")
    # La pata @6 es el techo: solo bono, sin relleno.
    assert ("bono", "2") in patas
    assert ("relleno", "2") not in patas

    # Cada resultado devuelve exactamente R (relleno que iguala, RF-13/RF-14).
    for r in ("1", "X", "2"):
        retorno_r = sum(
            (p.importe * p.cuota for p in op.patas if p.resultado == r), Decimal(0)
        )
        assert retorno_r == op.retorno


def test_dos_bonos_tercer_resultado_solo_con_dinero_real():
    # Bonos en 1 (cuota 2) y X (cuota 4); el 2 se cubre entero con dinero real.
    asignacion = {
        "1": (_bono("Luckia", "100"), Decimal("2")),
        "X": (_bono("Bet365", "100"), Decimal("4")),
        "2": None,
    }
    rellenos = {
        "1": (Decimal("2"), "Codere"),
        "X": (Decimal("4"), "Pokerstars"),
        "2": (Decimal("4"), "Marca"),
    }
    op = calcular_opcion_multi("A vs B", asignacion, rellenos)

    assert op.retorno == Decimal("400")  # techo = 100·4
    patas = _patas_por_clave(op)
    assert ("bono", "2") not in patas  # el 2 no lleva bono
    assert patas[("relleno", "2")].importe == Decimal("100")  # 400/4, cobertura entera
    assert patas[("relleno", "1")].importe == Decimal("100")  # (400-200)/2
    assert op.dinero_real == Decimal("200")
    assert op.perdida == Decimal("0")  # (200 bono + 200 real) - 400
    assert op.perdida_pct == Decimal("0")
    assert op.neto == Decimal("200")


def test_perdida_negativa_es_arbitraje():
    # Cuotas de surebet (payout > 100 %): la pérdida sale negativa (beneficio).
    asignacion = {
        "1": (_bono("Luckia", "100"), Decimal("2.7")),
        "X": (_bono("Bet365", "100"), Decimal("3.6")),
        "2": (_bono("Winamax", "100"), Decimal("3.2")),
    }
    rellenos = {
        "1": (Decimal("2.7"), "Codere"),
        "X": (Decimal("3.6"), "Pokerstars"),
        "2": (Decimal("3.2"), "Marca"),
    }
    op = calcular_opcion_multi("A vs B", asignacion, rellenos)

    assert op.retorno == Decimal("360")  # techo = 100·3.6
    assert op.perdida < 0  # arbitraje
    assert op.perdida_pct < 0
    assert op.neto == op.retorno - op.dinero_real  # coherencia neto = R - real
