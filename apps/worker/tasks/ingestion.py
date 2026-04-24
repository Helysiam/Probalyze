import asyncio
from packages.utils.logger import get_logger
from packages.db.client import get_supabase_client
from services.scrapers.understat import UnderstatScraper
from services.scrapers.fbref import FBrefScraper
from services.odds.fetcher import OddsFetcher

logger = get_logger(__name__)


async def run_ingestion_cycle():
    db = get_supabase_client()

    # Run scrapers concurrently
    results = await asyncio.gather(
        _ingest_understat(db),
        _ingest_odds(db),
        return_exceptions=True,
    )

    for i, r in enumerate(results):
        if isinstance(r, Exception):
            logger.error(f"Ingestion task {i} failed: {r}")


async def _ingest_understat(db):
    scraper = UnderstatScraper()
    leagues = ["EPL", "La_liga", "Bundesliga", "Serie_A", "Ligue_1"]
    season = "2024"

    for league in leagues:
        try:
            logger.info(f"Scraping Understat: {league} {season}")
            matches = await scraper.fetch_matches(league, season)
            await _upsert_matches(db, matches, source="understat")
            logger.info(f"Understat {league}: {len(matches)} matches ingested")
        except Exception as e:
            logger.error(f"Understat {league} failed: {e}")

    await scraper.close()


async def _ingest_odds(db):
    fetcher = OddsFetcher()
    try:
        sports = ["soccer_epl", "soccer_spain_la_liga", "soccer_germany_bundesliga"]
        for sport in sports:
            logger.info(f"Fetching odds: {sport}")
            odds = await fetcher.fetch_odds(sport)
            await _upsert_odds(db, odds)
            logger.info(f"Odds {sport}: {len(odds)} events processed")
    finally:
        await fetcher.close()


async def _upsert_matches(db, matches: list, source: str):
    for m in matches:
        try:
            # Upsert teams
            home = db.table("teams").upsert(
                {"name": m["home_team"], "slug": _slugify(m["home_team"]), "league": m["league"]},
                on_conflict="slug",
            ).execute()
            away = db.table("teams").upsert(
                {"name": m["away_team"], "slug": _slugify(m["away_team"]), "league": m["league"]},
                on_conflict="slug",
            ).execute()

            home_id = home.data[0]["id"]
            away_id = away.data[0]["id"]

            # Upsert match
            db.table("matches").upsert(
                {
                    "home_team_id": home_id,
                    "away_team_id": away_id,
                    "league": m["league"],
                    "season": m.get("season"),
                    "match_date": m.get("date"),
                    "status": m.get("status", "scheduled"),
                    "home_score": m.get("home_score"),
                    "away_score": m.get("away_score"),
                    "understat_id": m.get("id"),
                    "raw_data": m,
                },
                on_conflict="understat_id",
            ).execute()

        except Exception as e:
            logger.error(f"Upsert match error: {e}")


async def _upsert_odds(db, odds_list: list):
    for o in odds_list:
        try:
            # Find match by teams + date
            result = db.table("matches").select("id").eq(
                "understat_id", o.get("match_id", "")
            ).execute()

            if not result.data:
                continue

            match_id = result.data[0]["id"]
            db.table("odds").insert(
                {
                    "match_id": match_id,
                    "bookmaker": o["bookmaker"],
                    "market": o["market"],
                    "home_win": o.get("home"),
                    "draw": o.get("draw"),
                    "away_win": o.get("away"),
                    "over_25": o.get("over_2_5"),
                    "under_25": o.get("under_2_5"),
                    "raw_data": o,
                }
            ).execute()

        except Exception as e:
            logger.error(f"Upsert odds error: {e}")


def _slugify(name: str) -> str:
    return name.lower().replace(" ", "-").replace(".", "").replace("'", "")
