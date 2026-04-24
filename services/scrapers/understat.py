import json
import re
from datetime import datetime
from services.scrapers.base import BaseScraper
from packages.utils.logger import get_logger

logger = get_logger(__name__)

LEAGUES = {
    "EPL": "epl",
    "La_liga": "la_liga",
    "Bundesliga": "bundesliga",
    "Serie_A": "serie_a",
    "Ligue_1": "ligue_1",
    "RFPL": "rfpl",
}


class UnderstatScraper(BaseScraper):
    def __init__(self):
        super().__init__(base_url="https://understat.com")

    async def fetch_matches(self, league: str, season: str) -> list[dict]:
        url = f"{self.base_url}/league/{league}/{season}"
        html = await self.get(url, headers={"Accept": "text/html"})
        return self._parse_matches(html, league, season)

    def _parse_matches(self, html: str, league: str, season: str) -> list[dict]:
        pattern = r"var datesData\s*=\s*JSON\.parse\('(.+?)'\)"
        match = re.search(pattern, html)
        if not match:
            logger.warning(f"No datesData found for {league}/{season}")
            return []

        raw = match.group(1).encode().decode("unicode_escape")
        data = json.loads(raw)

        matches = []
        for m in data:
            try:
                matches.append({
                    "id": m.get("id"),
                    "league": league,
                    "season": season,
                    "date": m.get("datetime"),
                    "home_team": m.get("h", {}).get("title", ""),
                    "away_team": m.get("a", {}).get("title", ""),
                    "home_score": int(m["goals"]["h"]) if m.get("goals", {}).get("h") else None,
                    "away_score": int(m["goals"]["a"]) if m.get("goals", {}).get("a") else None,
                    "home_xg": float(m["xG"]["h"]) if m.get("xG", {}).get("h") else None,
                    "away_xg": float(m["xG"]["a"]) if m.get("xG", {}).get("a") else None,
                    "status": "finished" if m.get("isResult") else "scheduled",
                })
            except (KeyError, ValueError, TypeError) as e:
                logger.debug(f"Match parse error: {e}")

        logger.info(f"Understat {league}/{season}: parsed {len(matches)} matches")
        return matches

    async def fetch_team_stats(self, team_id: str) -> dict:
        url = f"{self.base_url}/team/{team_id}"
        html = await self.get(url, headers={"Accept": "text/html"})
        return self._parse_team_stats(html)

    def _parse_team_stats(self, html: str) -> dict:
        patterns = {
            "history": r"var historyData\s*=\s*JSON\.parse\('(.+?)'\)",
            "players": r"var playersData\s*=\s*JSON\.parse\('(.+?)'\)",
        }
        result = {}
        for key, pattern in patterns.items():
            m = re.search(pattern, html)
            if m:
                raw = m.group(1).encode().decode("unicode_escape")
                result[key] = json.loads(raw)
        return result
