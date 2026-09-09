from __future__ import annotations
from playwright.async_api import Page
from ..base import ScraperBase


class SpeedybetScraper(ScraperBase):
    CASA = "Speedybet"
    # Speedybet usa plataforma Kambi
    URL_FUTBOL = "https://www.speedybet.es/betting#sports-hub/football"

    async def extraer(self, page: Page) -> list[dict]:
        await page.wait_for_selector(".KambiBC-sandwich-filter__event-list-item", timeout=20_000)
        return await page.evaluate(_JS_EXTRACT)


_JS_EXTRACT = """
(() => {
  const items = document.querySelectorAll('.KambiBC-sandwich-filter__event-list-item');
  const results = [];

  for (const item of items) {
    const text  = item.innerText.replace(/\\n/g, '|');
    const parts = text.split('|').map(s => s.trim()).filter(Boolean);

    // Formato: day|time|Team1|Team2|CA|odd1|oddX|odd2|...
    const caIdx = parts.indexOf('CA');
    if (caIdx < 3) continue;

    const team1 = parts[caIdx - 2];
    const team2 = parts[caIdx - 1];
    const odd1  = parts[caIdx + 1];
    const oddX  = parts[caIdx + 2];
    const odd2  = parts[caIdx + 3];

    if (!/^\\d+\\.\\d+$/.test(odd1) || !/^\\d+\\.\\d+$/.test(oddX) || !/^\\d+\\.\\d+$/.test(odd2)) continue;

    results.push({
      partido: team1 + ' vs ' + team2,
      '1': parseFloat(odd1),
      'X': parseFloat(oddX),
      '2': parseFloat(odd2),
    });
  }
  return results;
})()
"""
