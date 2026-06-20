from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Optional, Callable

from moso_core.realtime.analyzer import Analyzer
from moso_core.realtime.cache import ResponseCache
from moso_core.realtime.fetcher import Fetcher
from moso_core.realtime.models import (
    AnalysisResult,
    FetchResult,
    RealtimeResponse,
    SourceCategory,
    SourceVerification,
)
from moso_core.realtime.privacy_check import WebPrivacyChecker
from moso_core.realtime.risk_engine import WebRiskEngine
from moso_core.realtime.sources import SourceDefinition, detect_category, get_sources_for_query
from moso_core.realtime.summarizer import Summarizer
from moso_core.realtime.verifier import SourceVerifier

logger = logging.getLogger(__name__)


class AuraCallback:
    def __init__(self):
        self.on_risk_checking: Optional[Callable] = None
        self.on_privacy_checking: Optional[Callable] = None
        self.on_fetching: Optional[Callable] = None
        self.on_verifying: Optional[Callable] = None
        self.on_analyzing: Optional[Callable] = None
        self.on_explaining: Optional[Callable] = None

    def risk_checking(self):
        if self.on_risk_checking:
            self.on_risk_checking()

    def privacy_checking(self):
        if self.on_privacy_checking:
            self.on_privacy_checking()

    def fetching(self):
        if self.on_fetching:
            self.on_fetching()

    def verifying(self):
        if self.on_verifying:
            self.on_verifying()

    def analyzing(self):
        if self.on_analyzing:
            self.on_analyzing()

    def explaining(self):
        if self.on_explaining:
            self.on_explaining()


class RealtimeManager:
    def __init__(
        self,
        memory: Optional[object] = None,
        llm: Optional[object] = None,
        identity: Optional[object] = None,
        aura: Optional[AuraCallback] = None,
        cache: Optional[ResponseCache] = None,
    ):
        self._memory = memory
        self._llm = llm
        self._identity = identity
        self._aura = aura or AuraCallback()
        self._cache = cache or ResponseCache()

        self._risk_engine = WebRiskEngine()
        self._privacy_checker = WebPrivacyChecker()
        self._fetcher = Fetcher()
        self._verifier = SourceVerifier()
        self._analyzer = Analyzer(llm_manager=llm)
        self._summarizer = Summarizer()

        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def _get_or_create_loop(self) -> asyncio.AbstractEventLoop:
        try:
            loop = asyncio.get_event_loop()
            if loop.is_closed():
                raise RuntimeError("closed")
            return loop
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop

    def research(self, query: str, max_sources: int = 3) -> RealtimeResponse:
        response = RealtimeResponse(query=query)
        overall_start = time.time()

        try:
            category = self._identify_need(query, response)
            sources = get_sources_for_query(query, max_sources=max_sources)
            response.sources = [s.to_source_info() for s in sources]

            self._aura.risk_checking()
            self._run_risk_check(sources, response)

            self._aura.privacy_checking()
            self._run_privacy_check(sources, response)

            self._aura.fetching()
            results = self._run_fetch(sources, category, response)

            self._aura.verifying()
            self._run_verification(results, category, response)

            self._aura.analyzing()
            self._run_analysis(query, results, category, response)

            self._aura.explaining()
            self._run_summarization(response)

            self._store_knowledge(query, response, category)

            elapsed = time.time() - overall_start
            logger.info(
                "Research completed in %.1fs: '%s' (%d sources, risk=%s)",
                elapsed, query[:60], len(results), response.risk.level.value,
            )

        except Exception as e:
            logger.error("Research pipeline failed: %s", e, exc_info=True)
            response.analysis = AnalysisResult(
                what_happened=f"Research pipeline encountered an error",
                why_it_matters="Unable to complete the research process",
                key_findings=[f"Error: {str(e)[:200]}"],
                recommendation="Please try again or check connectivity and configuration.",
            )

        return response

    def _identify_need(self, query: str, response: RealtimeResponse) -> SourceCategory:
        category = detect_category(query)
        logger.info("Identified information need: '%s' -> %s", query[:60], category.value)
        return category

    def _run_risk_check(
        self,
        sources: list[SourceDefinition],
        response: RealtimeResponse,
    ):
        max_risk = None
        for src in sources:
            assessment = self._risk_engine.assess_url(src.url)
            if max_risk is None or assessment.score > max_risk.score:
                max_risk = assessment

        risk = max_risk or self._risk_engine.assess_url("")
        response.risk = risk
        logger.info("Risk check: level=%s score=%.2f", risk.level.value, risk.score)

    def _run_privacy_check(
        self,
        sources: list[SourceDefinition],
        response: RealtimeResponse,
    ):
        max_privacy = None
        for src in sources:
            assessment = self._privacy_checker.check_url(src.url)
            if max_privacy is None:
                max_privacy = assessment

        privacy = max_privacy or self._privacy_checker.check_url("")
        response.privacy = privacy
        logger.info("Privacy check: exposure=%s network=%s", privacy.data_exposure, privacy.network_exposure)

    def _run_fetch(
        self,
        sources: list[SourceDefinition],
        category: SourceCategory,
        response: RealtimeResponse,
    ) -> list[FetchResult]:
        loop = self._get_or_create_loop()
        results = loop.run_until_complete(
            self._fetcher.fetch_by_source(
                sources,
                use_cache=True,
                cache=self._cache,
            )
        )
        response.fetch_results = results
        logger.info("Fetched %d/%d sources", len([r for r in results if r.success]), len(results))
        return results

    def _run_verification(
        self,
        results: list[FetchResult],
        category: SourceCategory,
        response: RealtimeResponse,
    ):
        verified_list: list[tuple[FetchResult, SourceVerification]] = []
        for result in results:
            src_info = next(
                (s for s in response.sources if s.url == result.url),
                None,
            )
            base_score = src_info.reliability_score if src_info else 0.5
            verification = self._verifier.verify(
                result,
                category=category,
                reliability_score=base_score,
            )
            response.verifications[result.url] = verification
            verified_list.append((result, verification))

        conflicts = self._verifier.detect_conflicts(verified_list)
        for conflict in conflicts:
            logger.warning("Content conflict detected: %s", conflict)

        reliability = self._verifier.resolve_reliability_label(results)
        logger.info(
            "Verification: %d/%d verified, conflicts=%d, reliability=%s",
            sum(1 for v in response.verifications.values() if v.is_verified),
            len(results), len(conflicts), reliability,
        )

    def _run_analysis(
        self,
        query: str,
        results: list[FetchResult],
        category: SourceCategory,
        response: RealtimeResponse,
    ):
        analysis = self._analyzer.analyze(
            query, results, response.verifications, category
        )
        response.analysis = analysis
        logger.info("Analysis complete: method=%s confidence=%.2f", analysis.analysis_method, analysis.confidence)

    def _run_summarization(self, response: RealtimeResponse):
        summary = self._summarizer.generate_summary(response)
        response.summary = summary
        logger.info("Summary generated (%d chars)", len(summary))

    def _store_knowledge(
        self,
        query: str,
        response: RealtimeResponse,
        category: SourceCategory,
    ):
        if self._memory is None:
            return
        try:
            findings_text = "; ".join(response.analysis.key_findings[:3])
            self._memory.store_event(
                title=f"Research: {query[:80]}",
                description=(
                    f"Real-time research on '{query}'. "
                    f"Risk: {response.risk.level.value}. "
                    f"Findings: {findings_text[:300]}"
                ),
                tags=["realtime", category.value, response.risk.level.value],
                owner_id="default",
            )

            for finding in response.analysis.key_findings[:2]:
                if len(finding) > 20:
                    self._memory.store_fact(
                        fact=finding[:300],
                        confidence=response.analysis.confidence * 0.8,
                        category=category.value,
                        owner_id="default",
                        source="realtime",
                    )

            logger.info("Stored %d finding(s) in memory", len(response.analysis.key_findings[:2]))
        except Exception as e:
            logger.warning("Failed to store knowledge in memory: %s", e)

    def research_summary(self, query: str) -> str:
        response = self.research(query)
        return response.formatted_report

    @property
    def aura_callbacks(self) -> AuraCallback:
        return self._aura

    @property
    def cache(self) -> ResponseCache:
        return self._cache

    def close(self):
        try:
            loop = self._get_or_create_loop()
            if not loop.is_closed():
                loop.run_until_complete(self._fetcher.close())
        except Exception as e:
            logger.warning("Error closing fetcher: %s", e)
        self._cache.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
