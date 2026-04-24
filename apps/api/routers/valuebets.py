from fastapi import APIRouter, Query, Depends, HTTPException
from typing import Optional
from datetime import date

from packages.db.client import get_supabase
from packages.utils.cache import cached

router = APIRouter()


@router.get("")
@cached(ttl=60, key_prefix="valuebets")
async def list_value_bets(
    min_value: float = Query(0.0, description="Minimum edge (0 = all positive value)"),
    market: Optional[str] = None,
    bookmaker: Optional[str] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    is_active: bool = True,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("value", regex="^(value|odds_value|probability|created_at)$"),
    db=Depends(get_supabase),
):
    offset = (page - 1) * page_size
    query = db.table("value_bets").select(
        "*, match:matches(id, match_date, league, status, "
        "home_team:teams!home_team_id(name, slug), "
        "away_team:teams!away_team_id(name, slug))"
    )

    query = query.eq("is_active", is_active)
    query = query.gte("value", min_value)

    if market:
        query = query.eq("market", market)
    if bookmaker:
        query = query.eq("bookmaker", bookmaker)
    if date_from:
        query = query.gte("created_at", date_from.isoformat())
    if date_to:
        query = query.lte("created_at", date_to.isoformat())

    result = query.order(sort_by, desc=True).range(offset, offset + page_size - 1).execute()
    return {
        "data": result.data,
        "page": page,
        "page_size": page_size,
        "filters": {"min_value": min_value, "market": market, "bookmaker": bookmaker},
    }


@router.get("/summary")
@cached(ttl=300, key_prefix="valuebets_summary")
async def value_bets_summary(db=Depends(get_supabase)):
    result = db.table("value_bets").select("market, bookmaker, value, odds_value, probability").eq("is_active", True).execute()
    data = result.data

    if not data:
        return {"total": 0, "avg_value": 0, "avg_odds": 0, "by_market": {}}

    import statistics
    values = [r["value"] for r in data if r["value"] is not None]
    by_market = {}
    for r in data:
        m = r["market"]
        by_market.setdefault(m, []).append(r["value"])

    return {
        "total": len(data),
        "avg_value": round(statistics.mean(values), 4) if values else 0,
        "avg_odds": round(sum(r["odds_value"] for r in data if r["odds_value"]) / len(data), 3),
        "by_market": {m: {"count": len(v), "avg_value": round(statistics.mean(v), 4)} for m, v in by_market.items()},
    }


@router.get("/{vb_id}")
async def get_value_bet(vb_id: str, db=Depends(get_supabase)):
    result = db.table("value_bets").select("*").eq("id", vb_id).single().execute()
    if not result.data:
        raise HTTPException(status_code=404, detail="Value bet not found")
    return result.data
