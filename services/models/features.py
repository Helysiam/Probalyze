from packages.utils.logger import get_logger

logger = get_logger(__name__)

N_RECENT = 10  # number of recent matches for form calculation


class FeatureEngineer:
    def __init__(self, db):
        self.db = db

    async def extract(self, home_team_id: str, away_team_id: str) -> dict:
        home_stats = await self._team_stats(home_team_id, is_home=True)
        away_stats = await self._team_stats(away_team_id, is_home=False)

        return {
            "home_team_id": home_team_id,
            "away_team_id": away_team_id,
            # Expected goals (attack / defence proxies)
            "home_attack": home_stats["avg_xg_for"],
            "home_defence": home_stats["avg_xg_against"],
            "away_attack": away_stats["avg_xg_for"],
            "away_defence": away_stats["avg_xg_against"],
            # Possession
            "home_possession": home_stats["avg_possession"],
            "away_possession": away_stats["avg_possession"],
            # Form (last N games)
            "home_form": home_stats["form"],
            "away_form": away_stats["form"],
        }

    async def _team_stats(self, team_id: str, is_home: bool) -> dict:
        result = self.db.table("stats").select(
            "xg, xga, possession, match:matches(home_score, away_score, home_team_id)"
        ).eq("team_id", team_id).eq("is_home", is_home).order(
            "created_at", desc=True
        ).limit(N_RECENT).execute()

        rows = result.data or []

        if not rows:
            return self._default_stats()

        xg_values = [r["xg"] for r in rows if r.get("xg") is not None]
        xga_values = [r["xga"] for r in rows if r.get("xga") is not None]
        poss_values = [r["possession"] for r in rows if r.get("possession") is not None]

        avg_xg = sum(xg_values) / len(xg_values) if xg_values else 1.3
        avg_xga = sum(xga_values) / len(xga_values) if xga_values else 1.3
        avg_poss = sum(poss_values) / len(poss_values) if poss_values else 50.0

        # Form: points from last N (3W 1D 0L → "WWWDL…")
        form = self._calc_form(rows, team_id, is_home)

        return {
            "avg_xg_for": round(avg_xg, 3),
            "avg_xg_against": round(avg_xga, 3),
            "avg_possession": round(avg_poss, 2),
            "form": form,
        }

    def _calc_form(self, rows: list, team_id: str, is_home: bool) -> str:
        form = []
        for r in rows[:5]:
            match = r.get("match", {})
            if not match:
                continue
            h_score = match.get("home_score")
            a_score = match.get("away_score")
            if h_score is None or a_score is None:
                continue

            if is_home:
                if h_score > a_score:
                    form.append("W")
                elif h_score == a_score:
                    form.append("D")
                else:
                    form.append("L")
            else:
                if a_score > h_score:
                    form.append("W")
                elif a_score == h_score:
                    form.append("D")
                else:
                    form.append("L")

        return "".join(form) or "UNKNOWN"

    @staticmethod
    def _default_stats() -> dict:
        # League average fallback
        return {
            "avg_xg_for": 1.35,
            "avg_xg_against": 1.35,
            "avg_possession": 50.0,
            "form": "UNKNOWN",
        }
