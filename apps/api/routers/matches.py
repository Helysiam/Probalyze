from fastapi import APIRouter, Query, Depends, HTTPException
from typing import Optional
from datetime import date
import json

from packages.db.client import get_supabase
from packages.utils.cache import cached
from packages.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("")
@cached(ttl=120, key_prefix="matches")
async def list_matches(
    league: Optional[str] = None,
    status: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db=Depends(get_supabase),
):
    offset = (page - 1) * page_size
    query = db.table("matches").select(
        "*, home_team:teams!home_team_id(name, slug), away_team:teams!away_team_id(name, slug)"
    )

    if league:
        query = query.eq("league", league)
    if status:
        query = query.eq("status", status)
    if date_from:
        query = query.gte("match_date", date_from.isoformat())
    if date_to:
        query = query.lte("match_date", date_to.isoformat())

    query = query.order("match_date", desc=True).range(offset, offset + page_size - 1)

    result = query.execute()
    return {"data": result.data, "page": page, "page_size": page_size, "total": len(result.data)}


@router.get("/{match_id}")
async def get_match(match_id: str, db=Depends(get_supabase)):
    result = db.table("matches").select(
        "*, home_team:teams!home_team_id(*), away_team:teams!away_team_id(*), stats(*), odds(*), predictions(*)"
    ).eq("id", match_id).single().execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="Match not found")
    return result.data
