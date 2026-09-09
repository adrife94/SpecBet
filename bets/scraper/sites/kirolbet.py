from __future__ import annotations
from playwright.async_api import Page
from ..base import ScraperBase


class KirolbetScraper(ScraperBase):
    CASA = "Kirolbet"
    URL_FUTBOL = "https://canarias.kirolbet.es/esp/Sport/Hoy/ProximosEventos"

    async def extraer(self, page: Page) -> list[dict]:
        await page.wait_for_selector("li.filtroCategoria", timeout=25_000)
        await page.wait_for_timeout(1500)
        return await page.evaluate(_JS_EXTRACT)


_JS_EXTRACT = """
(() => {
  // Kirolbet – li.filtroCategoria contiene cada partido con mercado 1X2
  // Formato: "LIVE|...|TEAM1 VS. TEAM2 (+N)|handicap...|1||odd1|...|X||oddX|...|2||odd2"
  const items = document.querySelectorAll('li.filtroCategoria');
  const results = [];
  const seen = new Set();

  for (const item of items) {
    const text = item.innerText.replace(/\\n/g, '|').replace(/\\s{2,}/g, '|');

    const nameMatch = text.match(/([A-Z\\u00C0-\\u024F][^|]{3,}?)\\s+VS\\.\\s+([A-Z\\u00C0-\\u024F][^|]{3,}?)(?:\\s*\\(\\+|\\|)/i);
    if (!nameMatch) continue;

    const team1 = nameMatch[1].trim().replace(/\\s+/g, ' ');
    const team2 = nameMatch[2].trim().replace(/\\s+/g, ' ');

    // Odds: "1||odd1...X||oddX...2||odd2"
    const oddsMatch = text.match(/1\\|\\|?([\\d,]+).*?X\\|\\|?([\\d,]+).*?2\\|\\|?([\\d,]+)/);
    if (!oddsMatch) continue;

    const key = team1 + '|' + team2;
    if (seen.has(key)) continue;
    seen.add(key);

    results.push({
      partido: team1 + ' vs ' + team2,
      '1': parseFloat(oddsMatch[1].replace(',', '.')),
      'X': parseFloat(oddsMatch[2].replace(',', '.')),
      '2': parseFloat(oddsMatch[3].replace(',', '.')),
    });
  }
  return results;
})()
"""
