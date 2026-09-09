from __future__ import annotations
import re
from playwright.async_api import Page
from ..base import ScraperBase


class WinamaxScraper(ScraperBase):
    CASA = "Winamax"
    URL_FUTBOL = "https://www.winamax.es/apuestas-deportivas/sports/1"

    async def extraer(self, page: Page) -> list[dict]:
        await page.wait_for_selector('[data-testid^="match-card-"]', timeout=15_000)
        return await page.evaluate(_JS_EXTRACT)


_JS_EXTRACT = """
(() => {
  const cards = document.querySelectorAll('[data-testid^="match-card-"]');
  const results = [];

  for (const card of cards) {
    const oddButtons = card.querySelectorAll('.bet-group-outcome-odd');
    if (oddButtons.length !== 3) continue;

    const oddValues = [...oddButtons].map(btn => {
      const valueEl = btn.querySelector('.odd-button-value');
      return valueEl?.innerText.trim().replace(',', '.') || '';
    });
    if (oddValues.some(v => !v || isNaN(parseFloat(v)))) continue;

    // Team names: anchor en HH:MM o en "Mañana HH:MM" / "Hoy HH:MM"
    const cardText = card.innerText.replace(/\\n/g, '|');
    // Buscar patrón de hora con o sin prefijo de día
    const timeMatch = cardText.match(/\\|(?:(?:Hoy|Ma[ñn]ana|[A-Za-záéíóú]+)\\s+)?(\\d{1,2}:\\d{2})\\|/i);
    let home = '', away = '';
    if (timeMatch) {
      const anchorIdx = cardText.indexOf(timeMatch[0]);
      const before = cardText.substring(0, anchorIdx);
      const after  = cardText.substring(anchorIdx + timeMatch[0].length);
      const beforeParts = before.split('|').filter(s => s.trim() && s.trim().length > 2 && !/^(Hoy|Ma[ñn]ana|J\d)$/i.test(s.trim()));
      home = beforeParts[beforeParts.length - 1]?.trim() || '';
      away = after.split('|').find(s => s.trim() && s.trim().length > 2)?.trim() || '';
    }
    if (!home || !away) continue;

    const entry = { partido: home + ' vs ' + away, '1': parseFloat(oddValues[0]), 'X': parseFloat(oddValues[1]), '2': parseFloat(oddValues[2]) };
    results.push(entry);
  }
  return results;
})()
"""
