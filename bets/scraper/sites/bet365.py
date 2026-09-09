from __future__ import annotations
from playwright.async_api import Page
from ..base import ScraperBase


class Bet365Scraper(ScraperBase):
    CASA = "Bet365"
    URL_FUTBOL = "https://www.bet365.es/#/AS/B1/"

    async def extraer(self, page: Page) -> list[dict]:
        # Bet365 usa hash-routing; esperar a que cargue algún contenido de cuotas
        await page.wait_for_load_state("networkidle", timeout=20_000)
        await page.wait_for_timeout(3000)
        return await page.evaluate(_JS_EXTRACT)


_JS_EXTRACT = """
(() => {
  // Bet365 usa clases hash inestables; extraemos por estructura textual
  const allDivs = document.querySelectorAll('div');
  const results = [];
  const seen    = new Set();

  for (const div of allDivs) {
    if (div.children.length > 4) continue;
    const text = div.innerText?.replace(/\\n/g, '|') || '';

    // Una sola ocurrencia de 1|odd|X|odd|2|odd en este div
    const oddsRe = /\\|1\\|(\\d+\\.?\\d*)\\|X\\|(\\d+\\.?\\d*)\\|2\\|(\\d+\\.?\\d*)/g;
    const found  = [...text.matchAll(oddsRe)];
    if (found.length !== 1) continue;

    const m = found[0];
    const beforeOdds = text.substring(0, m.index);
    const parts = beforeOdds.split('|').map(s => s.trim()).filter(Boolean);
    const timeIdx = parts.findIndex(p => /^\\d{1,2}:\\d{2}$/.test(p));
    if (timeIdx < 2) continue;

    const team1 = parts[timeIdx - 2];
    const team2 = parts[timeIdx - 1];
    const key   = team1 + '|' + team2;
    if (!team1 || !team2 || seen.has(key)) continue;
    seen.add(key);

    results.push({
      partido: team1 + ' vs ' + team2,
      '1': parseFloat(m[1]),
      'X': parseFloat(m[2]),
      '2': parseFloat(m[3]),
    });
  }
  return results;
})()
"""
