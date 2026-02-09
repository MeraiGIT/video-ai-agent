"""
Tavily web search service — research phase support.

Provides web search capabilities for trend analysis,
platform best practices, and reference gathering.
"""

import logging
from config import settings

logger = logging.getLogger(__name__)

_client = None


def _get_client():
    """Lazy-load the Tavily client singleton."""
    global _client
    if _client is None:
        if not settings.TAVILY_API_KEY:
            raise RuntimeError("TAVILY_API_KEY not set — web search unavailable")
        from tavily import TavilyClient
        _client = TavilyClient(api_key=settings.TAVILY_API_KEY)
    return _client


def search(query: str, max_results: int = 5) -> list[dict]:
    """Search the web and return structured results.

    Args:
        query: Search query string.
        max_results: Maximum results to return (1-10).

    Returns:
        List of {title, url, content} dicts.
    """
    client = _get_client()
    max_results = max(1, min(max_results, 10))

    logger.info("[tavily] Searching: %s", query[:80])
    response = client.search(query=query, max_results=max_results)

    results = []
    for item in response.get("results", []):
        results.append({
            "title": item.get("title", ""),
            "url": item.get("url", ""),
            "content": item.get("content", "")[:500],
        })

    logger.info("[tavily] Got %d results for: %s", len(results), query[:50])
    return results


def search_multiple(queries: list[str], max_results_per: int = 3) -> list[dict]:
    """Run multiple searches and return combined results.

    Args:
        queries: List of search queries.
        max_results_per: Max results per query.

    Returns:
        Combined list of {title, url, content, query} dicts.
    """
    all_results = []
    for query in queries:
        try:
            results = search(query, max_results=max_results_per)
            for r in results:
                r["query"] = query
            all_results.extend(results)
        except Exception as e:
            logger.warning("[tavily] Search failed for '%s': %s", query[:50], e)

    return all_results
