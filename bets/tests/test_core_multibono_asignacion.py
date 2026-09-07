"""T3: elección de asignación de menor pérdida y relleno excluyendo casas de bono
(RF-6, RF-7, RF-8, RF-9, RF-10, RF-11, RF-16, RF-17)."""

from decimal import Decimal

from betting.core import (
    construir_config_multi,
    _mejor_cuota_excluyendo,
    _opcion_de_partido_multi,
)


def _casa(nombre, uno=None, equis=None, dos=None):
    entrada = {"casa": nombre}
    if uno is not None:
        entrada["1"] = Decimal(uno)
    if equis is not None:
        entrada["X"] = Decimal(equis)
    if dos is not None:
        entrada["2"] = Decimal(dos)
    return entrada


def _partido(nombre, *casas):
    return {"partido": nombre, "cuotas": list(casas)}


def _bono(casa, importe="100", cuota_minima="1.01"):
    return {"casa": casa, "importe": importe, "cuota_minima": cuota_minima}


def _patas_por_clave(opcion):
    return {(p.tipo, p.resultado): p for p in opcion.patas}


# --- _mejor_cuota_excluyendo (RF-15, RF-16) ---

def test_mejor_cuota_excluyendo_ignora_casas_de_bono():
    partido = _partido(
        "A vs B",
        _casa("Luckia", uno="1.60"),
        _casa("Bet365", uno="1.55"),
        _casa("Codere", uno="1.50"),
        _casa("Marca", uno="1.50"),
    )
    # Excluidas las dos de bono, gana la mejor de las demás; empate → primera.
    assert _mejor_cuota_excluyendo(partido, "1", {"luckia", "bet365"}) == (Decimal("1.50"), "Codere")


def test_mejor_cuota_excluyendo_sin_casa_valida_es_none():
    partido = _partido("A vs B", _casa("Luckia", uno="1.60"), _casa("Bet365", uno="1.55"))
    assert _mejor_cuota_excluyendo(partido, "1", {"luckia", "bet365"}) is None


# --- asignación (RF-7, RF-8, RF-9, RF-10, RF-16, RF-17) ---

def test_elige_la_asignacion_de_menor_perdida_con_importes_distintos():
    # Cuotas 1=2, X=3, 2=4 en todas; el bono pequeño (50) en la cuota más alta
    # minimiza la pérdida (25 frente a 33.33 de las otras asignaciones).
    partido = _partido(
        "A vs B",
        _casa("Luckia", uno="2", equis="3", dos="4"),
        _casa("Bet365", uno="2", equis="3", dos="4"),
        _casa("Winamax", uno="2", equis="3", dos="4"),
        _casa("Codere", uno="2", equis="3", dos="4"),
    )
    config = construir_config_multi([_bono("Luckia"), _bono("Bet365"), _bono("Winamax", importe="50")])
    op, descarte = _opcion_de_partido_multi(partido, config)

    assert descarte is None
    assert op.perdida == Decimal("25")
    # El bono de importe 50 (Winamax) queda anclado en el resultado "2".
    bono_50 = next(p for p in op.patas if p.tipo == "bono" and p.importe == Decimal("50"))
    assert bono_50.resultado == "2"
    assert bono_50.casa == "Winamax"


def test_empate_de_perdida_es_determinista_por_orden_de_permutacion():
    # Cuotas iguales para todos y bonos iguales → todas las permutaciones empatan;
    # se toma la primera: bonos[0]→1, [1]→X, [2]→2.
    partido = _partido(
        "A vs B",
        _casa("Luckia", uno="3", equis="3", dos="3"),
        _casa("Bet365", uno="3", equis="3", dos="3"),
        _casa("Winamax", uno="3", equis="3", dos="3"),
        _casa("Codere", uno="3", equis="3", dos="3"),
    )
    config = construir_config_multi([_bono("Luckia"), _bono("Bet365"), _bono("Winamax")])
    op, descarte = _opcion_de_partido_multi(partido, config)

    assert descarte is None
    patas = _patas_por_clave(op)
    assert patas[("bono", "1")].casa == "Luckia"
    assert patas[("bono", "X")].casa == "Bet365"
    assert patas[("bono", "2")].casa == "Winamax"


def test_el_relleno_excluye_todas_las_casas_de_bono():
    # Bet365 (de bono) paga mejor el "1" (2.0) que Codere (1.9), pero el relleno
    # debe ir a Codere: las casas de bono están excluidas del relleno.
    partido = _partido(
        "A vs B",
        _casa("Luckia", uno="2.0", equis="3.0", dos="6.0"),
        _casa("Bet365", uno="2.0", equis="3.0", dos="6.0"),
        _casa("Winamax", uno="2.0", equis="3.0", dos="6.0"),
        _casa("Codere", uno="1.9", equis="2.9", dos="5.0"),
    )
    config = construir_config_multi([_bono("Luckia"), _bono("Bet365"), _bono("Winamax")])
    op, descarte = _opcion_de_partido_multi(partido, config)

    assert descarte is None
    casas_bono = {"luckia", "bet365", "winamax"}
    rellenos = [p for p in op.patas if p.tipo == "relleno"]
    assert rellenos  # hay relleno
    assert all(p.casa.strip().casefold() not in casas_bono for p in rellenos)
    # El relleno del "1" usa Codere (1.9), no la cuota mayor de una casa de bono.
    relleno_1 = next(p for p in rellenos if p.resultado == "1")
    assert relleno_1.casa == "Codere"


def test_resultado_no_rellenable_es_descarte():
    # Solo participan las casas de bono: no hay dónde rellenar → descarte.
    partido = _partido(
        "A vs B",
        _casa("Luckia", uno="1.5", equis="4", dos="6"),
        _casa("Bet365", uno="1.5", equis="4", dos="6"),
        _casa("Winamax", uno="1.5", equis="4", dos="6"),
    )
    config = construir_config_multi([_bono("Luckia"), _bono("Bet365"), _bono("Winamax")])
    op, descarte = _opcion_de_partido_multi(partido, config)

    assert op is None
    assert descarte is not None
    assert "rellenar" in descarte.motivo


def test_casa_de_bono_ausente_es_descarte():
    partido = _partido(
        "A vs B",
        _casa("Luckia", uno="2", equis="3", dos="4"),
        _casa("Bet365", uno="2", equis="3", dos="4"),
        _casa("Codere", uno="2", equis="3", dos="4"),
    )
    config = construir_config_multi([_bono("Luckia"), _bono("Bet365"), _bono("Winamax")])
    op, descarte = _opcion_de_partido_multi(partido, config)

    assert op is None
    assert descarte is not None
    assert "Winamax" in descarte.motivo


def test_dos_bonos_dejan_un_resultado_solo_con_dinero_real():
    partido = _partido(
        "A vs B",
        _casa("Luckia", uno="3", equis="3", dos="3"),
        _casa("Bet365", uno="3", equis="3", dos="3"),
        _casa("Codere", uno="3", equis="3", dos="3"),
    )
    config = construir_config_multi([_bono("Luckia"), _bono("Bet365")])
    op, descarte = _opcion_de_partido_multi(partido, config)

    assert descarte is None
    bonos = [p for p in op.patas if p.tipo == "bono"]
    assert len(bonos) == 2  # solo dos patas de bono
    con_bono = {p.resultado for p in bonos}
    sin_bono = set(("1", "X", "2")) - con_bono
    assert len(sin_bono) == 1
    (resultado_real,) = sin_bono
    # El resultado sin bono se cubre solo con dinero real.
    rellenos = {p.resultado for p in op.patas if p.tipo == "relleno"}
    assert resultado_real in rellenos


def test_bono_por_debajo_de_la_minima_en_todo_el_partido_es_descarte():
    partido = _partido(
        "A vs B",
        _casa("Luckia", uno="2", equis="3", dos="4"),
        _casa("Bet365", uno="2", equis="3", dos="4"),
        _casa("Codere", uno="2", equis="3", dos="4"),
    )
    # Bet365 exige cuota mínima 99: no puede anclarse en ningún resultado.
    config = construir_config_multi([_bono("Luckia"), _bono("Bet365", cuota_minima="99")])
    op, descarte = _opcion_de_partido_multi(partido, config)

    assert op is None
    assert descarte is not None
    assert "mínima" in descarte.motivo
