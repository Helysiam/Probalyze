from packages.utils.logger import get_logger
from packages.db.client import get_supabase_client
from packages.utils.config import settings
from services.models.poisson import PoissonModel
from services.models.features import FeatureEngineer
from services.models.value_bet import ValueBetCalculator

logger = get_logger(__name__)


async def run_compute_cycle():
    db = get_supabase_client()

    # Fetch upcoming matches without predictions
    result = db.table("matches").select(
        "id, home_team_id, away_team_id, league"
    ).eq("status", "scheduled").is_("id", None).execute()

    # Get matches that don't have predictions yet
    matches_result = db.table("matches").select("id, home_team_id, away_team_id, league").eq(
        "status", "scheduled"
    ).execute()

    existing_preds = db.table("predictions").select("match_id").execute()
    predicted_ids = {p["match_id"] for p in existing_preds.data}

    pending = [m for m in matches_result.data if m["id"] not in predicted_ids]
    logger.info(f"Computing predictions for {len(pending)} matches...")

    feature_eng = FeatureEngineer(db)
    model = PoissonModel()
    vb_calc = ValueBetCalculator()

    for match in pending:
        try:
            features = await feature_eng.extract(match["home_team_id"], match["away_team_id"])
            prediction = model.predict(features)

            # Store prediction
            pred_result = db.table("predictions").insert({
                "match_id": match["id"],
                "model_version": settings.MODEL_VERSION,
                "lambda_home": prediction["lambda_home"],
                "lambda_away": prediction["lambda_away"],
                "prob_home_win": prediction["prob_home_win"],
                "prob_draw": prediction["prob_draw"],
                "prob_away_win": prediction["prob_away_win"],
                "prob_over_25": prediction["prob_over_25"],
                "prob_btts": prediction["prob_btts"],
                "score_matrix": prediction["score_matrix"],
            }).execute()

            prediction_id = pred_result.data[0]["id"]

            # Find odds for this match
            odds_result = db.table("odds").select("*").eq("match_id", match["id"]).execute()

            for odds_row in odds_result.data:
                vbs = vb_calc.calculate(prediction, odds_row)
                for vb in vbs:
                    if vb["value"] > 0:
                        db.table("value_bets").insert({
                            "match_id": match["id"],
                            "prediction_id": prediction_id,
                            "odds_id": odds_row["id"],
                            "bookmaker": odds_row["bookmaker"],
                            "market": vb["market"],
                            "outcome": vb["outcome"],
                            "odds_value": vb["odds"],
                            "probability": vb["probability"],
                            "value": vb["value"],
                            "kelly_fraction": vb["kelly"],
                        }).execute()

        except Exception as e:
            logger.error(f"Compute error for match {match['id']}: {e}")
