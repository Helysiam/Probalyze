from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import redis.asyncio as aioredis

from apps.api.routers import matches, teams, odds, predictions, valuebets
from packages.utils.logger import get_logger
from packages.utils.config import settings

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Probalyze API...")
    app.state.redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    yield
    await app.state.redis.aclose()
    logger.info("API shutdown.")


app = FastAPI(
    title="Probalyze API",
    description="Football value bet detection platform",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(matches.router, prefix="/matches", tags=["Matches"])
app.include_router(teams.router, prefix="/teams", tags=["Teams"])
app.include_router(odds.router, prefix="/odds", tags=["Odds"])
app.include_router(predictions.router, prefix="/predictions", tags=["Predictions"])
app.include_router(valuebets.router, prefix="/valuebets", tags=["Value Bets"])


@app.get("/health")
async def health():
    return {"status": "ok", "service": "probalyze-api"}
