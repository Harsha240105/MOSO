from __future__ import annotations

import logging
import re
from typing import Optional
from urllib.parse import urlparse

from moso_core.risk.reputation import ReputationChecker

logger = logging.getLogger(__name__)

LOOKALIKE_PATTERNS: list[tuple[str, str]] = [
    (r"g00gle", "google"),
    (r"go0gle", "google"),
    (r"goggle", "google"),
    (r"googie", "google"),
    (r"rnicrosoft", "microsoft"),
    (r"mlcrosost", "microsoft"),
    (r"mlcrosoft", "microsoft"),
    (r"mlcosoft", "microsoft"),
    (r"appIe", "apple"),
    (r"app1e", "apple"),
    (r"appa", "apple"),
    (r"faceb00k", "facebook"),
    (r"facebo0k", "facebook"),
    (r"facebok", "facebook"),
    (r"facebock", "facebook"),
    (r"tw1tter", "twitter"),
    (r"twltter", "twitter"),
    (r"tvvitter", "twitter"),
    (r"y0utube", "youtube"),
    (r"youtub3", "youtube"),
    (r"youtobe", "youtube"),
    (r"githab", "github"),
    (r"githob", "github"),
    (r"githud", "github"),
    (r"paypaI", "paypal"),
    (r"paypa1", "paypal"),
    (r"paypai", "paypal"),
]

PHISHING_PATH_PATTERNS: list[str] = [
    r"login",
    r"signin",
    r"verify",
    r"secure",
    r"account",
    r"update.*account",
    r"password.*reset",
    r"confirm.*identity",
    r"wallet",
    r"seed.*phrase",
    r"private.*key",
    r"2fa",
    r"two.?factor",
    r"auth",
    r"authenticate",
]

TRACKING_DOMAINS: frozenset[str] = frozenset({
    "doubleclick.net",
    "googlesyndication.com",
    "googleadservices.com",
    "google-analytics.com",
    "googletagmanager.com",
    "connect.facebook.net",
    "analytics.twitter.com",
    "ads.linkedin.com",
    "bat.bing.com",
    "pixel.quantserve.com",
    "scorecardresearch.com",
    "criteo.com",
    "criteo.net",
    "casalemedia.com",
    "rubiconproject.com",
    "pubmatic.com",
    "openx.net",
    "appnexus.com",
    "adsrvr.org",
    "adnxs.com",
    "moatads.com",
    "outbrain.com",
    "taboola.com",
    "hotjar.com",
    "mouseflow.com",
    "crazyegg.com",
    "fullstory.com",
    "heap.io",
    "mixpanel.com",
    "amplitude.com",
    "segment.io",
    "segment.com",
})

SUSPICIOUS_URL_PATTERNS: list[re.Pattern] = [
    re.compile(r"https?://\d+\.\d+\.\d+\.\d+/.+"),
    re.compile(r"https?://[^/]*@[^/]+"),
    re.compile(r"https?://[^/]+\.\w+\.(?:xyz|top|club|gq|ml|cf|tk|work|date|men|loan|win|bid|trade|webcam|download)\b"),
    re.compile(r"https?://[^/]*-\w+\.\w+\.\w+"),
]


class WebReputationChecker:
    def __init__(self):
        self._base_checker = ReputationChecker()

    def check_url(self, url: str) -> tuple[float, str]:
        score = 0.0
        reasons: list[str] = []

        try:
            parsed = urlparse(url)
            hostname = parsed.hostname or ""
        except Exception:
            return 0.5, "could not parse URL"

        base_score, base_reason = self._base_checker.check_domain(hostname)
        if base_score > score:
            reasons.append(base_reason)
        score = max(score, base_score)

        lookalike_score, lookalike_reason = self._check_lookalike(hostname)
        if lookalike_score > 0:
            score += lookalike_score
            reasons.append(lookalike_reason)

        path_score, path_reason = self._check_phishing_path(parsed.path)
        if path_score > 0:
            score += path_score
            reasons.append(path_reason)

        url_pattern_score, url_pattern_reason = self._check_url_patterns(url)
        if url_pattern_score > 0:
            score += url_pattern_score
            reasons.append(url_pattern_reason)

        tracking_score, tracking_reason = self._check_tracking_domain(hostname)
        if tracking_score > 0:
            score += tracking_score
            reasons.append(tracking_reason)

        score = min(score, 1.0)

        combined_reason = "; ".join(reasons) if reasons else "no risk signals detected"
        return score, combined_reason

    def _check_lookalike(self, hostname: str) -> tuple[float, str]:
        for pattern, brand in LOOKALIKE_PATTERNS:
            if re.search(pattern, hostname, re.IGNORECASE):
                return 0.6, f"lookalike domain targeting '{brand}'"
        return 0.0, ""

    def _check_phishing_path(self, path: str) -> tuple[float, str]:
        for pattern in PHISHING_PATH_PATTERNS:
            if re.search(pattern, path, re.IGNORECASE):
                return 0.4, f"suspicious path pattern: '{pattern}'"
        return 0.0, ""

    def _check_url_patterns(self, url: str) -> tuple[float, str]:
        for pattern in SUSPICIOUS_URL_PATTERNS:
            if pattern.search(url):
                return 0.3, f"suspicious URL pattern: {pattern.pattern[:40]}"
        return 0.0, ""

    def _check_tracking_domain(self, hostname: str) -> tuple[float, str]:
        for td in TRACKING_DOMAINS:
            if td in hostname:
                return 0.2, f"known tracking domain: {td}"
        return 0.0, ""

    def estimate_risk_level(self, score: float) -> str:
        if score >= 0.8:
            return "critical"
        elif score >= 0.5:
            return "high"
        elif score >= 0.2:
            return "medium"
        return "low"
