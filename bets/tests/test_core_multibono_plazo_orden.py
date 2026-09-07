"""T4: plazo por apalancamiento y orden por pérdida
(RF-22, RF-23, RF-24, RF-25, RF-26, RF-27, RF-28, RF-33, RF-34)."""

from decimal import Decimal

from betting.core import construir_config_multi, evaluar_multibono


def _casa(nombre, uno=None, equis=None, dos=None):
    entrada = {"casa": nombre}
    if uno is not None:
        entrada["1"] = Decimal(uno)
    if equis is not None:
        entrada["X"] = Decimal(equis)
    if dos is not None:
        entrada["2"] = Decimal(dos)
    return entrada


def _partido(nombre, *casas, fecha=None):
    partido = {"partido": nombre, "cuotas": list(casas)}
    if fecha is not None:
        partido["fecha"] = fecha
    return partido


def _bono(casa, importe="100", cuota_minima="1.01"):
    return {"casa": casa, "importe": importe, "cuota_minima": cuota_minima}


def _bonos_estandar():
    return [_bono("Luckia"), _bono("Bet365"), _bono("Winamax")]


def _parejo(nombre, cuota="2.6", fecha=None):
    # 3 casas de bono con cuotas iguales: sin relleno, opción siempre válida.
    return _partido(
        nombre,
        _casa("Luckia", uno=cuota, equis=cuota, dos=cuota),
        _casa("Bet365", uno=cuota, equis=cuota, dos=cuota),
        _casa("Winamax", uno=cuota, equis=cuota, dos=cuota),
        fecha=fecha,
    )


def test_fuera_de_plazo_en_esa_fecha_o_despues_se_descarta():
    partidos = [
        _parejo("Antes", fecha="2026-09-10"),
        _parejo("MismoDia", fecha="2026-09-20"),
        _parejo("Despues", fecha="2026-09-21"),
    ]
    config = construir_config_multi(_bonos_estandar(), fecha_apalancamiento="2026-09-20")
    res = evaluar_multibono(partidos, config)

    nombres_ok = {o.partido for o in res.opciones}
    assert nombres_ok == {"Antes"}
    descartados = {d.partido: d.motivo for d in res.descartes}
    assert set(descartados) == {"MismoDia", "Despues"}
    assert all("plazo" in m for m in descartados.values())


def test_partido_sin_fecha_con_apalancamiento_se_evalua_con_aviso():
    partidos = [_parejo("SinFecha")]  # sin fecha
    config = construir_config_multi(_bonos_estandar(), fecha_apalancamiento="2026-09-20")
    res = evaluar_multibono(partidos, config)

    assert {o.partido for o in res.opciones} == {"SinFecha"}  # se evalúa igual
    assert res.avisos_sin_fecha == ["SinFecha"]  # pero avisa


def test_sin_apalancamiento_se_ignoran_las_fechas():
    partidos = [_parejo("Cualquiera", fecha="2020-01-01")]  # fecha pasada
    config = construir_config_multi(_bonos_estandar())  # sin apalancamiento
    res = evaluar_multibono(partidos, config)

    assert {o.partido for o in res.opciones} == {"Cualquiera"}
    assert res.descartes == []
    assert res.avisos_sin_fecha == []


def test_orden_por_perdida_ascendente_con_negativo():
    # Parejo mal pagado (2.6/2.6/2.6 → 40 €) por encima del desequilibrado más caro
    # (1.5/4/6 → 50 €); y un arbitraje (2.7/3.6/3.2 → pérdida negativa) el primero.
    desequilibrado = _partido(
        "Desequilibrado",
        _casa("Luckia", uno="1.5", equis="4", dos="6"),
        _casa("Bet365", uno="1.5", equis="4", dos="6"),
        _casa("Winamax", uno="1.5", equis="4", dos="6"),
        _casa("Codere", uno="1.5", equis="4", dos="6"),
    )
    arbitraje = _partido(
        "Arbitraje",
        _casa("Luckia", uno="2.7", equis="3.6", dos="3.2"),
        _casa("Bet365", uno="2.7", equis="3.6", dos="3.2"),
        _casa("Winamax", uno="2.7", equis="3.6", dos="3.2"),
        _casa("Codere", uno="2.7", equis="3.6", dos="3.2"),
    )
    partidos = [desequilibrado, _parejo("Parejo", cuota="2.6"), arbitraje]
    config = construir_config_multi(_bonos_estandar())
    res = evaluar_multibono(partidos, config)

    assert [o.partido for o in res.opciones] == ["Arbitraje", "Parejo", "Desequilibrado"]
    assert res.opciones[0].perdida < 0
    assert res.opciones[1].perdida == Decimal("40")
    assert res.opciones[2].perdida == Decimal("50")


def test_sin_partidos_devuelve_listas_vacias():
    config = construir_config_multi(_bonos_estandar())
    res = evaluar_multibono([], config)

    assert res.opciones == []
    assert res.descartes == []
    assert res.avisos_sin_fecha == []


def test_ninguna_opcion_valida_devuelve_solo_descartes():
    # Falta una casa de bono en cada partido → todos descartados, sin opciones.
    partidos = [
        _partido(
            "A vs B",
            _casa("Luckia", uno="2", equis="3", dos="4"),
            _casa("Bet365", uno="2", equis="3", dos="4"),
        )
    ]
    config = construir_config_multi(_bonos_estandar())
    res = evaluar_multibono(partidos, config)

    assert res.opciones == []
    assert len(res.descartes) == 1
    assert "Winamax" in res.descartes[0].motivo
