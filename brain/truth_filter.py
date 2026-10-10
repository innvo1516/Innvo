import re
import logging
from typing import Dict, Any, List, Optional

from internet.web_searcher import WebSearcher

logger = logging.getLogger("InnvoTruthFilter")

class TruthFilter:
    """
    Multi-Source Fact Verification and Triangulation Engine.
    Ensures newly learned facts or search results pass consensus checks
    before being committed as permanent knowledge.
    """

    def __init__(self, searcher: Optional[WebSearcher] = None):
        self.searcher = searcher or WebSearcher()

    def verify_fact(self, claim: str) -> Dict[str, Any]:
        """
        Cross-checks a factual claim against multiple internet sources (DuckDuckGo + Wikipedia).
        Returns confidence score (0.0 to 1.0) and status.
        """
        claim_clean = claim.strip()
        if not claim_clean:
            return {"verified": False, "confidence": 0.0, "reason": "Empty claim"}

        # Search multiple sources
        results = self.searcher.search(claim_clean, max_results=4)
        if not results:
            return {
                "verified": False,
                "confidence": 0.2,
                "reason": "No corroborating sources found",
                "sources": []
            }

        # Analyze matching key tokens
        claim_keywords = set([w.lower() for w in re.findall(r"\b\w{4,}\b", claim_clean)])
        if not claim_keywords:
            return {
                "verified": True,
                "confidence": 0.5,
                "reason": "Generic statement",
                "sources": [r.get("url", "") for r in results[:2]]
            }

        corroborated_sources = 0
        snippets = []

        for r in results:
            snippet = r.get("snippet", "").lower()
            overlap = [kw for kw in claim_keywords if kw in snippet]
            if len(overlap) >= max(1, len(claim_keywords) // 2):
                corroborated_sources += 1
                snippets.append(r.get("snippet", ""))

        confidence = min(1.0, round(corroborated_sources / max(1, len(results)), 2))
        is_verified = confidence >= 0.5

        return {
            "verified": is_verified,
            "confidence": confidence,
            "corroborated_count": corroborated_sources,
            "sources": [r.get("url", "") for r in results[:3] if r.get("url")],
            "sample_snippet": snippets[0] if snippets else (results[0].get("snippet") if results else "")
        }
