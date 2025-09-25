from __future__ import annotations
import asyncio, random
from urllib.parse import urlparse

class AsyncIntervalLimiter:
    """
    Enforces an inter-request gap across concurrent tasks.
    Default: 50–100 ms (Scryfall's guidance).
    """
    def __init__(self, min_interval: float = 0.06, jitter: tuple[float, float] | None = (0.0, 0.06)):
        self.min_interval = float(min_interval)
        self.jitter = jitter
        self._lock = asyncio.Lock()
        self._next_ok = 0.0  # event-loop time

    async def wait(self):
        async with self._lock:
            now = asyncio.get_running_loop().time()
            if now < self._next_ok:
                await asyncio.sleep(self._next_ok - now)
                now = self._next_ok
            extra = random.uniform(*self.jitter) if self.jitter else 0.0
            self._next_ok = now + self.min_interval + extra

SCRYFALL_HOST = "api.scryfall.com"
SCRYFALL_LIMITER = AsyncIntervalLimiter(0.06, (0.0, 0.06))

def configure_scryfall_rate(min_interval: float = 0.06, jitter: tuple[float, float] | None = (0.0, 0.06)) -> None:
    """Adjust spacing without touching call sites."""
    SCRYFALL_LIMITER.min_interval = float(min_interval)
    SCRYFALL_LIMITER.jitter = jitter

async def scryfall_get(client, url: str = "https://api.scryfall.com/cards/search", **kwargs):
    """Drop-in wrapper: await scryfall_get(client, url, ...)"""
    if urlparse(url).netloc == SCRYFALL_HOST:
        await SCRYFALL_LIMITER.wait()
    return await client.get(url, **kwargs)

async def rate_limited_get(client, url: str, **kwargs):
    if urlparse(url).netloc == SCRYFALL_HOST:
        await SCRYFALL_LIMITER.wait()
    return await client.get(url, **kwargs)
