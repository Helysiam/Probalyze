import asyncio
import aiohttp
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from packages.utils.logger import get_logger

logger = get_logger(__name__)

DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json, text/html,*/*",
    "Accept-Language": "en-US,en;q=0.9",
}


class BaseScraper:
    def __init__(self, base_url: str = "", timeout: int = 30):
        self.base_url = base_url
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self._session: aiohttp.ClientSession | None = None

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers=DEFAULT_HEADERS,
                timeout=self.timeout,
            )
        return self._session

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        retry=retry_if_exception_type((aiohttp.ClientError, asyncio.TimeoutError)),
        reraise=True,
    )
    async def get(self, url: str, params: dict = None, headers: dict = None) -> dict | str:
        session = await self._get_session()
        logger.debug(f"GET {url} params={params}")
        async with session.get(url, params=params, headers=headers) as resp:
            resp.raise_for_status()
            content_type = resp.headers.get("Content-Type", "")
            if "json" in content_type:
                return await resp.json()
            return await resp.text()

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()
