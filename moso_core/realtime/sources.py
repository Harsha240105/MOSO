from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
from urllib.parse import urlparse

from moso_core.realtime.models import FetchResult, SourceCategory, SourceInfo, SourceTier

logger = logging.getLogger(__name__)


@dataclass
class SourceDefinition:
    name: str
    url: str
    category: SourceCategory
    reliability_score: float = 0.5
    tier: SourceTier = SourceTier.TIER_3_TERTIARY
    fetch_strategy: str = "general"
    language: str = "en"
    topics: list[str] = field(default_factory=list)

    def to_source_info(self) -> SourceInfo:
        return SourceInfo(
            name=self.name,
            url=self.url,
            category=self.category,
            reliability_score=self.reliability_score,
        )


PREDEFINED_SOURCES: list[SourceDefinition] = [
    # Technology News
    SourceDefinition("The Verge", "https://www.theverge.com/tech", SourceCategory.NEWS, 0.75, SourceTier.TIER_3_TERTIARY, topics=["technology", "gadgets", "tech"]),
    SourceDefinition("Ars Technica", "https://arstechnica.com", SourceCategory.NEWS, 0.80, SourceTier.TIER_2_SECONDARY, topics=["technology", "science", "tech"]),
    SourceDefinition("TechCrunch", "https://techcrunch.com", SourceCategory.NEWS, 0.70, SourceTier.TIER_3_TERTIARY, topics=["startups", "technology", "tech"]),
    SourceDefinition("Wired", "https://www.wired.com", SourceCategory.NEWS, 0.75, SourceTier.TIER_3_TERTIARY, topics=["technology", "culture", "science"]),
    SourceDefinition("Hacker News", "https://news.ycombinator.com", SourceCategory.NEWS, 0.65, SourceTier.TIER_5_COMMUNITY, topics=["technology", "startups", "programming"]),
    SourceDefinition("CNET", "https://www.cnet.com", SourceCategory.NEWS, 0.65, SourceTier.TIER_4_AGGREGATOR, topics=["technology", "reviews", "tech"]),

    # AI Developments
    SourceDefinition("OpenAI Blog", "https://openai.com/blog", SourceCategory.AI, 0.85, SourceTier.TIER_1_PRIMARY, topics=["ai", "openai", "research"]),
    SourceDefinition("DeepMind Blog", "https://deepmind.google/blog", SourceCategory.AI, 0.85, SourceTier.TIER_1_PRIMARY, topics=["ai", "deepmind", "research"]),
    SourceDefinition("Anthropic Blog", "https://anthropic.com/blog", SourceCategory.AI, 0.85, SourceTier.TIER_1_PRIMARY, topics=["ai", "anthropic", "safety"]),
    SourceDefinition("Hugging Face Blog", "https://huggingface.co/blog", SourceCategory.AI, 0.80, SourceTier.TIER_2_SECONDARY, topics=["ai", "huggingface", "ml"]),
    SourceDefinition("Meta AI Blog", "https://ai.meta.com/blog", SourceCategory.AI, 0.75, SourceTier.TIER_1_PRIMARY, topics=["ai", "meta", "research"]),
    SourceDefinition("Google AI Blog", "https://ai.googleblog.com", SourceCategory.AI, 0.80, SourceTier.TIER_1_PRIMARY, topics=["ai", "google", "research"]),

    # Security Advisories
    SourceDefinition("The Hacker News", "https://thehackernews.com", SourceCategory.SECURITY, 0.70, SourceTier.TIER_3_TERTIARY, topics=["security", "cybersecurity", "threats"]),
    SourceDefinition("Krebs on Security", "https://krebsonsecurity.com", SourceCategory.SECURITY, 0.85, SourceTier.TIER_2_SECONDARY, topics=["security", "cybersecurity", "threats"]),
    SourceDefinition("BleepingComputer", "https://www.bleepingcomputer.com", SourceCategory.SECURITY, 0.75, SourceTier.TIER_3_TERTIARY, topics=["security", "malware", "threats"]),
    SourceDefinition("NVD (NIST)", "https://nvd.nist.gov", SourceCategory.SECURITY, 0.90, SourceTier.TIER_1_PRIMARY, topics=["security", "cve", "vulnerabilities"]),

    # Market Data
    SourceDefinition("Bloomberg Technology", "https://www.bloomberg.com/technology", SourceCategory.MARKET, 0.80, SourceTier.TIER_2_SECONDARY, topics=["markets", "finance", "stocks"]),
    SourceDefinition("Reuters Tech", "https://www.reuters.com/technology", SourceCategory.MARKET, 0.80, SourceTier.TIER_2_SECONDARY, topics=["markets", "finance", "stocks"]),

    # Cryptocurrency
    SourceDefinition("CoinDesk", "https://www.coindesk.com", SourceCategory.CRYPTO, 0.65, SourceTier.TIER_3_TERTIARY, topics=["crypto", "bitcoin", "blockchain"]),
    SourceDefinition("CoinTelegraph", "https://cointelegraph.com", SourceCategory.CRYPTO, 0.60, SourceTier.TIER_4_AGGREGATOR, topics=["crypto", "bitcoin", "blockchain"]),

    # Open Source
    SourceDefinition("GitHub Trending", "https://github.com/trending", SourceCategory.OSS, 0.70, SourceTier.TIER_4_AGGREGATOR, topics=["github", "open-source", "coding"]),
    SourceDefinition("GitHub Blog", "https://github.blog", SourceCategory.OSS, 0.85, SourceTier.TIER_1_PRIMARY, topics=["github", "open-source", "development"]),

    # Software Releases
    SourceDefinition("Phoronix", "https://www.phoronix.com", SourceCategory.SOFTWARE, 0.75, SourceTier.TIER_2_SECONDARY, topics=["linux", "open-source", "benchmarks"]),
    SourceDefinition("OSNews", "https://www.osnews.com", SourceCategory.SOFTWARE, 0.65, SourceTier.TIER_4_AGGREGATOR, topics=["operating-systems", "software", "tech"]),

    # Hardware News
    SourceDefinition("AnandTech", "https://www.anandtech.com", SourceCategory.HARDWARE, 0.80, SourceTier.TIER_2_SECONDARY, topics=["hardware", "processors", "benchmarks"]),
    SourceDefinition("Tom's Hardware", "https://www.tomshardware.com", SourceCategory.HARDWARE, 0.70, SourceTier.TIER_3_TERTIARY, topics=["hardware", "components", "reviews"]),

    # Public Documentation
    SourceDefinition("Python Docs", "https://docs.python.org/3", SourceCategory.DOCS, 0.90, SourceTier.TIER_1_PRIMARY, topics=["python", "documentation", "programming"]),
    SourceDefinition("MDN Web Docs", "https://developer.mozilla.org", SourceCategory.DOCS, 0.90, SourceTier.TIER_1_PRIMARY, topics=["web", "javascript", "documentation"]),
    SourceDefinition("Microsoft Learn", "https://learn.microsoft.com", SourceCategory.DOCS, 0.85, SourceTier.TIER_1_PRIMARY, topics=["microsoft", "documentation", "development"]),
]

CATEGORY_SOURCE_MAP: dict[SourceCategory, list[SourceDefinition]] = {}
for src in PREDEFINED_SOURCES:
    CATEGORY_SOURCE_MAP.setdefault(src.category, []).append(src)

CATEGORY_KEYWORDS: dict[SourceCategory, list[str]] = {
    SourceCategory.NEWS: ["news", "headlines", "breaking", "announced", "announcement"],
    SourceCategory.AI: ["ai", "artificial intelligence", "machine learning", "deep learning", "llm", "gpt", "neural", "transformer", "openai", "anthropic", "claude", "gemini", "copilot"],
    SourceCategory.SECURITY: ["security", "cybersecurity", "vulnerability", "cve", "exploit", "malware", "ransomware", "hack", "hacker", "breach", "threat", "patching"],
    SourceCategory.MARKET: ["market", "stock", "finance", "trading", "economy", "nasdaq", "sp500", "investment", "earnings", "ipo"],
    SourceCategory.CRYPTO: ["crypto", "cryptocurrency", "bitcoin", "ethereum", "blockchain", "defi", "nft", "web3", "solana"],
    SourceCategory.OSS: ["open source", "github", "gitlab", "repository", "trending", "project", "pull request", "fork"],
    SourceCategory.SOFTWARE: ["software", "release", "version", "launch", "app", "application", "desktop", "mobile app"],
    SourceCategory.HARDWARE: ["hardware", "cpu", "gpu", "processor", "chip", "nvidia", "amd", "intel", "phone", "smartphone", "laptop"],
    SourceCategory.DOCS: ["documentation", "docs", "reference", "guide", "tutorial", "how to", "how do i", "how can i", "learn", "example", "syntax"],
    SourceCategory.GENERAL: [],
}


def _keyword_match(keyword: str, text: str) -> bool:
    if keyword in text:
        return True
    if keyword.endswith("y") and len(keyword) > 3:
        plural = keyword[:-1] + "ies"
        if plural in text:
            return True
    if keyword.endswith("s") and keyword[:-1] in text:
        return True
    if keyword.endswith("e") and keyword + "s" in text:
        return True
    if keyword.endswith("ed") and keyword[:-1] in text:
        return True
    if keyword.endswith("ing") and keyword[:-3] + "e" in text:
        return True
    return False


def _keyword_score(keyword: str, query_lower: str) -> int:
    if " " in keyword:
        return 3 if keyword in query_lower else 0
    if keyword in query_lower:
        return 2
    if keyword.endswith("y") and len(keyword) > 3:
        if keyword[:-1] + "ies" in query_lower:
            return 2
    if keyword.endswith("s"):
        if keyword[:-1] in query_lower:
            return 2
    if keyword.endswith("e"):
        if keyword + "s" in query_lower or keyword + "d" in query_lower:
            return 2
    if keyword.endswith("ed"):
        if keyword[:-2] in query_lower or keyword[:-1] in query_lower:
            return 2
    if keyword.endswith("ing"):
        base = keyword[:-3]
        if base + "e" in query_lower or base + "ed" in query_lower:
            return 2
    return 0


def detect_category(query: str) -> Optional[SourceCategory]:
    query_lower = query.lower()
    scores: dict[SourceCategory, int] = {}
    for cat, keywords in CATEGORY_KEYWORDS.items():
        if not keywords:
            continue
        score = sum(_keyword_score(kw, query_lower) for kw in keywords)
        if score > 0:
            scores[cat] = score
    if not scores:
        return SourceCategory.GENERAL
    max_score = max(scores.values())
    tied = [c for c, s in scores.items() if s == max_score]
    for cat in (SourceCategory.AI, SourceCategory.SECURITY, SourceCategory.CRYPTO, SourceCategory.MARKET, SourceCategory.DOCS):
        if cat in tied:
            return cat
    return tied[0] if tied else SourceCategory.GENERAL


def get_sources_for_query(query: str, max_sources: int = 3) -> list[SourceDefinition]:
    category = detect_category(query)
    sources = CATEGORY_SOURCE_MAP.get(category, [])
    if not sources:
        sources = CATEGORY_SOURCE_MAP.get(SourceCategory.GENERAL, [])
    sorted_sources = sorted(sources, key=lambda s: s.reliability_score, reverse=True)
    return sorted_sources[:max_sources]


def get_sources_for_url(url: str) -> Optional[SourceDefinition]:
    parsed = urlparse(url)
    domain = parsed.netloc.lower()
    for src in PREDEFINED_SOURCES:
        if domain in src.url:
            return src
    return None


def filter_sources_by_tier(
    sources: list[SourceDefinition],
    min_tier: SourceTier = SourceTier.TIER_3_TERTIARY,
) -> list[SourceDefinition]:
    return [s for s in sources if s.tier <= min_tier]


def tier_name(tier: SourceTier) -> str:
    return {
        SourceTier.TIER_1_PRIMARY: "Primary (official/research)",
        SourceTier.TIER_2_SECONDARY: "Secondary (journalism/analysis)",
        SourceTier.TIER_3_TERTIARY: "Tertiary (news/coverage)",
        SourceTier.TIER_4_AGGREGATOR: "Aggregator (curated/community)",
        SourceTier.TIER_5_COMMUNITY: "Community (user-generated)",
    }.get(tier, "Unknown")
