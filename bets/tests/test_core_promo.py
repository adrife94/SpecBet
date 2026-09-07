"""T1: núcleo del filtro de promo "ventaja de 2 goles"
(RF-1, RF-3, RF-5, RF-6, RF-7, RF-8, RF-9, RF-10, RF-11, RF-12, RF-13, RF-14, RF-15, RF-17)."""

from decimal import Decimal

import pytest

from betting.core import (
    construir_filtro_promo,
    opciones_promo,
    posicion_promo,
    coste_promo,
    windfall_promo,
)
from betting.storage import ErrorDatos


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


# --- filtro (RF-1, RF-3, RF-5) ---

def test_construir_filtro_normaliza_y_valida():
    filtro = construir_filtro_promo(["Bet365", " 20BET "])
    assert filtro.casas == frozenset({"bet365", "20bet"})


def test_lista_vacia_es_error():
    with pytest.raises(ErrorDatos):
        construir_filtro_promo([])


def test_lista_solo_espacios_es_error():
    with pytest.raises(ErrorDatos):
        construir_filtro_promo(["  ", ""])


# --- posición, coste y windfall (RF-6, RF-8, RF-11, RF-12, RF-13, RF-14) ---

def test_posicion_coste_y_windfall_verificados_a_mano():
    partido = _partido(
        "A vs B",
        _casa("Bet365", uno="2.00", equis="3.40", dos="3.50"),
        _casa("Winamax", uno="2.10", equis="3.30", dos="3.60"),
    )
    filtro = construir_filtro_promo(["Bet365"])
    pata = posicion_promo(partido, "1", filtro)

    assert pata.casa == "Bet365"
    assert pata.cuota == Decimal("2.00")
    assert pata.casa_referencia == "Winamax"  # mejor cuota sin restricción
    assert pata.cuota_referencia == Decimal("2.10")
    assert coste_promo(pata, Decimal("50")) == Decimal("5.00")  # 50·(2.10−2.00)
    assert windfall_promo(pata, Decimal("50")) == Decimal("100.00")  # 50·2.00


def test_coste_cero_cuando_la_mejor_cuota_ya_es_de_la_promo():
    partido = _partido(
        "A vs B",
        _casa("Bet365", uno="2.15", equis="3.40", dos="3.50"),
        _casa("Winamax", uno="2.10", equis="3.30", dos="3.60"),
    )
    filtro = construir_filtro_promo(["Bet365"])
    pata = posicion_promo(partido, "1", filtro)

    assert pata.casa == "Bet365"
    assert pata.cuota_referencia == Decimal("2.15")  # la referencia es la propia Bet365
    assert coste_promo(pata, Decimal("50")) == Decimal("0.00")  # seguro gratis
    assert windfall_promo(pata, Decimal("50")) == Decimal("107.50")  # 50·2.15


def test_pata_no_asegurable_devuelve_none():
    # La casa de promo no cotiza el "1".
    partido = _partido(
        "A vs B",
        _casa("Bet365", equis="3.40", dos="3.50"),  # sin "1"
        _casa("Winamax", uno="2.10", equis="3.30", dos="3.60"),
    )
    filtro = construir_filtro_promo(["Bet365"])
    assert posicion_promo(partido, "1", filtro) is None


# --- tres opciones y avisos (RF-4, RF-7, RF-10, RF-15, RF-17) ---

def test_tres_opciones_juntas_con_aviso_de_acumulacion():
    partido = _partido(
        "A vs B",
        _casa("Bet365", uno="2.00", equis="3.40", dos="3.50"),
        _casa("Winamax", uno="2.10", equis="3.30", dos="3.60"),
    )
    filtro = construir_filtro_promo(["Bet365"])
    promo = opciones_promo(partido, filtro)

    nombres = [o.nombre for o in promo.opciones]
    assert nombres == ["asegurar_1", "asegurar_2", "asegurar_ambos"]
    ambos = next(o for o in promo.opciones if o.nombre == "asegurar_ambos")
    assert len(ambos.patas) == 2
    assert any("acumul" in a for a in promo.avisos)  # RF-15


def test_la_x_nunca_se_restringe():
    partido = _partido(
        "A vs B",
        _casa("Bet365", uno="2.00", equis="3.40", dos="3.50"),
        _casa("Winamax", uno="2.10", equis="3.30", dos="3.60"),
    )
    filtro = construir_filtro_promo(["Bet365"])
    promo = opciones_promo(partido, filtro)

    # Ninguna pata posicionada es la X (solo se aseguran 1 y 2).
    resultados = {p.resultado for o in promo.opciones for p in o.patas}
    assert "X" not in resultados
    assert resultados <= {"1", "2"}


def test_pata_no_asegurable_omite_opcion_y_avisa():
    # Solo hay casa de promo para el "2"; el "1" no se puede asegurar.
    partido = _partido(
        "A vs B",
        _casa("Bet365", equis="3.40", dos="3.50"),  # sin "1"
        _casa("Winamax", uno="2.10", equis="3.30", dos="3.60"),
    )
    filtro = construir_filtro_promo(["Bet365"])
    promo = opciones_promo(partido, filtro)

    nombres = [o.nombre for o in promo.opciones]
    assert nombres == ["asegurar_2"]  # sin asegurar_1 ni asegurar_ambos
    assert any("resultado 1" in a for a in promo.avisos)  # RF-10
