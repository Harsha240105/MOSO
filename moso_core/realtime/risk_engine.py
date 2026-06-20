from __future__ import annotations

import logging
import time
from typing import Optional
from urllib.parse import urlparse

from moso_core.risk.models import RiskAssessment, RiskLevel
from moso_core.risk.network_analysis import NetworkAnalysis
from moso_core.realtime.reputation import TRACKING_DOMAINS, WebReputationChecker

logger = logging.getLogger(__name__)


class WebRiskEngine:
    def __init__(self):
        self._network = NetworkAnalysis()
        self._reputation = WebReputationChecker()

    def assess_url(self, url: str) -> RiskAssessment:
        factors: list[str] = []
        score = 0.0

        dest_score, dest_factors = self._assess_destination(url)
        score += dest_score
        factors.extend(dest_factors)

        tls_score, tls_factors = self._assess_tls(url)
        score += tls_score
        factors.extend(tls_factors)

        redirect_score, redirect_factors = self._assess_redirect_risk(url)
        score += redirect_score
        factors.extend(redirect_factors)

        phishing_score, phishing_factors = self._assess_phishing_risk(url)
        score += phishing_score
        factors.extend(phishing_factors)

        tracking_score, tracking_factors = self._assess_tracking_risk(url)
        score += tracking_score
        factors.extend(tracking_factors)

        score = min(score, 1.0)
        level = RiskLevel.LOW
        if score >= 0.8:
            level = RiskLevel.CRITICAL
        elif score >= 0.5:
            level = RiskLevel.HIGH
        elif score >= 0.2:
            level = RiskLevel.MEDIUM

        explanation = self._build_explanation(level, score, factors)
        recommendation = self._build_recommendation(level)

        return RiskAssessment(
            level=level,
            score=score,
            factors=factors,
            explanation=explanation,
            recommendation=recommendation,
        )

    def _assess_destination(self, url: str) -> tuple[float, list[str]]:
        factors: list[str] = []
        analysis = self._network.analyze_destination(url)
        rep_score = analysis.get("reputation_score", 0.0)
        if rep_score >= 0.7:
            factors.append(f"destination reputation risk: {analysis.get('reputation_reason', 'unknown')}")
            return 0.4, factors
        elif rep_score >= 0.3:
            factors.append(f"moderate reputation risk: {analysis.get('reputation_reason', 'unknown')}")
            return 0.2, factors
        return 0.0, []

    def _assess_tls(self, url: str) -> tuple[float, list[str]]:
        factors: list[str] = []
        try:
            parsed = urlparse(url)
            if parsed.scheme == "https":
                return 0.0, []
            if parsed.scheme == "http":
                factors.append("connection uses HTTP, not HTTPS")
                return 0.3, factors
            factors.append(f"unknown URL scheme: {parsed.scheme}")
            return 0.1, factors
        except Exception:
            factors.append("could not parse URL scheme")
            return 0.1, factors

    def _assess_redirect_risk(self, url: str) -> tuple[float, list[str]]:
        factors: list[str] = []
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname or ""
            if not hostname:
                return 0.0, []
            if hostname.count(".") > 3:
                factors.append("unusual number of subdomains (potential redirect chain)")
                return 0.15, factors
            if "//" in parsed.path:
                factors.append("URL path contains potential open redirect pattern")
                return 0.2, factors
        except Exception:
            pass
        return 0.0, []

    def _assess_phishing_risk(self, url: str) -> tuple[float, list[str]]:
        factors: list[str] = []
        rep_score, rep_reason = self._reputation.check_url(url)
        if rep_score >= 0.5:
            factors.append(f"phishing indicator: {rep_reason}")
            return 0.5, factors
        return 0.0, []

    def _assess_tracking_risk(self, url: str) -> tuple[float, list[str]]:
        factors: list[str] = []
        try:
            parsed = urlparse(url)
            hostname = parsed.hostname or ""
            for td in TRACKING_DOMAINS:
                if td in hostname:
                    factors.append(f"known tracking/analytics domain")
                    return 0.2, factors
        except Exception:
            pass
        return 0.0, []

    def _build_explanation(self, level: RiskLevel, score: float, factors: list[str]) -> str:
        if not factors:
            return "No web risk factors detected. Source appears safe."
        prefix = {
            RiskLevel.LOW: "Low risk.",
            RiskLevel.MEDIUM: "Medium risk identified.",
            RiskLevel.HIGH: "High risk! Proceed with caution.",
            RiskLevel.CRITICAL: "CRITICAL risk! Source is blocked.",
        }.get(level, "Web risk assessment completed.")
        return f"{prefix} Score: {score:.2f}. Factors: {'; '.join(factors)}"

    def _build_recommendation(self, level: RiskLevel) -> str:
        if level == RiskLevel.LOW:
            return "Source appears safe to access."
        if level == RiskLevel.MEDIUM:
            return "Review risk factors before accessing. Consider using verified sources instead."
        if level == RiskLevel.HIGH:
            return "Strongly consider alternatives. This source may be unsafe."
        if level == RiskLevel.CRITICAL:
            return "Source blocked. This URL is too risky to access."
        return ""
