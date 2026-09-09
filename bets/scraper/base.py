from __future__ import annotations
from abc import ABC, abstractmethod
from playwright.async_api import Page


class ScraperBase(ABC):
    CASA: str = ""
    URL_FUTBOL: str = ""

    @abstractmethod
    async def extraer(self, page: Page) -> list[dict]:
        """
        Navega a URL_FUTBOL y extrae las cuotas del día.

        Retorna lista de dicts con claves:
          partido  str   "Equipo A vs Equipo B"
          fecha    str   ISO-8601 opcional ("2026-09-10" o "2026-09-10T21:00")
          1        float cuota local  (omitir si no disponible)
          X        float cuota empate (omitir si no disponible)
          2        float cuota visitante (omitir si no disponible)
        """
