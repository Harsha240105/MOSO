from __future__ import annotations

import asyncio
import logging
import re
import time
from typing import Optional
from urllib.parse import urlparse

from moso_core.realtime.models import FetchResult
from moso_core.realtime.sources import SourceDefinition, get_sources_for_url

logger = logging.getLogger(__name__)

FETCH_TIMEOUT = 15
MAX_REDIRECTS = 5
MAX_TEXT_SIZE = 500_000

try:
    import aiohttp

    AIOHTTP_AVAILABLE = True
except ImportError:
    AIOHTTP_AVAILABLE = False

try:
    from bs4 import BeautifulSoup

    BEAUTIFULSOUP_AVAILABLE = True
except ImportError:
    BEAUTIFULSOUP_AVAILABLE = False


def strip_html(html: str) -> str:
    if BEAUTIFULSOUP_AVAILABLE:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()
        text = soup.get_text(separator="\n")
    else:
        text = re.sub(r"<[^>]+>", " ", html)
        text = re.sub(r"\s+", " ", text)
    lines = (line.strip() for line in text.splitlines())
    return "\n".join(line for line in lines if line)


def extract_title(html: str) -> str:
    match = re.search(r"<title[^>]*>([^<]+)</title>", html, re.IGNORECASE)
    return match.group(1).strip() if match else ""


def truncate_text(text: str, max_chars: int = MAX_TEXT_SIZE) -> str:
    if len(text) > max_chars:
        return text[:max_chars] + f"\n\n[...truncated at {max_chars} chars]"
    return text


class Fetcher:
    def __init__(self):
        self._session: Optional[aiohttp.ClientSession] = None
        self._user_agent = (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )

    async def _get_session(self) -> aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            timeout = aiohttp.ClientTimeout(total=FETCH_TIMEOUT)
            connector = aiohttp.TCPConnector(
                limit=10,
                ttl_dns_cache=300,
                ssl=True,
            )
            self._session = aiohttp.ClientSession(
                timeout=timeout,
                connector=connector,
                headers={"User-Agent": self._user_agent},
            )
        return self._session

    async def fetch_url(
        self,
        url: str,
        source_name: str = "",
        tls_verify: bool = True,
    ) -> FetchResult:
        if not AIOHTTP_AVAILABLE:
            return FetchResult(
                url=url,
                source_name=source_name or url,
                raw_text="",
                parsed_text="aiohttp is not installed. Install with: pip install aiohttp",
                status_code=0,
                error="aiohttp not available",
            )

        session = await self._get_session()
        redirect_chain: list[str] = []
        current_url = url
        fetch_start = time.time()

        for hop in range(MAX_REDIRECTS + 1):
            try:
                async with session.get(
                    current_url,
                    allow_redirects=False,
                    ssl=True,
                ) as resp:
                    status = resp.status
                    content_type = resp.content_type or "text/plain"

                    if status in (301, 302, 303, 307, 308):
                        location = resp.headers.get("Location", "")
                        if not location:
                            break
                        redirect_chain.append(current_url)
                        current_url = location
                        logger.debug("Redirect %d -> %s", hop + 1, location)
                        continue

                    raw = await resp.read()
                    raw_text = raw.decode("utf-8", errors="replace")
                    raw_text = truncate_text(raw_text)

                    encoding = resp.charset or "utf-8"
                    try:
                        decoded = raw.decode(encoding, errors="replace")
                    except (LookupError, UnicodeDecodeError):
                        decoded = raw.decode("utf-8", errors="replace")

                    parsed = extract_title(decoded) + "\n\n" + strip_html(decoded)
                    parsed = truncate_text(parsed)

                    elapsed = time.time() - fetch_start
                    logger.info(
                        "Fetched %s (%d, %.1fs, %d chars)",
                        url, status, elapsed, len(parsed),
                    )

                    return FetchResult(
                        url=url,
                        source_name=source_name or url,
                        raw_text=raw_text,
                        parsed_text=parsed,
                        status_code=status,
                        timestamp=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                        content_type=content_type,
                        redirect_chain=redirect_chain,
                        tls_verified=True,
                    )

            except asyncio.TimeoutError:
                logger.warning("Timeout fetching %s", url)
                return FetchResult(
                    url=url,
                    source_name=source_name or url,
                    raw_text="",
                    parsed_text="",
                    status_code=0,
                    error=f"Timeout after {FETCH_TIMEOUT}s",
                )
            except aiohttp.ClientError as e:
                logger.warning("HTTP error fetching %s: %s", url, e)
                return FetchResult(
                    url=url,
                    source_name=source_name or url,
                    raw_text="",
                    parsed_text="",
                    status_code=0,
                    error=str(e),
                )

        return FetchResult(
            url=url,
            source_name=source_name or url,
            raw_text="",
            parsed_text="",
            status_code=0,
            error=f"Too many redirects ({len(redirect_chain)})",
            redirect_chain=redirect_chain,
        )

    async def fetch_multiple(
        self,
        urls: list[str],
        source_names: Optional[list[str]] = None,
    ) -> list[FetchResult]:
        tasks = []
        for i, url in enumerate(urls):
            name = source_names[i] if source_names and i < len(source_names) else ""
            tasks.append(self.fetch_url(url, source_name=name))
        return await asyncio.gather(*tasks)

    async def fetch_by_source(
        self,
        sources: list[SourceDefinition],
        use_cache: bool = True,
        cache=None,
        ttl_override: Optional[int] = None,
    ) -> list[FetchResult]:
        results = []
        to_fetch: list[tuple[str, str]] = []
        for src in sources:
            if use_cache and cache:
                cached = cache.get(src.url)
                if cached is not None:
                    results.append(cached)
                    continue
            to_fetch.append((src.url, src.name))

        if to_fetch:
            urls = [t[0] for t in to_fetch]
            names = [t[1] for t in to_fetch]
            fetched = await self.fetch_multiple(urls, source_names=names)
            for result in fetched:
                if use_cache and cache and result.success:
                    cache.set(result.url, result, ttl=ttl_override)
                results.append(result)

        results.sort(key=lambda r: r.success, reverse=True)
        return results

    async def close(self):
        if self._session and not self._session.closed:
            await self._session.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._session and not self._session.closed:
            asyncio.create_task(self._session.close())
