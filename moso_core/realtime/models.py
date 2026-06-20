from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, IntEnum
from typing import Any, Optional

from moso_core.risk.models import PrivacyAssessment, RiskAssessment, RiskLevel


class SourceTier(IntEnum):
    TIER_1_PRIMARY = 1
    TIER_2_SECONDARY = 2
    TIER_3_TERTIARY = 3
    TIER_4_AGGREGATOR = 4
    TIER_5_COMMUNITY = 5


class SourceCategory(str, Enum):
    NEWS = "news"
    AI = "ai"
    SECURITY = "security"
    MARKET = "market"
    CRYPTO = "crypto"
    OSS = "open_source"
    SOFTWARE = "software"
    HARDWARE = "hardware"
    DOCS = "documentation"
    GENERAL = "general"


@dataclass
class SourceInfo:
    name: str
    url: str
    category: SourceCategory = SourceCategory.GENERAL
    reliability_score: float = 0.5
    last_checked: Optional[str] = None
    error_count: int = 0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "url": self.url,
            "category": self.category.value,
            "reliability_score": self.reliability_score,
            "last_checked": self.last_checked,
            "error_count": self.error_count,
        }


@dataclass
class FetchResult:
    url: str
    source_name: str
    raw_text: str
    parsed_text: str
    status_code: int = 200
    timestamp: str = ""
    error: Optional[str] = None
    content_type: str = "text/plain"
    redirect_chain: list[str] = field(default_factory=list)
    tls_verified: bool = False

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

    @property
    def success(self) -> bool:
        return self.error is None and self.status_code < 400

    def to_dict(self) -> dict:
        return {
            "url": self.url,
            "source_name": self.source_name,
            "status_code": self.status_code,
            "timestamp": self.timestamp,
            "error": self.error,
            "content_type": self.content_type,
            "success": self.success,
        }


@dataclass
class SourceVerification:
    is_verified: bool = False
    publication_date: Optional[str] = None
    is_stale: bool = False
    is_duplicate: bool = False
    duplicate_of: Optional[str] = None
    conflicts: list[str] = field(default_factory=list)
    reliability_rank: int = 0
    reliability_label: str = "unknown"
    verification_notes: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "is_verified": self.is_verified,
            "publication_date": self.publication_date,
            "is_stale": self.is_stale,
            "is_duplicate": self.is_duplicate,
            "duplicate_of": self.duplicate_of,
            "conflicts": self.conflicts,
            "reliability_rank": self.reliability_rank,
            "reliability_label": self.reliability_label,
            "verification_notes": self.verification_notes,
        }


@dataclass
class AnalysisResult:
    what_happened: str = ""
    why_it_matters: str = ""
    what_changed: str = ""
    implications: str = ""
    key_findings: list[str] = field(default_factory=list)
    recommendation: str = ""
    confidence: float = 0.5
    analysis_method: str = "rule-based"

    def to_dict(self) -> dict:
        return {
            "what_happened": self.what_happened,
            "why_it_matters": self.why_it_matters,
            "what_changed": self.what_changed,
            "implications": self.implications,
            "key_findings": self.key_findings,
            "recommendation": self.recommendation,
            "confidence": self.confidence,
            "analysis_method": self.analysis_method,
        }


@dataclass
class RealtimeResponse:
    query: str
    risk: RiskAssessment = field(default_factory=RiskAssessment)
    privacy: PrivacyAssessment = field(default_factory=PrivacyAssessment)
    sources: list[SourceInfo] = field(default_factory=list)
    fetch_results: list[FetchResult] = field(default_factory=list)
    verifications: dict[str, SourceVerification] = field(default_factory=dict)
    analysis: AnalysisResult = field(default_factory=AnalysisResult)
    summary: str = ""
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

    @property
    def formatted_report(self) -> str:
        lines = []
        lines.append("RISK REPORT")
        lines.append(f"Level: {self.risk.level.value.upper()}")
        lines.append(self.risk.explanation)
        lines.append("")

        lines.append("SOURCE SUMMARY")
        for src in self.sources:
            v = self.verifications.get(src.url)
            rank = v.reliability_label if v else "unknown"
            lines.append(f"  - {src.name} ({src.category.value}, reliability: {rank})")
        lines.append("")

        lines.append("KEY FINDINGS")
        for finding in self.analysis.key_findings:
            lines.append(f"  - {finding}")
        lines.append("")

        lines.append("ANALYSIS")
        lines.append(f"What happened: {self.analysis.what_happened}")
        lines.append(f"Why it matters: {self.analysis.why_it_matters}")
        if self.analysis.what_changed:
            lines.append(f"What changed: {self.analysis.what_changed}")
        if self.analysis.implications:
            lines.append(f"Implications: {self.analysis.implications}")
        lines.append("")

        lines.append("RECOMMENDATION")
        lines.append(self.analysis.recommendation)

        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "risk": self.risk.to_dict(),
            "privacy": self.privacy.to_dict(),
            "sources": [s.to_dict() for s in self.sources],
            "fetch_results": [r.to_dict() for r in self.fetch_results],
            "verifications": {k: v.to_dict() for k, v in self.verifications.items()},
            "analysis": self.analysis.to_dict(),
            "summary": self.summary,
            "timestamp": self.timestamp,
        }


@dataclass
class ResearchReport:
    query: str
    research_goal: str = ""
    executive_summary: str = ""
    key_findings: list[str] = field(default_factory=list)
    evidence: list[dict] = field(default_factory=list)
    sources_consulted: list[SourceInfo] = field(default_factory=list)
    methodology: str = ""
    limitations: list[str] = field(default_factory=list)
    confidence_score: float = 0.0
    gaps_identified: list[str] = field(default_factory=list)
    contradictions: list[dict] = field(default_factory=list)
    timeline: list[dict] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    transparency_log: list[dict] = field(default_factory=list)
    related_queries: list[str] = field(default_factory=list)
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.utcnow().isoformat()

    def to_dict(self) -> dict:
        return {
            "query": self.query,
            "research_goal": self.research_goal,
            "executive_summary": self.executive_summary,
            "key_findings": self.key_findings,
            "evidence": self.evidence,
            "sources_consulted": [s.to_dict() for s in self.sources_consulted],
            "methodology": self.methodology,
            "limitations": self.limitations,
            "confidence_score": self.confidence_score,
            "gaps_identified": self.gaps_identified,
            "contradictions": self.contradictions,
            "timeline": self.timeline,
            "recommendations": self.recommendations,
            "transparency_log": self.transparency_log,
            "related_queries": self.related_queries,
            "timestamp": self.timestamp,
        }
