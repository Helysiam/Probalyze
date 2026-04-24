from fastapi import APIRouter, Query, Depends, HTTPException
from typing import Optional

from packages.db.client import get_supabase
from packages.utils.cache import cached

router = APIRouter()


@router.get("")
@cached(ttl=120, key_prefix="predictions")
async def list_predictions(
    match_id: Optional[str] = None,
    model_version: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db=Depends(get_supabase),
):
    offset = (page - 1) * page_size
    query = db.table("predictions").select(
        "*, match:matches(match_date, league, home_team:teams!home_team_id(name), away_team:teams!away_team_id(name))"
    )

    if match_id:
        query = query.eq("match_id", match_id)
    if model_version:
        query = query.eq("model_version", model_version)

    result = query.order("computed_at", desc=True).range(offset, offset + page_size - 1).execute()
    return {"data": result.data, "page": page, "page_size": page_size}


@router.get("/{prediction_id}")
async def get_prediction(prediction_id: str, db=Depends(get_supabase)):
    result = db.table("predictions").select("*").eq("id", prediction_id).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Prediction not found")
    return result.data
