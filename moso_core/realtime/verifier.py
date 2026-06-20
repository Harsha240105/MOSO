from __future__ import annotations

import logging
import re
import time
from datetime import datetime
from typing import Optional

from moso_core.realtime.models import FetchResult, SourceCategory, SourceVerification

logger = logging.getLogger(__name__)

RELIABILITY_LABELS: dict[int, str] = {
    5: "very high",
    4: "high",
    3: "moderate",
    2: "low",
    1: "very low",
    0: "unknown",
}

DATE_PATTERNS: list[re.Pattern] = [
    re.compile(r"(20\d{2})[-/](0[1-9]|1[0-2])[-/](0[1-9]|[12]\d|3[01])"),
    re.compile(r"(0[1-9]|[12]\d|3[01])[-/](0[1-9]|1[0-2])[-/](20\d{2})"),
    re.compile(r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+20\d{2}"),
    re.compile(r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+20\d{2}"),
    re.compile(r"20\d{2}[-/](0[1-9]|1[0-2])[-/](0[1-9]|[12]\d|3[01])"),
]

STALENESS_DAYS: dict[SourceCategory, int] = {
    SourceCategory.NEWS: 7,
    SourceCategory.AI: 30,
    SourceCategory.SECURITY: 14,
    SourceCategory.MARKET: 1,
    SourceCategory.CRYPTO: 1,
    SourceCategory.OSS: 60,
    SourceCategory.SOFTWARE: 90,
    SourceCategory.HARDWARE: 180,
    SourceCategory.DOCS: 365,
    SourceCategory.GENERAL: 90,
}


class SourceVerifier:
    def __init__(self):
        self._seen_content_hashes: set[int] = set()

    def verify(
        self,
        result: FetchResult,
        category: SourceCategory = SourceCategory.GENERAL,
        reliability_score: float = 0.5,
    ) -> SourceVerification:
        verification = SourceVerification()

        pub_date = self._extract_publication_date(result.parsed_text)
        if pub_date:
            verification.publication_date = pub_date
            verification.is_stale = self._check_staleness(pub_date, category)

        content_hash = hash(result.parsed_text[:1000])
        if content_hash in self._seen_content_hashes:
            verification.is_duplicate = True
            verification.duplicate_of = f"similar content previously fetched"
        else:
            self._seen_content_hashes.add(content_hash)

        verification.reliability_rank = self._compute_reliability_rank(
            reliability_score, result.success, result.status_code
        )
        verification.reliability_label = RELIABILITY_LABELS.get(
            verification.reliability_rank, "unknown"
        )

        verification.is_verified = (
            result.success
            and not verification.is_stale
            and verification.reliability_rank >= 2
        )

        if result.error:
            verification.verification_notes.append(f"fetch error: {result.error}")
        if verification.is_stale:
            verification.verification_notes.append("content may be outdated")
        if verification.is_duplicate:
            verification.verification_notes.append("duplicate content detected")
        if not verification.is_verified:
            verification.verification_notes.append("source does not meet reliability threshold")

        return verification

    def _extract_publication_date(self, text: str) -> Optional[str]:
        for pattern in DATE_PATTERNS:
            match = pattern.search(text)
            if match:
                return match.group(0)
        return None

    def _check_staleness(self, date_str: str, category: SourceCategory) -> bool:
        try:
            parsed = None
            for fmt in [
                "%Y-%m-%d", "%Y/%m/%d",
                "%d-%m-%Y", "%d/%m/%Y",
                "%B %d, %Y", "%B %d %Y",
                "%b %d, %Y", "%b %d %Y",
            ]:
                try:
                    parsed = datetime.strptime(date_str[:20], fmt)
                    break
                except ValueError:
                    continue
            if parsed is None:
                return False
            max_days = STALENESS_DAYS.get(category, 90)
            delta = datetime.utcnow() - parsed
            return delta.days > max_days
        except Exception:
            return False

    def _compute_reliability_rank(
        self, base_score: float, success: bool, status_code: int
    ) -> int:
        rank = 2
        if base_score >= 0.8:
            rank = 4
        elif base_score >= 0.6:
            rank = 3
        elif base_score >= 0.4:
            rank = 2
        else:
            rank = 1

        if not success:
            rank -= 1
        if status_code >= 500:
            rank -= 1
        if status_code == 200:
            rank += 0

        return max(0, min(5, rank))

    def detect_conflicts(
        self, results: list[tuple[FetchResult, SourceVerification]]
    ) -> list[str]:
        conflicts: list[str] = []
        if len(results) < 2:
            return conflicts

        verified_results = [
            r for r, v in results if v.is_verified and r.success
        ]
        if len(verified_results) < 2:
            return conflicts

        for i in range(len(verified_results)):
            for j in range(i + 1, len(verified_results)):
                text_i = verified_results[i].parsed_text[:500]
                text_j = verified_results[j].parsed_text[:500]
                if text_i and text_j and len(set(text_i.split()) & set(text_j.split())) < 10:
                    conflicts.append(
                        f"Content divergence between {verified_results[i].source_name} "
                        f"and {verified_results[j].source_name}"
                    )

        return conflicts

    def resolve_reliability_label(self, results: list[FetchResult]) -> str:
        if not results:
            return "unknown"
        scores = []
        for r in results:
            if r.success and r.status_code == 200:
                conf = r.parsed_text.count(" ") / max(len(r.parsed_text), 1)
                if conf > 0.1:
                    scores.append(0.8)
                else:
                    scores.append(0.5)
            else:
                scores.append(0.1)
        avg = sum(scores) / len(scores)
        if avg >= 0.8:
            return "high confidence"
        elif avg >= 0.5:
            return "moderate confidence"
        elif avg >= 0.2:
            return "low confidence"
        return "unreliable"
