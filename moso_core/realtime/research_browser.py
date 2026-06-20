from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import Optional

logger = logging.getLogger(__name__)

try:
    from playwright.sync_api import sync_playwright, Page, Browser as PlaywrightBrowser

    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


@dataclass
class PageContent:
    url: str
    title: str
    text: str
    html: str
    metadata: dict = field(default_factory=dict)
    links: list[dict] = field(default_factory=list)
    status_code: int = 200
    fetch_time_ms: float = 0.0
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        return self.error is None and self.status_code < 400


USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
]


class ResearchBrowser:
    def __init__(
        self,
        headless: bool = True,
        timeout_ms: int = 30000,
        user_agent_rotation: bool = True,
        viewport: Optional[dict] = None,
    ):
        if not PLAYWRIGHT_AVAILABLE:
            raise ImportError(
                "Playwright is required for ResearchBrowser. "
                "Install with: pip install playwright && playwright install chromium"
            )
        self._headless = headless
        self._timeout_ms = timeout_ms
        self._user_agent_rotation = user_agent_rotation
        self._viewport = viewport or {"width": 1920, "height": 1080}
        self._browser: Optional[PlaywrightBrowser] = None
        self._ua_index = 0

    def _get_user_agent(self) -> str:
        if not self._user_agent_rotation:
            return USER_AGENTS[0]
        ua = USER_AGENTS[self._ua_index % len(USER_AGENTS)]
        self._ua_index += 1
        return ua

    def _create_page(self, playwright) -> Page:
        browser = playwright.chromium.launch(
            headless=self._headless,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-web-security",
                "--disable-features=IsolateOrigins,site-per-process",
            ],
        )
        self._browser = browser
        context = browser.new_context(
            user_agent=self._get_user_agent(),
            viewport=self._viewport,
            locale="en-US",
            timezone_id="America/New_York",
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            },
        )
        page = context.new_page()
        page.set_default_timeout(self._timeout_ms)
        page.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins', { get: () => [1, 2, 3, 4, 5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
        """)
        return page

    def _extract_metadata(self, page: Page) -> dict:
        metadata = {}
        try:
            metadata["title"] = page.title()
        except Exception:
            metadata["title"] = ""
        try:
            metadata["description"] = page.eval_on_selector(
                'meta[name="description"]', "el => el.content"
            )
        except Exception:
            pass
        try:
            metadata["og_title"] = page.eval_on_selector(
                'meta[property="og:title"]', "el => el.content"
            )
        except Exception:
            pass
        try:
            metadata["og_description"] = page.eval_on_selector(
                'meta[property="og:description"]', "el => el.content"
            )
        except Exception:
            pass
        try:
            metadata["og_image"] = page.eval_on_selector(
                'meta[property="og:image"]', "el => el.content"
            )
        except Exception:
            pass
        try:
            metadata["keywords"] = page.eval_on_selector(
                'meta[name="keywords"]', "el => el.content"
            )
        except Exception:
            pass
        try:
            metadata["author"] = page.eval_on_selector(
                'meta[name="author"]', "el => el.content"
            )
        except Exception:
            pass
        for prop in ("article:published_time", "article:modified_time"):
            try:
                metadata[prop] = page.eval_on_selector(
                    f'meta[property="{prop}"]', "el => el.content"
                )
            except Exception:
                pass
        return metadata

    def _extract_links(self, page: Page, base_url: str) -> list[dict]:
        try:
            links = page.eval_on_selector_all(
                "a[href]",
                "elements => elements.map(el => ({ href: el.href, text: el.textContent.trim().slice(0, 200), title: el.title || '' }))",
            )
            return [l for l in links if l["href"].startswith("http")]
        except Exception:
            return []

    def fetch_page(self, url: str) -> PageContent:
        start = time.perf_counter()
        if not PLAYWRIGHT_AVAILABLE:
            return PageContent(url=url, title="", text="", html="", error="Playwright not installed")

        with sync_playwright() as p:
            try:
                page = self._create_page(p)
                response = page.goto(url, wait_until="networkidle")
                status = response.status if response else 0
                title = page.title()
                text = page.inner_text("body")
                html = page.content()
                metadata = self._extract_metadata(page)
                links = self._extract_links(page, url)
                elapsed = (time.perf_counter() - start) * 1000

                return PageContent(
                    url=url,
                    title=title,
                    text=text,
                    html=html,
                    metadata=metadata,
                    links=links,
                    status_code=status,
                    fetch_time_ms=elapsed,
                )
            except Exception as e:
                elapsed = (time.perf_counter() - start) * 1000
                return PageContent(
                    url=url,
                    title="",
                    text="",
                    html="",
                    status_code=0,
                    fetch_time_ms=elapsed,
                    error=str(e),
                )
            finally:
                if self._browser:
                    try:
                        self._browser.close()
                    except Exception:
                        pass
                    self._browser = None

    def extract_content(self, url: str) -> str:
        result = self.fetch_page(url)
        if result.error:
            logger.warning("Failed to fetch %s: %s", url, result.error)
            return ""
        return result.text

    def extract_links(self, url: str) -> list[dict]:
        result = self.fetch_page(url)
        return result.links

    def screenshot(self, url: str, output_path: str = "screenshot.png") -> Optional[str]:
        if not PLAYWRIGHT_AVAILABLE:
            logger.warning("Playwright not available for screenshot")
            return None
        with sync_playwright() as p:
            try:
                page = self._create_page(p)
                page.goto(url, wait_until="networkidle")
                page.screenshot(path=output_path, full_page=True)
                return output_path
            except Exception as e:
                logger.error("Screenshot failed: %s", e)
                return None
            finally:
                if self._browser:
                    try:
                        self._browser.close()
                    except Exception:
                        pass
                    self._browser = None

    def pdf_download(self, url: str, output_path: str = "page.pdf") -> Optional[str]:
        if not PLAYWRIGHT_AVAILABLE:
            logger.warning("Playwright not available for PDF download")
            return None
        with sync_playwright() as p:
            try:
                page = self._create_page(p)
                page.goto(url, wait_until="networkidle")
                page.pdf(path=output_path, format="A4")
                return output_path
            except Exception as e:
                logger.error("PDF download failed: %s", e)
                return None
            finally:
                if self._browser:
                    try:
                        self._browser.close()
                    except Exception:
                        pass
                    self._browser = None
