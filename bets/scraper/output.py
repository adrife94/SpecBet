from __future__ import annotations
import unicodedata
import re


def _normalizar(nombre: str) -> str:
    """Minúsculas, sin acentos, sin caracteres raros → clave de agrupación."""
    s = unicodedata.normalize("NFD", nombre.lower())
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    s = re.sub(r"\s+", " ", s).strip()
    return s


def consolidar(resultados: list[tuple[str, list[dict]]]) -> dict:
    """
    Recibe lista de (casa, [partido_dict, ...]) y produce el JSON partidos v1.

    Dos entradas se consideran el mismo partido si su nombre normalizado coincide.
    """
    partidos: dict[str, dict] = {}  # clave normalizada → dict acumulado

    for casa, filas in resultados:
        for fila in filas:
            nombre = fila.get("partido", "").strip()
            if not nombre:
                continue
            clave = _normalizar(nombre)

            if clave not in partidos:
                entrada: dict = {"partido": nombre, "cuotas": []}
                if fila.get("fecha"):
                    entrada["fecha"] = fila["fecha"]
                partidos[clave] = entrada

            cuota: dict = {"casa": casa}
            for k in ("1", "X", "2"):
                if k in fila:
                    cuota[k] = fila[k]
            if len(cuota) > 1:
                partidos[clave]["cuotas"].append(cuota)

    return {"version": 1, "partidos": list(partidos.values())}
