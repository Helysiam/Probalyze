from fastapi import APIRouter, Query, Depends, HTTPException
from typing import Optional

from packages.db.client import get_supabase
from packages.utils.cache import cached
from packages.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("")
@cached(ttl=300, key_prefix="teams")
async def list_teams(
    league: Optional[str] = None,
    country: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db=Depends(get_supabase),
):
    offset = (page - 1) * page_size
    query = db.table("teams").select("*")

    if league:
        query = query.eq("league", league)
    if country:
        query = query.eq("country", country)

    result = query.order("name").range(offset, offset + page_size - 1).execute()
    return {"data": result.data, "page": page, "page_size": page_size}


@router.get("/{team_id}")
async def get_team(team_id: str, db=Depends(get_supabase)):
    result = db.table("teams").select("*").eq("id", team_id).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Team not found")
    return result.data
