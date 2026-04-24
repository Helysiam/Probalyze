"""
Poisson model for football score prediction.

Lambda estimation: λ = attack_strength × defence_weakness × league_avg
Score probability: P(x,y) = Poisson(x;λ_home) × Poisson(y;λ_away)
1X2 probs: sum over relevant cells of the score matrix
"""

import math
from scipy.stats import poisson
import numpy as np
from packages.utils.logger import get_logger

logger = get_logger(__name__)

LEAGUE_AVG_GOALS = 1.35  # typical European league average
MAX_GOALS = 10           # truncate matrix at 10 goals


class PoissonModel:
    def predict(self, features: dict) -> dict:
        lambda_home = self._calc_lambda(
            attack=features["home_attack"],
            defence_opp=features["away_defence"],
        )
        lambda_away = self._calc_lambda(
            attack=features["away_attack"],
            defence_opp=features["home_defence"],
        )

        # Home advantage factor (+8%)
        lambda_home *= 1.08

        score_matrix = self._score_matrix(lambda_home, lambda_away)
        probs = self._outcome_probs(score_matrix)
        probs["prob_over_25"] = self._prob_over(score_matrix, 2.5)
        probs["prob_btts"] = self._prob_btts(score_matrix)
        probs["lambda_home"] = round(lambda_home, 3)
        probs["lambda_away"] = round(lambda_away, 3)
        probs["score_matrix"] = self._matrix_to_json(score_matrix)

        logger.debug(
            f"Poisson: λ_h={lambda_home:.2f} λ_a={lambda_away:.2f} "
            f"H={probs['prob_home_win']:.2%} D={probs['prob_draw']:.2%} A={probs['prob_away_win']:.2%}"
        )
        return probs

    def _calc_lambda(self, attack: float, defence_opp: float) -> float:
        """Expected goals = (team attack / league avg) × (opp defence / league avg) × league avg"""
        attack_strength = attack / LEAGUE_AVG_GOALS
        defence_weakness = defence_opp / LEAGUE_AVG_GOALS
        return round(attack_strength * defence_weakness * LEAGUE_AVG_GOALS, 4)

    def _score_matrix(self, lh: float, la: float) -> np.ndarray:
        matrix = np.zeros((MAX_GOALS + 1, MAX_GOALS + 1))
        for h in range(MAX_GOALS + 1):
            for a in range(MAX_GOALS + 1):
                matrix[h][a] = poisson.pmf(h, lh) * poisson.pmf(a, la)
        return matrix

    def _outcome_probs(self, matrix: np.ndarray) -> dict:
        home_win = float(np.sum(np.tril(matrix, -1)))   # h > a
        away_win = float(np.sum(np.triu(matrix, 1)))    # a > h
        draw = float(np.trace(matrix))

        total = home_win + away_win + draw
        return {
            "prob_home_win": round(home_win / total, 4),
            "prob_draw": round(draw / total, 4),
            "prob_away_win": round(away_win / total, 4),
        }

    def _prob_over(self, matrix: np.ndarray, threshold: float) -> float:
        prob = 0.0
        for h in range(MAX_GOALS + 1):
            for a in range(MAX_GOALS + 1):
                if (h + a) > threshold:
                    prob += matrix[h][a]
        return round(float(prob), 4)

    def _prob_btts(self, matrix: np.ndarray) -> float:
        prob = 0.0
        for h in range(1, MAX_GOALS + 1):
            for a in range(1, MAX_GOALS + 1):
                prob += matrix[h][a]
        return round(float(prob), 4)

    def _matrix_to_json(self, matrix: np.ndarray) -> dict:
        # Store first 6×6 for display purposes
        result = {}
        for h in range(6):
            for a in range(6):
                result[f"{h}-{a}"] = round(float(matrix[h][a]), 5)
        return result
