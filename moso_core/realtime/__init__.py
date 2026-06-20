from moso_core.realtime.manager import RealtimeManager
from moso_core.realtime.models import (
    AnalysisResult,
    FetchResult,
    RealtimeResponse,
    ResearchReport,
    SourceCategory,
    SourceInfo,
    SourceTier,
    SourceVerification,
)

try:
    from moso_core.realtime.cache import ResponseCache
    from moso_core.realtime.fetcher import Fetcher
    from moso_core.realtime.knowledge_graph import KnowledgeGraph
    from moso_core.realtime.research_browser import ResearchBrowser
    from moso_core.realtime.sources import (
        PREDEFINED_SOURCES,
        SourceDefinition,
        detect_category,
        filter_sources_by_tier,
        get_sources_for_query,
        tier_name,
    )
    from moso_core.realtime.risk_engine import WebRiskEngine
    from moso_core.realtime.privacy_check import WebPrivacyChecker
    from moso_core.realtime.reputation import WebReputationChecker
    from moso_core.realtime.verifier import SourceVerifier
    from moso_core.realtime.analyzer import Analyzer
    from moso_core.realtime.summarizer import Summarizer

    REALTIME_AVAILABLE = True
except ImportError:
    ResponseCache = None  # noqa: F811
    Fetcher = None  # noqa: F811
    KnowledgeGraph = None  # noqa: F811
    ResearchBrowser = None  # noqa: F811
    SourceDefinition = None  # noqa: F811
    WebRiskEngine = None  # noqa: F811
    WebPrivacyChecker = None  # noqa: F811
    WebReputationChecker = None  # noqa: F811
    SourceVerifier = None  # noqa: F811
    Analyzer = None  # noqa: F811
    Summarizer = None  # noqa: F811
    PREDEFINED_SOURCES = []  # noqa: F811
    detect_category = None  # noqa: F811
    filter_sources_by_tier = None  # noqa: F811
    get_sources_for_query = None  # noqa: F811
    tier_name = None  # noqa: F811
    REALTIME_AVAILABLE = False

RESEARCH_BROWSER_AVAILABLE = False
try:
    import playwright  # noqa: F401
    if ResearchBrowser is not None:
        RESEARCH_BROWSER_AVAILABLE = True
except ImportError:
    pass

__all__ = [
    "RealtimeManager",
    "RealtimeResponse",
    "ResearchReport",
    "AnalysisResult",
    "FetchResult",
    "SourceInfo",
    "SourceCategory",
    "SourceTier",
    "SourceVerification",
    "KnowledgeGraph",
    "ResearchBrowser",
    "ResponseCache",
    "Fetcher",
    "SourceDefinition",
    "PREDEFINED_SOURCES",
    "WebRiskEngine",
    "WebPrivacyChecker",
    "WebReputationChecker",
    "SourceVerifier",
    "Analyzer",
    "Summarizer",
    "detect_category",
    "filter_sources_by_tier",
    "get_sources_for_query",
    "tier_name",
    "REALTIME_AVAILABLE",
    "RESEARCH_BROWSER_AVAILABLE",
]
