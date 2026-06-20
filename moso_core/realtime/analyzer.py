from __future__ import annotations

import logging
import re
from typing import Optional

from moso_core.realtime.models import (
    AnalysisResult,
    FetchResult,
    SourceCategory,
    SourceVerification,
)

logger = logging.getLogger(__name__)

AI_KEYWORDS: list[str] = [
    "ai", "artificial intelligence", "machine learning", "deep learning",
    "llm", "gpt", "claude", "gemini", "transformer", "neural network",
    "diffusion", "openai", "anthropic", "google ai", "meta ai",
    "fine-tuning", "rlhf", "rag", "agent", "copilot",
]

SECURITY_KEYWORDS: list[str] = [
    "cve", "vulnerability", "exploit", "malware", "ransomware",
    "zero-day", "patch", "security advisory", "breach", "data leak",
    "attack vector", "backdoor", "trojan", "phishing",
]

MARKET_KEYWORDS: list[str] = [
    "stock", "market", "trading", "ipo", "earnings", "revenue",
    "acquisition", "merger", "investment", "funding", "valuation",
    "billion", "million",
]


class KeywordExtractor:
    def extract_keywords(self, text: str) -> list[str]:
        words = re.findall(r"\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)*\b", text)
        return list(set(w for w in words if len(w) > 3))[:20]

    def extract_numbers(self, text: str) -> list[str]:
        return re.findall(r"\$\d+(?:\.\d+)?[BMK]?", text)

    def extract_dates(self, text: str) -> list[str]:
        date_patterns = [
            r"(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+20\d{2}",
            r"(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2},?\s+20\d{2}",
            r"20\d{2}[-/]\d{2}[-/]\d{2}",
        ]
        results = []
        for pattern in date_patterns:
            results.extend(re.findall(pattern, text))
        return results


class Analyzer:
    def __init__(self, llm_manager: Optional[object] = None):
        self._llm = llm_manager
        self._keyword_extractor = KeywordExtractor()

    def analyze(
        self,
        query: str,
        results: list[FetchResult],
        verifications: dict[str, SourceVerification],
        category: SourceCategory = SourceCategory.GENERAL,
    ) -> AnalysisResult:
        combined_text = "\n\n".join(
            r.parsed_text for r in results if r.success
        )

        if not combined_text.strip():
            return AnalysisResult(
                what_happened="No content could be fetched.",
                why_it_matters="Unable to retrieve information.",
                key_findings=["No data available"],
                recommendation="Try different search terms or check connectivity.",
            )

        if self._llm is not None:
            return self._analyze_with_llm(query, combined_text, category)

        return self._analyze_rule_based(query, combined_text, results, category)

    def _analyze_with_llm(
        self,
        query: str,
        combined_text: str,
        category: SourceCategory,
    ) -> AnalysisResult:
        try:
            truncated = combined_text[:8000]
            prompt = (
                f"Analyze this information for the query: '{query}'\n\n"
                f"Content:\n{truncated}\n\n"
                "Answer these 4 questions:\n"
                "1. What happened?\n"
                "2. Why does it matter?\n"
                "3. What changed?\n"
                "4. What are the implications?\n\n"
                "Also list 3-5 key findings and a recommendation."
            )
            response_data = self._llm.complete(prompt)
            response_text = response_data.text if hasattr(response_data, "text") else str(response_data)
            parsed = self._parse_llm_response(response_text)
            parsed.analysis_method = "llm"
            return parsed
        except Exception as e:
            logger.warning("LLM analysis failed, falling back to rule-based: %s", e)
            return self._analyze_rule_based(query, combined_text, [], category)

    def _parse_llm_response(self, text: str) -> AnalysisResult:
        sections = {
            "what_happened": "",
            "why_it_matters": "",
            "what_changed": "",
            "implications": "",
        }
        current_section = None
        key_findings = []
        recommendation = ""

        for line in text.split("\n"):
            line_lower = line.lower().strip()
            if "what happened" in line_lower:
                current_section = "what_happened"
            elif "why does it matter" in line_lower or "why it matters" in line_lower:
                current_section = "why_it_matters"
            elif "what changed" in line_lower:
                current_section = "what_changed"
            elif "implication" in line_lower:
                current_section = "implications"
            elif "key finding" in line_lower:
                current_section = "key_findings"
            elif "recommendation" in line_lower:
                current_section = "recommendation"
            elif current_section == "key_findings" and line.strip().startswith("-"):
                key_findings.append(line.strip()[1:].strip())
            elif current_section == "recommendation" and line.strip():
                recommendation = line.strip()
            elif current_section and current_section in sections:
                if line.strip():
                    if sections[current_section]:
                        sections[current_section] += " " + line.strip()
                    else:
                        sections[current_section] = line.strip()

        return AnalysisResult(
            what_happened=sections["what_happened"],
            why_it_matters=sections["why_it_matters"],
            what_changed=sections["what_changed"],
            implications=sections["implications"],
            key_findings=key_findings or ["See analysis summary"],
            recommendation=recommendation or "Review the analysis for actionable insights.",
            confidence=0.7,
            analysis_method="llm",
        )

    def _analyze_rule_based(
        self,
        query: str,
        combined_text: str,
        results: list[FetchResult],
        category: SourceCategory,
    ) -> AnalysisResult:
        kw = self._keyword_extractor
        entities = kw.extract_keywords(combined_text)
        numbers = kw.extract_numbers(combined_text)
        dates = kw.extract_dates(combined_text)

        what_happened = self._build_what_happened(results, category, entities[:5])
        why_it_matters = self._build_why_it_matters(category, entities, numbers)
        what_changed = self._build_what_changed(category, numbers)
        implications = self._build_implications(category, entities)
        key_findings = self._build_key_findings(results, entities, numbers, dates)
        recommendation = self._build_recommendation(category, key_findings)

        return AnalysisResult(
            what_happened=what_happened,
            why_it_matters=why_it_matters,
            what_changed=what_changed,
            implications=implications,
            key_findings=key_findings,
            recommendation=recommendation,
            confidence=0.5,
            analysis_method="rule-based",
        )

    def _build_what_happened(
        self,
        results: list[FetchResult],
        category: SourceCategory,
        entities: list[str],
    ) -> str:
        if not results:
            return "No information retrieved."
        source_names = [r.source_name for r in results if r.success]
        source_str = ", ".join(source_names[:3]) or "multiple sources"
        entity_str = ", ".join(entities[:3]) if entities else "various topics"
        return (
            f"Information from {source_str} reports on {entity_str}. "
            f"Content covers developments in {category.value}."
        )

    def _build_why_it_matters(
        self,
        category: SourceCategory,
        entities: list[str],
        numbers: list[str],
    ) -> str:
        entity_str = ", ".join(entities[:3]) if entities else "this topic"
        num_str = ", ".join(numbers[:3]) if numbers else ""
        reasons = []
        if category == SourceCategory.AI:
            reasons.append("AI developments affect productivity, privacy, and industry landscapes")
        elif category == SourceCategory.SECURITY:
            reasons.append("Security developments directly impact system safety and data protection")
        elif category == SourceCategory.MARKET:
            reasons.append("Market movements affect investment decisions and economic outlook")
        elif category == SourceCategory.CRYPTO:
            reasons.append("Crypto developments signal shifts in digital finance and technology adoption")
        elif category == SourceCategory.NEWS:
            reasons.append("Technology news shapes understanding of the digital world")
        else:
            reasons.append(f"Changes in {entity_str} affect technology decisions")
        if num_str:
            reasons.append(f"Notable figures: {num_str}")
        return " | ".join(reasons)

    def _build_what_changed(self, category: SourceCategory, numbers: list[str]) -> str:
        if numbers:
            return f"New data points reported: {', '.join(numbers[:3])}"
        return "Content represents current state of information at time of fetch."

    def _build_implications(self, category: SourceCategory, entities: list[str]) -> str:
        entity_str = ", ".join(entities[:3]) if entities else "these developments"
        implications = {
            SourceCategory.AI: f"Organizations should monitor {entity_str} and evaluate impact on their AI strategy",
            SourceCategory.SECURITY: f"Security teams should review {entity_str} and assess vulnerability exposure",
            SourceCategory.MARKET: f"Investors may want to factor {entity_str} into their analysis",
            SourceCategory.CRYPTO: f"Crypto participants should evaluate how {entity_str} affects positions",
            SourceCategory.NEWS: f"Staying informed about {entity_str} helps anticipate industry shifts",
        }.get(category, f"Review how {entity_str} applies to your context")
        return implications

    def _build_key_findings(
        self,
        results: list[FetchResult],
        entities: list[str],
        numbers: list[str],
        dates: list[str],
    ) -> list[str]:
        findings = []
        for r in results[:3]:
            if r.success:
                title = ""
                title_match = re.search(r"^(.+?)\n\n", r.parsed_text)
                if title_match:
                    title = title_match.group(1).strip()
                    findings.append(f"{r.source_name}: {title[:120]}")

        if entities:
            findings.append(f"Key entities mentioned: {', '.join(entities[:5])}")
        if numbers:
            findings.append(f"Financial/metric data: {', '.join(numbers[:3])}")
        if dates:
            findings.append(f"Relevant dates: {', '.join(dates[:3])}")

        if not findings:
            findings.append("Content retrieved but could not auto-extract key findings")
        return findings[:5]

    def _build_recommendation(self, category: SourceCategory, findings: list[str]) -> str:
        base_recommendations = {
            SourceCategory.AI: "Consider how these AI updates apply to your work. Run MOSO analysis for deeper insights.",
            SourceCategory.SECURITY: "Review your security posture against any new threats. Apply patches if needed.",
            SourceCategory.MARKET: "Use this information as one data point in your broader market analysis.",
            SourceCategory.CRYPTO: "Conduct your own research before making any financial decisions based on this data.",
            SourceCategory.NEWS: "Stay updated by checking sources directly for full articles.",
        }
        return base_recommendations.get(
            category,
            "Review the findings above and take appropriate action based on your needs.",
        )

    def deep_analyze(
        self,
        query: str,
        results: list[FetchResult],
        verifications: dict[str, SourceVerification],
        category: SourceCategory = SourceCategory.GENERAL,
    ) -> dict:
        combined_text = "\n\n".join(r.parsed_text for r in results if r.success)
        if not combined_text.strip():
            return {"error": "No content available for analysis"}

        if self._llm is not None:
            try:
                truncated = combined_text[:12000]
                prompt = (
                    f"Perform a deep 15-point structured analysis for the query: '{query}'\n\n"
                    f"Content:\n{truncated}\n\n"
                    "Answer these questions:\n"
                    "1. What happened? (concise summary)\n"
                    "2. Why does it matter? (significance)\n"
                    "3. What changed? (delta from previous state)\n"
                    "4. What are the implications? (broader impact)\n"
                    "5. Who are the key actors/entities?\n"
                    "6. What is the timeline of events?\n"
                    "7. What evidence supports the claims?\n"
                    "8. What evidence contradicts the claims?\n"
                    "9. What is the confidence level? (0.0-1.0)\n"
                    "10. What gaps exist in the information?\n"
                    "11. What are the technical details?\n"
                    "12. What are related topics/queries?\n"
                    "13. What methodology was used?\n"
                    "14. What are the limitations?\n"
                    "15. What recommendations follow?\n\n"
                    "Format each answer as 'N. label: answer' on its own line."
                )
                response_data = self._llm.complete(prompt)
                response_text = response_data.text if hasattr(response_data, "text") else str(response_data)
                return self._parse_deep_analysis(response_text)
            except Exception as e:
                logger.warning("Deep LLM analysis failed: %s", e)

        return self._deep_analyze_rule_based(query, combined_text, results, category)

    def _parse_deep_analysis(self, text: str) -> dict:
        result: dict = {}
        current_section: Optional[str] = None
        for line in text.split("\n"):
            line = line.strip()
            if not line:
                continue
            import re as _re
            m = _re.match(r"^(\d{1,2})[\.\)]\s+(.+?):\s*(.*)", line)
            if m:
                num = int(m.group(1))
                label = m.group(2).strip().lower()
                value = m.group(3).strip()
                keys = {
                    1: "what_happened", 2: "why_it_matters", 3: "what_changed",
                    4: "implications", 5: "key_actors", 6: "timeline",
                    7: "supporting_evidence", 8: "contradicting_evidence",
                    9: "confidence", 10: "gaps", 11: "technical_details",
                    12: "related_topics", 13: "methodology", 14: "limitations",
                    15: "recommendations",
                }
                key = keys.get(num)
                if key:
                    result[key] = value
                    current_section = key
            elif current_section and current_section in result:
                result[current_section] += " " + line
        return result

    def _deep_analyze_rule_based(
        self,
        query: str,
        combined_text: str,
        results: list[FetchResult],
        category: SourceCategory,
    ) -> dict:
        kw = self._keyword_extractor
        entities = kw.extract_keywords(combined_text)
        numbers = kw.extract_numbers(combined_text)
        dates = kw.extract_dates(combined_text)

        source_names = [r.source_name for r in results if r.success]

        return {
            "what_happened": self._build_what_happened(results, category, entities),
            "why_it_matters": self._build_why_it_matters(category, entities, numbers),
            "what_changed": self._build_what_changed(category, numbers),
            "implications": self._build_implications(category, entities),
            "key_actors": [e for e in entities[:8]],
            "timeline": dates[:5] if dates else ["No dates extracted"],
            "supporting_evidence": [f"{s}: content verified" for s in source_names[:5]],
            "contradicting_evidence": [],
            "confidence": 0.4,
            "gaps": ["Rule-based analysis may miss nuances"],
            "technical_details": [f"Sources: {', '.join(source_names[:5])}"],
            "related_topics": [f"{category.value} developments"],
            "methodology": "Rule-based extraction from fetched content",
            "limitations": ["No cross-referencing performed", "No temporal validation"],
            "recommendations": [self._build_recommendation(category, [])],
        }
