import warnings
import logging
import urllib.parse
from typing import List, Dict, Any
import requests

# Suppress rename warning from duckduckgo_search
warnings.filterwarnings("ignore", category=RuntimeWarning, message=".*renamed to.*ddgs.*")

try:
    from ddgs import DDGS
except ImportError:
    try:
        from duckduckgo_search import DDGS
    except ImportError:
        DDGS = None

import config

logger = logging.getLogger("InnvoWebSearcher")

class WebSearcher:
    """
    Zero-API-key internet searcher with:
    1. DuckDuckGo Text Search (Primary)
    2. Wikipedia Direct Summary (Fast offline/online knowledge fallback)
    """
    def __init__(self):
        pass

    def search_duckduckgo(self, query: str, max_results: int = 3) -> List[Dict[str, str]]:
        results = []
        try:
            with DDGS() as ddgs:
                raw_results = list(ddgs.text(query, max_results=max_results))
                for r in raw_results:
                    title = r.get("title", "").strip()
                    body = r.get("body", "").strip()
                    href = r.get("href", "").strip()
                    if title or body:
                        results.append({
                            "title": title,
                            "snippet": body,
                            "url": href
                        })
        except Exception as e:
            logger.debug(f"DuckDuckGo search exception: {e}")
        return results

    def search_wikipedia(self, query: str) -> List[Dict[str, str]]:
        """Free Wikipedia REST API lookup (no API key required)."""
        try:
            clean_q = query.replace("who is", "").replace("what is", "").replace("kaun hai", "").strip()
            encoded = urllib.parse.quote(clean_q)
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}"
            headers = {"User-Agent": "InnvoAssistant/1.0"}
            resp = requests.get(url, headers=headers, timeout=4)
            if resp.status_code == 200:
                data = resp.json()
                extract = data.get("extract")
                title = data.get("title")
                if extract:
                    return [{
                        "title": f"Wikipedia: {title}",
                        "snippet": extract,
                        "url": data.get("content_urls", {}).get("desktop", {}).get("page", "")
                    }]
        except Exception:
            pass
        return []

    def search(self, query: str, max_results: int = None) -> List[Dict[str, str]]:
        max_results = max_results or config.MAX_SEARCH_RESULTS
        # Try DuckDuckGo first
        results = self.search_duckduckgo(query, max_results=max_results)
        # If no results or failed, try Wikipedia fallback
        if not results:
            results = self.search_wikipedia(query)
        return results

    def get_summary_context(self, query: str) -> str:
        results = self.search(query)
        if not results:
            return ""

        context_lines = [f"[Live Internet Context for: '{query}']"]
        for i, item in enumerate(results, 1):
            context_lines.append(f"{i}. {item['title']}: {item['snippet']}")
        
        return "\n".join(context_lines)
