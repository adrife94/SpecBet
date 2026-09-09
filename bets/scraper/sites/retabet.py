from __future__ import annotations
from playwright.async_api import Page
from ..base import ScraperBase


class RetabetScraper(ScraperBase):
    CASA = "Retabet"
    URL_FUTBOL = "https://canarias.retabet.es/deportes/futbol"

    async def extraer(self, page: Page) -> list[dict]:
        await page.wait_for_selector("li.event__item", timeout=20_000)
        return await page.evaluate(_JS_EXTRACT)


_JS_EXTRACT = """
(() => {
  // Retabet: li.event__item contiene "team1|team2|1|odd1|X|oddX|2|odd2|..."
  const items = document.querySelectorAll('li.event__item');
  const results = [];

  for (const item of items) {
    const text = item.innerText.replace(/\\n/g, '|');
    const m = text.match(/^([^|]+)\\|([^|]+)\\|1\\|([\\d,]+)\\|X\\|([\\d,]+)\\|2\\|([\\d,]+)/);
    if (!m) continue;

    results.push({
      partido: m[1].trim() + ' vs ' + m[2].trim(),
      '1': parseFloat(m[3].replace(',', '.')),
      'X': parseFloat(m[4].replace(',', '.')),
      '2': parseFloat(m[5].replace(',', '.')),
    });
  }
  return results;
})()
"""
