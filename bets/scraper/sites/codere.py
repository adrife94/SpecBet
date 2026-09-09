from __future__ import annotations
from playwright.async_api import Page
from ..base import ScraperBase


class CodereSccraper(ScraperBase):
    CASA = "Codere"
    # Homepage muestra los partidos destacados de fútbol con cuotas 1X2
    URL_FUTBOL = "https://m.apuestas.codere.es/deportesEs/#/HomePage"

    async def extraer(self, page: Page) -> list[dict]:
        await page.wait_for_selector(".game-row", timeout=15_000)
        return await page.evaluate(_JS_EXTRACT)


_JS_EXTRACT = """
(() => {
  const rows = document.querySelectorAll('.game-row');
  const results = [];

  for (const row of rows) {
    const text = row.innerText.replace(/\\n/g, '|');

    // Descartar partidos en directo (tienen marcador tipo "0|0|1º Tiempo")
    if (/\\d+\\|\\d+\\|\\d+.*Tiempo|DIRECTO|\\d+'/i.test(text)) continue;

    // Extraer cuotas 1X2
    const m = text.match(/\\b1\\|(\\d+[,.]?\\d*)\\|X\\|(\\d+[,.]?\\d*)\\|2\\|(\\d+[,.]?\\d*)/);
    if (!m) continue;

    // Equipos aparecen antes de la fecha
    const parts = text.split('|').map(s => s.trim()).filter(Boolean);
    const timeIdx = parts.findIndex(p => /^(Hoy|Mañana|\\d{2}\\/\\d{2})/.test(p));
    if (timeIdx < 2) continue;

    const team1 = parts[timeIdx - 2];
    const team2 = parts[timeIdx - 1];
    if (!team1 || !team2) continue;

    results.push({
      partido: team1 + ' vs ' + team2,
      '1': parseFloat(m[1].replace(',', '.')),
      'X': parseFloat(m[2].replace(',', '.')),
      '2': parseFloat(m[3].replace(',', '.')),
    });
  }
  return results;
})()
"""
