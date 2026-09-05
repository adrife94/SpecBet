"""T2/T3/T4: reparto de stake, señal y orden (RF-1..RF-3, RF-5..RF-10)."""

from decimal import Decimal

from betting.core import repartir, repartir_partido

DOS = Decimal("0.01")


def _mejor(cuota, *casas):
    return {"cuota": Decimal(cuota) if cuota is not None else None, "casas": list(casas)}


def _partido(nombre, uno, equis, dos, *, incompleto=False, payout=None):
    return {
        "partido": nombre,
        "payout": Decimal(payout) if payout is not None else None,
        "incompleto": incompleto,
        "mejores": {"1": uno, "X": equis, "2": dos},
    }


# --- T2: reparto numérico verificado a mano (RF-1, RF-2, RF-3, RF-5) ---


def test_reparto_verificado_suma_inversion_y_retorno_igual():
    # 2.10 / 3.60 / 4.20 → Σ(1/cuota) = 125/126, retorno = 100·126/125 = 100.80.
    # Importes exactos: 48 / 28 / 24 (suman 100); cada importe·cuota = 100.80.
    partido = _partido(
        "A vs B", _mejor("2.10", "Bet365"), _mejor("3.60", "Codere"), _mejor("4.20", "Winamax")
    )
    r = repartir_partido(partido, Decimal("100"))

    assert not r.no_calculable
    assert r.patas["1"].importe.quantize(DOS) == Decimal("48.00")
    assert r.patas["X"].importe.quantize(DOS) == Decimal("28.00")
    assert r.patas["2"].importe.quantize(DOS) == Decimal("24.00")

    suma = sum(r.patas[k].importe for k in ("1", "X", "2"))
    assert suma.quantize(DOS) == Decimal("100.00")

    for k in ("1", "X", "2"):
        retorno_pata = r.patas[k].importe * r.patas[k].cuota
        assert retorno_pata.quantize(DOS) == Decimal("100.80")
    assert r.retorno.quantize(DOS) == Decimal("100.80")


# --- T3: señalización surebet / pérdida / no calculable (RF-6, RF-7, RF-9) ---


def test_surebet_beneficio_positivo():
    partido = _partido(
        "A vs B", _mejor("2.10", "X"), _mejor("3.60", "Y"), _mejor("4.20", "Z"), payout="100.80"
    )
    r = repartir_partido(partido, Decimal("100"))
    assert r.surebet is True
    assert r.beneficio.quantize(DOS) == Decimal("0.80")


def test_perdida_beneficio_negativo():
    partido = _partido(
        "A vs B", _mejor("2.00", "X"), _mejor("3.00", "Y"), _mejor("3.00", "Z"), payout="85.71"
    )
    r = repartir_partido(partido, Decimal("100"))
    assert r.surebet is False
    assert r.beneficio < 0


def test_payout_exacto_100_beneficio_cero_no_es_surebet():
    partido = _partido(
        "A vs B", _mejor("3.00", "X"), _mejor("3.00", "Y"), _mejor("3.00", "Z"), payout="100.00"
    )
    r = repartir_partido(partido, Decimal("100"))
    assert r.surebet is False
    assert r.beneficio.quantize(DOS) == Decimal("0.00")


def test_incompleto_no_es_calculable():
    partido = _partido(
        "A vs B", _mejor("1.90", "X"), _mejor(None), _mejor(None), incompleto=True
    )
    r = repartir_partido(partido, Decimal("100"))
    assert r.no_calculable is True
    assert r.patas is None
    assert r.retorno is None
    assert r.beneficio is None
    assert r.surebet is False


# --- T4: empate de casas y orden (RF-8, RF-10) ---


def test_empate_de_casas_conserva_la_lista_sin_dividir_importe():
    partido = _partido(
        "A vs B",
        _mejor("2.10", "Bet365", "Codere"),
        _mejor("3.60", "Winamax"),
        _mejor("4.20", "Bet365"),
    )
    r = repartir_partido(partido, Decimal("100"))
    assert r.patas["1"].casas == ("Bet365", "Codere")
    # el importe de la pata es el total, no se reparte entre las dos casas
    assert r.patas["1"].importe.quantize(DOS) == Decimal("48.00")


def test_orden_calculables_por_beneficio_desc_y_no_calculables_al_final():
    surebet = _partido(
        "Surebet", _mejor("2.10", "X"), _mejor("3.60", "Y"), _mejor("4.20", "Z"), payout="100.80"
    )
    perdida = _partido(
        "Perdida", _mejor("2.00", "X"), _mejor("3.00", "Y"), _mejor("3.00", "Z"), payout="85.71"
    )
    incompleto = _partido(
        "Incompleto", _mejor("1.90", "X"), _mejor(None), _mejor(None), incompleto=True
    )
    orden = repartir([perdida, incompleto, surebet], Decimal("100"))
    assert [r.nombre for r in orden] == ["Surebet", "Perdida", "Incompleto"]
