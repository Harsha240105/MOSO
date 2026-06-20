from __future__ import annotations

import logging
from typing import Optional

from moso_core.realtime.models import (
    AnalysisResult,
    FetchResult,
    RealtimeResponse,
    SourceVerification,
)

logger = logging.getLogger(__name__)


class Summarizer:
    def __init__(self, memory_summarizer: Optional[object] = None):
        self._memory_summarizer = memory_summarizer

    def generate_summary(
        self,
        response: RealtimeResponse,
        max_sources: int = 3,
    ) -> str:
        parts: list[str] = []

        parts.append(self._summary_line(response))
        parts.append("")

        parts.append(self._key_findings_block(response, max_sources))

        parts.append(self._analysis_block(response))

        parts.append(self._recommendation_block(response))

        return "\n".join(parts).strip()

    def _summary_line(self, response: RealtimeResponse) -> str:
        num_sources = len([r for r in response.fetch_results if r.success])
        risk_level = response.risk.level.value.upper()
        key_finding_count = len(response.analysis.key_findings)
        return (
            f"Real-time report for '{response.query}': "
            f"fetched {num_sources} source(s), "
            f"risk level {risk_level}, "
            f"{key_finding_count} key finding(s)"
        )

    def _key_findings_block(self, response: RealtimeResponse, max_sources: int) -> str:
        lines = ["SOURCE SUMMARY"]
        for r in response.fetch_results[:max_sources]:
            if r.success:
                v = response.verifications.get(r.url)
                label = v.reliability_label if v else "unknown"
                status = f"verified ({label})" if v and v.is_verified else "unverified"
                lines.append(f"  {r.source_name}: {status}")
        if not response.fetch_results:
            lines.append("  No sources fetched.")
        lines.append("")

        lines.append("KEY FINDINGS")
        for finding in response.analysis.key_findings:
            lines.append(f"  - {finding}")
        if not response.analysis.key_findings:
            lines.append("  - No key findings extracted.")
        lines.append("")

        return "\n".join(lines)

    def _analysis_block(self, response: RealtimeResponse) -> str:
        lines = ["ANALYSIS"]

        if response.analysis.what_happened:
            lines.append(f"  What: {response.analysis.what_happened}")
        if response.analysis.why_it_matters:
            lines.append(f"  Why: {response.analysis.why_it_matters}")
        if response.analysis.what_changed:
            lines.append(f"  Change: {response.analysis.what_changed}")
        if response.analysis.implications:
            lines.append(f"  Implication: {response.analysis.implications}")

        lines.append(f"  Confidence: {response.analysis.confidence:.0%}")
        lines.append(f"  Method: {response.analysis.analysis_method}")
        lines.append("")

        return "\n".join(lines)

    def _recommendation_block(self, response: RealtimeResponse) -> str:
        lines = ["RECOMMENDATION"]
        if response.analysis.recommendation:
            lines.append(f"  {response.analysis.recommendation}")
        else:
            lines.append("  Review the analysis above for actionable insights.")
        return "\n".join(lines)

    def generate_short_summary(self, response: RealtimeResponse) -> str:
        findings = response.analysis.key_findings
        if findings:
            top = findings[0][:150]
            return f"[{response.risk.level.value.upper()}] {response.query}: {top}"
        num_sources = len([r for r in response.fetch_results if r.success])
        return f"[{response.risk.level.value.upper()}] {response.query}: {num_sources} source(s) analyzed"
