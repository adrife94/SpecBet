"""T3: generación de opciones por partido (RF-2, RF-6, RF-11, RF-12, RF-13)."""

from decimal import Decimal

from betting.core import ConfigBonus, _opciones_de_partido


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


def _config(casa="Luckia", importe="100", cuota_minima="1.5"):
    return ConfigBonus(casa=casa, importe=_c(importe), cuota_minima=_c(cuota_minima))


def test_una_opcion_por_resultado_por_encima_de_la_minima():
    partido = _partido(
        "A vs B",
        _entrada("Luckia", 2.10, 3.30, 2.50),
        _entrada("Bet365", 4.20, 3.60, 3.90),
        _entrada("Winamax", 4.10, 3.55, 3.95),
    )
    opciones, descartes = _opciones_de_partido(partido, _config(cuota_minima="1.5"))
    assert {o.resultado for o in opciones} == {"1", "X", "2"}
    assert descartes == []


def test_resultado_bajo_la_cuota_minima_se_omite():
    # En Luckia: 1=2.10, X=1.30 (bajo mínima 1.5), 2=2.50 → solo 1 y 2.
    partido = _partido(
        "A vs B",
        _entrada("Luckia", 2.10, 1.30, 2.50),
        _entrada("Bet365", 4.20, 3.60, 3.90),
    )
    opciones, _ = _opciones_de_partido(partido, _config(cuota_minima="1.5"))
    assert {o.resultado for o in opciones} == {"1", "2"}


def test_resultado_no_cubrible_genera_descarte():
    # El "2" solo lo ofrece Luckia (la casa del bono) → no cubrible al anclar en 1 o X.
    partido = _partido(
        "A vs B",
        _entrada("Luckia", 2.10, 3.30, 2.50),
        _entrada("Bet365", 4.20, 3.60),
    )
    opciones, descartes = _opciones_de_partido(partido, _config())
    assert {o.resultado for o in opciones} == {"2"}  # anclar en 2 sí cubre 1 y X
    motivos = [(d.resultado, d.motivo) for d in descartes]
    assert any(res in ("1", "X") and "no se puede cubrir" in m for res, m in motivos)


def test_cobertura_excluye_la_casa_del_bono():
    # Luckia tiene la mejor cuota del "1" (5.00) pero cubrir debe ir a otra casa.
    partido = _partido(
        "A vs B",
        _entrada("Luckia", 5.00, 3.30, 2.10),
        _entrada("Bet365", 4.20, 3.60, 2.05),
    )
    opciones, _ = _opciones_de_partido(partido, _config())
    anclada_2 = next(o for o in opciones if o.resultado == "2")
    cobertura_1 = next(c for c in anclada_2.coberturas if c.resultado == "1")
    assert cobertura_1.casa == "Bet365"
    assert cobertura_1.cuota == Decimal("4.20")


def test_casa_del_bono_ausente_descarta_el_partido():
    partido = _partido("A vs B", _entrada("Bet365", 2.10, 3.30, 3.50))
    opciones, descartes = _opciones_de_partido(partido, _config())
    assert opciones == []
    assert len(descartes) == 1
    assert descartes[0].resultado is None
    assert "no participa" in descartes[0].motivo
