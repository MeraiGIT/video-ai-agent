"""Web search capability — wraps tavily_service."""

import logging

logger = logging.getLogger(__name__)


def execute(params: dict, state: dict, ctx: dict) -> dict:
    """Search the web for information.

    params:
        query: str — search query
        max_results: int — max results (default 5)
    """
    query = params.get("query", "")
    max_results = params.get("max_results", 5)

    if not query:
        raise ValueError("No query for web search")

    from services.tavily_service import search
    results = search(query, max_results=max_results)

    return {
        "results": results,
        "query": query,
        "model": "tavily",
        "cost": 0.0,
    }
