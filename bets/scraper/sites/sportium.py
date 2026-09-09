from __future__ import annotations
from playwright.async_api import Page
from ..base import ScraperBase


class SportiumScraper(ScraperBase):
    CASA = "Sportium"
    URL_FUTBOL = "https://www.sportium.es/apuestas/sports/soccer/matches"

    async def extraer(self, page: Page) -> list[dict]:
        await page.wait_for_selector(".ta-price_text", timeout=25_000)
        await page.wait_for_timeout(1500)  # deja que innerText se rellene
        return await page.evaluate(_JS_EXTRACT)


_JS_EXTRACT = """
(() => {
  const items = document.querySelectorAll('.ta-EventListItem');
  const results = [];

  for (const item of items) {
    const mres = item.querySelector('.ta-MarketType-MRES');
    if (!mres) continue;

    const prices = [...mres.querySelectorAll('.ta-price_text')]
      .map(e => e.innerText.trim())
      .filter(v => v && !isNaN(parseFloat(v)));
    if (prices.length < 3) continue;

    const text  = item.innerText.replace(/\\n/g, '|');
    const parts = text.split('|').map(s => s.trim()).filter(Boolean);
    // parts[0] = time string ("Hoy, 16:45"), parts[1] = team1, parts[2] = team2
    if (parts.length < 3) continue;

    const team1 = parts[1];
    const team2 = parts[2];
    if (!team1 || !team2) continue;

    results.push({
      partido: team1 + ' vs ' + team2,
      fecha:   parts[0],
      '1': parseFloat(prices[0]),
      'X': parseFloat(prices[1]),
      '2': parseFloat(prices[2]),
    });
  }
  return results;
})()
"""
