"""
Value Bet Calculator

Value = (decimal_odds × probability) - 1
  > 0 → positive expected value (value bet)

Kelly Criterion (fractional):
  f = (b×p - q) / b
  where b = odds - 1, p = probability, q = 1 - p
"""

from packages.utils.logger import get_logger

logger = get_logger(__name__)

MARKETS = {
    "home_win": ("home_win", "prob_home_win"),
    "draw": ("draw", "prob_draw"),
    "away_win": ("away_win", "prob_away_win"),
    "over_25": ("over_25", "prob_over_25"),
}


class ValueBetCalculator:
    def calculate(self, prediction: dict, odds_row: dict) -> list[dict]:
        results = []

        for market, (odds_field, prob_field) in MARKETS.items():
            odds = odds_row.get(odds_field)
            prob = prediction.get(prob_field)

            if odds is None or prob is None:
                continue
            if odds <= 1.0 or prob <= 0.0:
                continue

            value = round((odds * prob) - 1, 4)
            kelly = self._kelly(odds, prob)

            results.append({
                "market": market,
                "outcome": market.replace("_", " ").title(),
                "odds": float(odds),
                "probability": float(prob),
                "value": value,
                "kelly": kelly,
                "is_value": value > 0,
            })

        return results

    def _kelly(self, odds: float, prob: float) -> float:
        b = odds - 1
        q = 1 - prob
        if b <= 0:
            return 0.0
        fraction = (b * prob - q) / b
        # Cap at 25% of bankroll (avoid ruin)
        return round(max(0.0, min(fraction, 0.25)), 4)

    def filter_value_bets(self, bets: list[dict], min_value: float = 0.0) -> list[dict]:
        return [b for b in bets if b["value"] > min_value]
