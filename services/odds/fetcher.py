from services.scrapers.base import BaseScraper
from packages.utils.config import settings
from packages.utils.logger import get_logger

logger = get_logger(__name__)

SPORT_REGIONS = "eu"
ODDS_MARKETS = "h2h"  # head-to-head = 1X2
BOOKMAKERS = "bet365,unibet,pinnacle,betfair_ex_eu,betclic"


class OddsFetcher(BaseScraper):
    """Fetches odds from the-odds-api.com (free tier: 500 req/month)."""

    def __init__(self):
        super().__init__(base_url=settings.ODDS_API_BASE)

    async def fetch_odds(self, sport: str, markets: str = ODDS_MARKETS) -> list[dict]:
        if not settings.ODDS_API_KEY:
            logger.warning("ODDS_API_KEY not configured — skipping odds fetch")
            return []

        url = f"{self.base_url}/sports/{sport}/odds"
        params = {
            "apiKey": settings.ODDS_API_KEY,
            "regions": SPORT_REGIONS,
            "markets": markets,
            "bookmakers": BOOKMAKERS,
            "oddsFormat": "decimal",
        }

        data = await self.get(url, params=params)
        return self._parse_odds(data, sport)

    def _parse_odds(self, data: list, sport: str) -> list[dict]:
        results = []

        for event in data:
            match_id = event.get("id")
            home = event.get("home_team", "")
            away = event.get("away_team", "")
            commence = event.get("commence_time", "")

            for bookmaker in event.get("bookmakers", []):
                bm_name = bookmaker.get("key", "")
                for market in bookmaker.get("markets", []):
                    market_key = market.get("key")
                    outcomes = {o["name"]: o["price"] for o in market.get("outcomes", [])}

                    results.append({
                        "match_id": match_id,
                        "sport": sport,
                        "home_team": home,
                        "away_team": away,
                        "commence_time": commence,
                        "bookmaker": bm_name,
                        "market": "1X2" if market_key == "h2h" else market_key,
                        "home": outcomes.get(home),
                        "draw": outcomes.get("Draw"),
                        "away": outcomes.get(away),
                        "over_2_5": outcomes.get("Over 2.5"),
                        "under_2_5": outcomes.get("Under 2.5"),
                    })

        logger.info(f"Odds {sport}: {len(results)} bookmaker entries parsed")
        return results

    async def get_remaining_requests(self) -> dict:
        url = f"{self.base_url}/sports"
        params = {"apiKey": settings.ODDS_API_KEY}
        resp = await self.get(url, params=params)
        return resp
