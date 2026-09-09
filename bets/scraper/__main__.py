"""
Scraper de cuotas 1X2 para SpecBet.

Modos de uso:
  # Usar las URLs guardadas en urls.json (comportamiento por defecto):
  python -m scraper --output partidos.json

  # Dar URLs directamente:
  python -m scraper --urls \\
    "https://www.sportium.es/apuestas/sports/soccer/competitions/45225" \\
    "https://canarias.retabet.es/deportes/futbol/europa/champions-league/10" \\
    --output partidos.json

  # Usar las URLs predefinidas por casa:
  python -m scraper --casas winamax sportium --output partidos.json

  # Sin ventana (puede fallar en sites con bot-detection):
  python -m scraper --headless --output partidos.json
"""

from __future__ import annotations
import argparse
import asyncio
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

from playwright.async_api import async_playwright, Page
from playwright_stealth import Stealth

from .output import consolidar
from .sites.winamax import WinamaxScraper
from .sites.codere import CodereSccraper
from .sites.sportium import SportiumScraper
from .sites.retabet import RetabetScraper
from .sites.kirolbet import KirolbetScraper
from .sites.speedybet import SpeedybetScraper
from .sites.bet20 import Bet20Scraper
from .sites.bet365 import Bet365Scraper

_stealth = Stealth()

_PROFILES_DIR = Path(__file__).parent / "profiles"

# Casas disponibles por nombre (para --casas)
SCRAPERS: dict[str, type] = {
    "winamax":   WinamaxScraper,
    "codere":    CodereSccraper,
    "sportium":  SportiumScraper,
    "retabet":   RetabetScraper,
    "kirolbet":  KirolbetScraper,
    "speedybet": SpeedybetScraper,
    "20bet":     Bet20Scraper,
    "bet365":    Bet365Scraper,
}

# Detección automática por dominio (para --urls)
_DOMAIN_MAP: dict[str, type] = {
    "winamax.es":           WinamaxScraper,
    "sportium.es":          SportiumScraper,
    "codere.es":            CodereSccraper,
    "apuestas.codere.es":   CodereSccraper,
    "m.apuestas.codere.es": CodereSccraper,
    "bet365.es":            Bet365Scraper,
    "speedybet.es":         SpeedybetScraper,
    "retabet.es":           RetabetScraper,
    "canarias.retabet.es":  RetabetScraper,
    "kirolbet.es":          KirolbetScraper,
    "canarias.kirolbet.es": KirolbetScraper,
    "20betz0ne1.com":       Bet20Scraper,
    "20bet.es":             Bet20Scraper,
}


def _scraper_para_url(url: str) -> type | None:
    host = urlparse(url).netloc.lower()
    if host in _DOMAIN_MAP:
        return _DOMAIN_MAP[host]
    for domain, cls in _DOMAIN_MAP.items():
        if host.endswith("." + domain) or host == domain:
            return cls
    return None


_SCROLL_JS = """
async () => {
  await new Promise(resolve => {
    let last = -1;
    const timer = setInterval(() => {
      window.scrollBy(0, 400);
      if (document.body.scrollHeight === last) {
        clearInterval(timer);
        resolve();
      }
      last = document.body.scrollHeight;
    }, 200);
    setTimeout(() => { clearInterval(timer); resolve(); }, 10_000);
  });
}
"""


async def _auto_scroll(page: Page) -> None:
    await page.evaluate(_SCROLL_JS)
    await page.wait_for_timeout(500)


async def _scrapear_con_perfil(pw, url: str, scraper_cls: type) -> tuple[str, list[dict]]:
    """Lanza Chromium con perfil propio persistente (guarda la sesión entre ejecuciones)."""
    scraper = scraper_cls()
    nombre = scraper.CASA.lower().replace(" ", "_").replace(".", "")
    profile_dir = _PROFILES_DIR / nombre
    profile_dir.mkdir(parents=True, exist_ok=True)
    context = None
    try:
        context = await pw.chromium.launch_persistent_context(
            str(profile_dir),
            headless=False,
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()
        await _stealth.apply_stealth_async(page)
        await page.goto(url, timeout=45_000, wait_until="domcontentloaded")
        await _auto_scroll(page)
        filas = await scraper.extraer(page)
        print(f"  ✓ {scraper.CASA} ({url.split('//')[1][:40]}): {len(filas)} partido(s)", file=sys.stderr)
        return scraper.CASA, filas
    except Exception as exc:
        print(f"  ✗ {scraper.CASA}: {exc}", file=sys.stderr)
        return scraper.CASA, []
    finally:
        if context:
            try:
                await context.close()
            except Exception:
                pass


async def _scrapear_url(browser, url: str, scraper_cls: type) -> tuple[str, list[dict]]:
    scraper = scraper_cls()
    context = await browser.new_context(
        user_agent=(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/125.0.0.0 Safari/537.36"
        )
    )
    page = await context.new_page()
    await _stealth.apply_stealth_async(page)
    try:
        await page.goto(url, timeout=45_000, wait_until="domcontentloaded")
        await _auto_scroll(page)
        filas = await scraper.extraer(page)
        print(f"  ✓ {scraper.CASA} ({url.split('//')[1][:40]}): {len(filas)} partido(s)", file=sys.stderr)
        return scraper.CASA, filas
    except Exception as exc:
        print(f"  ✗ {scraper.CASA}: {exc}", file=sys.stderr)
        return scraper.CASA, []
    finally:
        await context.close()


async def main(urls_y_clases: list[tuple[str, type]], output: str | None, headless: bool) -> None:
    print(f"Scrapeando {len(urls_y_clases)} página(s)…", file=sys.stderr)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=headless)
        tareas = []
        for url, cls in urls_y_clases:
            if getattr(cls, "USE_PERSISTENT_PROFILE", False):
                tareas.append(_scrapear_con_perfil(pw, url, cls))
            else:
                tareas.append(_scrapear_url(browser, url, cls))
        resultados = await asyncio.gather(*tareas)
        await browser.close()

    datos = consolidar(list(resultados))
    texto = json.dumps(datos, ensure_ascii=False, indent=2)

    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(texto)
        print(f"JSON escrito en {output}", file=sys.stderr)
    else:
        print(texto)


_URLS_CONFIG = Path(__file__).parent.parent / "urls.json"


def _cargar_urls_config() -> list[str]:
    if not _URLS_CONFIG.exists():
        return []
    with open(_URLS_CONFIG, encoding="utf-8") as f:
        data = json.load(f)
    return data.get("urls", [])


def _parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Scraper de cuotas 1X2 para SpecBet",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    group = p.add_mutually_exclusive_group()
    group.add_argument(
        "--urls", "-u",
        nargs="+",
        metavar="URL",
        help="URLs directas a scrapear (detecta la casa por dominio automáticamente)",
    )
    group.add_argument(
        "--casas",
        nargs="+",
        metavar="CASA",
        help=f"Casas a scrapear con URL predefinida. Opciones: {', '.join(SCRAPERS)}",
    )
    p.add_argument("--output", "-o", metavar="FICHERO", help="Escribe JSON aquí en vez de stdout")
    p.add_argument("--headless", action="store_true", help="Modo sin ventana (puede fallar en sites con bot-detection)")
    return p.parse_args()


def _resolver_urls_y_clases(args: argparse.Namespace) -> list[tuple[str, type]]:
    if args.urls:
        urls = args.urls
    elif not args.casas:
        urls = _cargar_urls_config()
        if urls:
            print(f"Usando {len(urls)} URL(s) de {_URLS_CONFIG.name}", file=sys.stderr)
        else:
            urls = None
    else:
        urls = None

    if urls is not None:
        resultado = []
        for url in urls:
            cls = _scraper_para_url(url)
            if cls is None:
                print(f"  ⚠ No se reconoce el dominio de: {url}", file=sys.stderr)
                continue
            resultado.append((url, cls))
        return resultado

    casas = args.casas or list(SCRAPERS.keys())
    desconocidas = [c for c in casas if c not in SCRAPERS]
    if desconocidas:
        print(f"Casas no reconocidas: {desconocidas}", file=sys.stderr)
    return [(SCRAPERS[c]().URL_FUTBOL, SCRAPERS[c]) for c in casas if c in SCRAPERS]


if __name__ == "__main__":
    args = _parse_args()
    pares = _resolver_urls_y_clases(args)
    if not pares:
        print("Nada que scrapear.", file=sys.stderr)
        sys.exit(1)
    asyncio.run(main(pares, args.output, args.headless))
