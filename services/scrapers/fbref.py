import re
import pandas as pd
from io import StringIO
from services.scrapers.base import BaseScraper
from packages.utils.logger import get_logger

logger = get_logger(__name__)

LEAGUE_URLS = {
    "EPL": "https://fbref.com/en/comps/9/schedule/Premier-League-Scores-and-Fixtures",
    "La_liga": "https://fbref.com/en/comps/12/schedule/La-Liga-Scores-and-Fixtures",
    "Bundesliga": "https://fbref.com/en/comps/20/schedule/Bundesliga-Scores-and-Fixtures",
    "Serie_A": "https://fbref.com/en/comps/11/schedule/Serie-A-Scores-and-Fixtures",
    "Ligue_1": "https://fbref.com/en/comps/13/schedule/Ligue-1-Scores-and-Fixtures",
}


class FBrefScraper(BaseScraper):
    def __init__(self):
        super().__init__(timeout=45)

    async def fetch_fixtures(self, league: str) -> list[dict]:
        url = LEAGUE_URLS.get(league)
        if not url:
            logger.warning(f"FBref: unknown league {league}")
            return []

        html = await self.get(url, headers={"Accept": "text/html"})
        return self._parse_fixtures(html, league)

    def _parse_fixtures(self, html: str, league: str) -> list[dict]:
        try:
            tables = pd.read_html(StringIO(html), attrs={"id": re.compile(r"sched_.*")})
            if not tables:
                logger.warning(f"FBref: no fixture table for {league}")
                return []

            df = tables[0]
            df = df.dropna(subset=["Home", "Away"])

            fixtures = []
            for _, row in df.iterrows():
                try:
                    fixtures.append({
                        "league": league,
                        "date": str(row.get("Date", "")),
                        "time": str(row.get("Time", "")),
                        "home_team": str(row.get("Home", "")),
                        "away_team": str(row.get("Away", "")),
                        "home_score": self._safe_int(row.get("Score", "").split("–")[0] if "–" in str(row.get("Score", "")) else None),
                        "away_score": self._safe_int(row.get("Score", "").split("–")[1] if "–" in str(row.get("Score", "")) else None),
                        "home_xg": self._safe_float(row.get("xG")),
                        "away_xg": self._safe_float(row.get("xG.1")),
                        "fbref_id": str(row.get("Match Report", "")),
                    })
                except Exception as e:
                    logger.debug(f"Row parse error: {e}")

            logger.info(f"FBref {league}: parsed {len(fixtures)} fixtures")
            return fixtures

        except Exception as e:
            logger.error(f"FBref parse error for {league}: {e}")
            return []

    @staticmethod
    def _safe_int(val) -> int | None:
        try:
            return int(val)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _safe_float(val) -> float | None:
        try:
            return float(val)
        except (TypeError, ValueError):
            return None
