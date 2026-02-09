"""Research node — web search + trend analysis.

Uses Claude to generate targeted search queries, Tavily for web search,
then Claude again to synthesize results into actionable insights.
"""

import json
import logging

from langgraph.config import get_stream_writer

from agent.state import ProductionState
from agent.prompts.research import (
    RESEARCH_QUERY_SYSTEM,
    RESEARCH_SYNTHESIS_SYSTEM,
    build_query_generation_prompt,
    build_synthesis_prompt,
)
from services.claude_service import client, MODEL

logger = logging.getLogger(__name__)


def run(state: ProductionState) -> dict:
    """Run web research and synthesize findings into actionable insights."""
    writer = get_stream_writer()

    writer({
        "event": "progress",
        "data": {"stage": "research", "message": "Researching trends and best practices..."},
    })

    user_request = state.get("user_request", "")
    content_type = state.get("content_type", "short_video")
    platform = state.get("target_platform", "unspecified")
    audience = state.get("target_audience", "general")
    interview_answers = state.get("interview_answers", "")

    # Step 1: Generate search queries with Claude
    query_prompt = build_query_generation_prompt(
        user_request, content_type, platform, audience, interview_answers,
    )

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=512,
            system=RESEARCH_QUERY_SYSTEM,
            messages=[{"role": "user", "content": query_prompt}],
        )
        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        query_data = json.loads(text)
        queries = query_data.get("queries", [])
    except Exception as e:
        logger.warning("Query generation failed: %s", e)
        queries = [f"{content_type} {platform} trends 2026"]

    if not queries:
        queries = [f"{content_type} {platform} trends 2026"]

    writer({
        "event": "progress",
        "data": {
            "stage": "research",
            "message": f"Searching the web ({len(queries)} queries)...",
        },
    })

    # Step 2: Search the web with Tavily
    from services.tavily_service import search_multiple

    try:
        search_results = search_multiple(queries, max_results_per=3)
        logger.info("Research: got %d results from %d queries", len(search_results), len(queries))
    except Exception as e:
        logger.warning("Tavily search failed: %s", e)
        search_results = []

    if not search_results:
        writer({
            "event": "message",
            "data": {
                "role": "assistant",
                "content": "Web research didn't return useful results. I'll use my knowledge to proceed.",
            },
        })
        return {
            "research_insights": {"summary": "No web results available. Using existing knowledge."},
            "status": "research_complete",
            "progress_messages": ["Research: no results, proceeding with knowledge"],
        }

    # Step 3: Synthesize results with Claude
    writer({
        "event": "progress",
        "data": {"stage": "research", "message": "Synthesizing research findings..."},
    })

    synthesis_prompt = build_synthesis_prompt(
        user_request, content_type, platform, search_results,
    )

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=1024,
            system=RESEARCH_SYNTHESIS_SYSTEM,
            messages=[{"role": "user", "content": synthesis_prompt}],
        )
        text = response.content[0].text.strip()
        if text.startswith("```"):
            text = text.split("\n", 1)[1].rsplit("```", 1)[0]
        insights = json.loads(text)
    except Exception as e:
        logger.warning("Research synthesis failed: %s", e)
        insights = {
            "summary": "Research completed but synthesis failed.",
            "trends": [],
            "recommendations": [],
        }

    # Show summary to user
    summary = insights.get("summary", "Research complete.")
    trends = insights.get("trends", [])
    recs = insights.get("recommendations", [])

    msg_parts = [f"**Research findings:**\n\n{summary}"]
    if trends:
        msg_parts.append("\n\n**Key trends:**")
        for t in trends[:5]:
            msg_parts.append(f"\n- {t}")
    if recs:
        msg_parts.append("\n\n**Recommendations:**")
        for r in recs[:5]:
            msg_parts.append(f"\n- {r}")

    writer({
        "event": "message",
        "data": {"role": "assistant", "content": "".join(msg_parts)},
    })

    return {
        "research_insights": insights,
        "status": "research_complete",
        "progress_messages": [f"Research: {len(search_results)} results, {len(trends)} trends"],
    }
