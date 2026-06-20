from __future__ import annotations

import logging
import re
import time
from typing import Optional
from urllib.parse import urlparse

from moso_core.risk.models import PrivacyAssessment

logger = logging.getLogger(__name__)

TRACKING_PARAMETERS: list[str] = [
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "fbclid", "gclid", "gbraid", "wbraid",
    "msclkid", "twclid", "sc_campaign", "sc_channel",
    "ref", "source", "referrer",
]

TRACKER_PATTERNS: list[re.Pattern] = [
    re.compile(r"https?://[^/]*doubleclick\.net/"),
    re.compile(r"https?://[^/]*googlesyndication\.com/"),
    re.compile(r"https?://[^/]*google-analytics\.com/"),
    re.compile(r"https?://[^/]*googletagmanager\.com/"),
    re.compile(r"https?://[^/]*facebook\.com/tr"),
    re.compile(r"https?://[^/]*connect\.facebook\.net/"),
    re.compile(r"https?://[^/]*analytics\.twitter\.com/"),
    re.compile(r"https?://[^/]*bat\.bing\.com/"),
    re.compile(r"https?://[^/]*hotjar\.com/"),
    re.compile(r"https?://[^/]*fullstory\.com/"),
    re.compile(r"https?://[^/]*mixpanel\.com/"),
    re.compile(r"https?://[^/]*amplitude\.com/"),
    re.compile(r"https?://[^/]*segment\.(io|com)/"),
]


class WebPrivacyChecker:
    def __init__(self):
        self._checked_urls: dict[str, float] = {}

    def check_url(self, url: str) -> PrivacyAssessment:
        data_exposure = "none"
        credential_exposure = False
        network_exposure = "none"
        user_data_accessed = False
        system_files_affected = False
        writes_externally = False
        warnings: list[str] = []

        try:
            parsed = urlparse(url)
            hostname = parsed.hostname or ""
            scheme = parsed.scheme or ""
            path = parsed.path or ""
        except Exception as e:
            return PrivacyAssessment(
                data_exposure="none",
                network_exposure="none",
                recommendation=f"Could not parse URL: {e}",
            )

        conn_risk, conn_warning = self._check_connection_security(scheme, hostname)
        if conn_risk:
            warnings.append(conn_warning)

        cert_risk, cert_warning = self._check_certificate_indicators(hostname)
        if cert_risk:
            warnings.append(cert_warning)

        tracking_risk, tracking_warning = self._check_tracking_indicators(url)
        if tracking_risk:
            warnings.append(tracking_warning)
            network_exposure = "tracking present"

        data_risk, data_warning = self._check_data_exposure(path)
        if data_risk:
            warnings.append(data_warning)
            data_exposure = "potential data submission"

        has_tracking_params = self._check_tracking_parameters(parsed.query)
        if has_tracking_params:
            warnings.append("URL contains tracking parameters")
            if network_exposure == "none":
                network_exposure = "tracking parameters present"

        if scheme == "http":
            writes_externally = True

        recommendation = self._build_recommendation(warnings)

        self._checked_urls[url] = time.time()

        return PrivacyAssessment(
            data_exposure=data_exposure,
            credential_exposure=credential_exposure,
            network_exposure=network_exposure,
            user_data_accessed=user_data_accessed,
            system_files_affected=system_files_affected,
            writes_externally=writes_externally,
            recommendation=recommendation,
        )

    def _check_connection_security(self, scheme: str, hostname: str) -> tuple[bool, str]:
        if scheme != "https":
            return True, "Connection is not encrypted (no HTTPS)"
        return False, ""

    def _check_certificate_indicators(self, hostname: str) -> tuple[bool, str]:
        if not hostname:
            return False, ""
        if hostname.endswith(".onion"):
            return True, "Onion service - verify certificate manually"
        ip_pattern = re.compile(r"^\d+\.\d+\.\d+\.\d+$")
        if ip_pattern.match(hostname):
            return True, "Direct IP access - no domain certificate validation"
        return False, ""

    def _check_tracking_indicators(self, url: str) -> tuple[bool, str]:
        for pattern in TRACKER_PATTERNS:
            if pattern.search(url):
                return True, "Tracking or analytics service detected"
        return False, ""

    def _check_data_exposure(self, path: str) -> tuple[bool, str]:
        exposure_patterns = [
            r"/submit", r"/login", r"/signup", r"/register",
            r"/checkout", r"/payment", r"/order",
            r"/contact", r"/feedback",
            r"/api/.*(?:data|user|info)",
        ]
        for pattern in exposure_patterns:
            if re.search(pattern, path, re.IGNORECASE):
                return True, f"Page may collect user data (path: {path[:30]})"
        return False, ""

    def _check_tracking_parameters(self, query: str) -> bool:
        for param in TRACKING_PARAMETERS:
            if param in query.lower():
                return True
        return False

    def _build_recommendation(self, warnings: list[str]) -> str:
        if not warnings:
            return "No privacy concerns detected with this URL."
        return "Privacy warnings: " + "; ".join(warnings) + "."
