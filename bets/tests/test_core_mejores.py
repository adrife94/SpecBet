"""T4: mejor cuota por resultado (RF-2, RF-4, RF-5, RF-7, RF-8)."""

from decimal import Decimal

from betting.core import Descartada, mejores_de_partido


def _partido(nombre: str, cuotas: list[dict]) -> dict:
    return {"partido": nombre, "cuotas": cuotas}


def test_mejor_cuota_es_la_mas_alta():
    partido = _partido(
        "A vs B",
        [
            {"casa": "Bet365", "1": Decimal("2.10"), "X": Decimal("3.30"), "2": Decimal("3.50")},
            {"casa": "Codere", "1": Decimal("2.05"), "X": Decimal("3.40"), "2": Decimal("3.60")},
        ],
    )
    mejores, descartes = mejores_de_partido(partido)
    assert mejores["1"].cuota == Decimal("2.10")
    assert mejores["1"].casas == ("Bet365",)
    assert mejores["X"].cuota == Decimal("3.40")
    assert mejores["X"].casas == ("Codere",)
    assert descartes == []


def test_empate_lista_todas_las_casas_en_orden():
    partido = _partido(
        "A vs B",
        [
            {"casa": "Bet365", "1": Decimal("2.10")},
            {"casa": "Codere", "1": Decimal("2.10")},
            {"casa": "Winamax", "1": Decimal("2.05")},
        ],
    )
    mejores, _ = mejores_de_partido(partido)
    assert mejores["1"].cuota == Decimal("2.10")
    assert mejores["1"].casas == ("Bet365", "Codere")


def test_hueco_por_casa_se_ignora():
    partido = _partido(
        "A vs B",
        [
            {"casa": "Bet365", "1": Decimal("2.10"), "2": Decimal("3.50")},  # sin X
            {"casa": "Codere", "X": Decimal("3.40")},
        ],
    )
    mejores, descartes = mejores_de_partido(partido)
    assert mejores["1"].casas == ("Bet365",)
    assert mejores["X"].casas == ("Codere",)
    assert descartes == []  # un hueco no genera aviso


def test_clave_nula_es_hueco_sin_aviso():
    partido = _partido("A vs B", [{"casa": "Bet365", "1": Decimal("2.10"), "X": None}])
    mejores, descartes = mejores_de_partido(partido)
    assert mejores["X"] is None
    assert descartes == []


def test_cuota_invalida_se_descarta_con_aviso():
    partido = _partido(
        "A vs B",
        [
            {"casa": "Bet365", "1": "N/A", "X": Decimal("1.00"), "2": Decimal("-2")},
            {"casa": "Codere", "1": Decimal("2.05"), "X": Decimal("3.40"), "2": Decimal("3.60")},
        ],
    )
    mejores, descartes = mejores_de_partido(partido)
    # solo cuentan las cuotas válidas de Codere
    assert mejores["1"].casas == ("Codere",)
    assert mejores["X"].casas == ("Codere",)
    assert mejores["2"].casas == ("Codere",)
    # las tres inválidas de Bet365 quedan registradas para avisar
    assert len(descartes) == 3
    assert all(isinstance(d, Descartada) and d.casa == "Bet365" for d in descartes)


def test_resultado_sin_ninguna_cuota_valida_es_none():
    partido = _partido("A vs B", [{"casa": "Bet365", "1": Decimal("2.10")}])
    mejores, _ = mejores_de_partido(partido)
    assert mejores["X"] is None
    assert mejores["2"] is None
