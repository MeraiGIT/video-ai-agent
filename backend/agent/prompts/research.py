"""Research phase prompts — web search query generation and synthesis."""


RESEARCH_QUERY_SYSTEM = (
    "You are a creative research assistant. Generate targeted web search queries "
    "to gather information that will make this content project better. "
    "Return ONLY valid JSON."
)


def build_query_generation_prompt(
    user_request: str,
    content_type: str,
    target_platform: str,
    target_audience: str,
    interview_answers: str = "",
) -> str:
    """Build prompt for generating search queries.

    Returns a prompt that asks Claude to generate 2-4 targeted search queries.
    """
    context = f"""Content type: {content_type}
Platform: {target_platform}
Audience: {target_audience}"""

    if interview_answers:
        context += f"\nAdditional context from user: {interview_answers}"

    return f"""Generate 2-4 targeted web search queries for this project:

USER REQUEST: {user_request}

{context}

Research should help with:
1. What's currently trending/performing well in this format
2. Platform-specific best practices and specs
3. Reference content or inspiration
4. Audience preferences and expectations

Return ONLY this JSON:
{{
  "queries": [
    "search query 1",
    "search query 2",
    "search query 3"
  ],
  "research_goals": "Brief description of what we're trying to learn"
}}

RULES:
- Be specific — "TikTok morning routine trends 2026" not "morning routines"
- Include platform name in at least one query
- Focus on actionable insights, not general knowledge"""


RESEARCH_SYNTHESIS_SYSTEM = (
    "You are a research analyst synthesizing web search results into actionable "
    "creative insights. Be concise and focus on what matters for production."
)


def build_synthesis_prompt(
    user_request: str,
    content_type: str,
    target_platform: str,
    search_results: list[dict],
) -> str:
    """Build prompt for synthesizing search results into insights.

    Args:
        search_results: List of {title, url, content, query} dicts from Tavily.
    """
    results_text = ""
    for r in search_results:
        results_text += f"\n**{r.get('title', 'No title')}** ({r.get('url', '')})\n"
        results_text += f"  {r.get('content', '')}\n"

    return f"""Synthesize these research results into actionable insights for a {content_type} project.

USER REQUEST: {user_request}
PLATFORM: {target_platform}

SEARCH RESULTS:
{results_text}

Return a JSON summary:
{{
  "trends": ["Key trend 1", "Key trend 2"],
  "platform_specs": {{
    "recommended_duration": "...",
    "aspect_ratio": "...",
    "other_specs": "..."
  }},
  "references": [
    {{"title": "...", "url": "...", "relevance": "..."}}
  ],
  "recommendations": [
    "Actionable recommendation 1",
    "Actionable recommendation 2"
  ],
  "summary": "2-3 sentence overview of key findings"
}}"""
