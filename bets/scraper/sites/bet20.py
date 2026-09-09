from __future__ import annotations
from playwright.async_api import Page
from ..base import ScraperBase


class Bet20Scraper(ScraperBase):
    CASA = "20bet"
    URL_FUTBOL = "https://20betz0ne1.com/es/prematch/sports/soccer"
    USE_PERSISTENT_PROFILE = True  # usa perfil propio para mantener la sesión

    async def extraer(self, page: Page) -> list[dict]:
        import asyncio, sys

        # Esperar a que el SPA renderice (login o partidos)
        await page.wait_for_function(
            "document.body.innerText.includes('INICIAR SESIÓN') || document.body.innerText.includes('Bet builder')",
            timeout=30_000,
        )

        # Si no hay sesión, avisar y esperar login manual
        logged_in = await page.evaluate(
            "!document.body.innerText.includes('INICIAR SESIÓN')"
        )
        if not logged_in:
            print(
                "\n  ⚠ 20bet: no hay sesión. Inicia sesión en el navegador que se ha abierto y pulsa ENTER aquí.",
                file=sys.stderr,
            )
            await asyncio.get_event_loop().run_in_executor(None, input)
            await page.wait_for_timeout(2000)

        # Esperar a que aparezcan los partidos
        await page.wait_for_function(
            "document.body.innerText.includes('Bet builder')",
            timeout=35_000,
        )
        # Scroll del div de partidos (contenedor interno, no window)
        prev_count = 0
        for _ in range(25):
            await page.evaluate(_SCROLL_INNER)
            await page.wait_for_timeout(700)
            count = await page.evaluate(
                "(document.body.innerText.match(/Bet builder/g) || []).length"
            )
            if count == prev_count and count > 0:
                break
            prev_count = count
        return await page.evaluate(_JS_EXTRACT)


_SCROLL_INNER = """
(() => {
  // 20bet: el contenido de partidos está en un div scrollable interno.
  // Preferimos el que contiene "Bet builder"; si no, el de MAYOR scrollHeight
  // (evitando el menú lateral que también es scrollable pero más pequeño).
  const scrollable = [...document.querySelectorAll('div')].filter(el => {
    const oy = getComputedStyle(el).overflowY;
    return (oy === 'scroll' || oy === 'auto') && el.scrollHeight > el.clientHeight + 100;
  });
  const withBB = scrollable.find(el => el.innerText && el.innerText.includes('Bet builder'));
  const target = withBB || scrollable.sort((a, b) => b.scrollHeight - a.scrollHeight)[0];
  if (target) target.scrollBy(0, 600);
  else document.body.scrollBy(0, 600);
})()
"""

_JS_EXTRACT = """
(() => {
  // 20bet: divs que contienen "Bet builder" como separador entre equipos y cuotas
  // Formato: "date|team1|team2|Bet builder|odd1|oddX|odd2|..."
  const allDivs = document.querySelectorAll('div');
  const results = [];
  const seen = new Set();

  for (const div of allDivs) {
    const text = div.innerText?.replace(/\\n/g, '|') || '';
    if (!text.includes('Bet builder')) continue;
    if (div.children.length > 8 || div.children.length < 2) continue;

    const bbIdx = text.indexOf('Bet builder');
    const after = text.substring(bbIdx + 'Bet builder|'.length);
    const odds = after.split('|').map(s => s.trim()).filter(s => /^\\d+\\.?\\d*$/.test(s));
    if (odds.length < 3) continue;

    const before = text.substring(0, bbIdx);
    const parts = before.split('|').map(s => s.trim()).filter(Boolean);
    if (parts.length < 2) continue;

    const team2 = parts[parts.length - 1];
    const team1 = parts[parts.length - 2];
    const key = team1 + '|' + team2;
    if (seen.has(key) || !team1 || !team2) continue;
    seen.add(key);

    results.push({
      partido: team1 + ' vs ' + team2,
      '1': parseFloat(odds[0]),
      'X': parseFloat(odds[1]),
      '2': parseFloat(odds[2]),
    });
  }
  return results;
})()
"""
