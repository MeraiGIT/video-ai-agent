"""Interview prompt — smart follow-up questions for the user."""


INTERVIEW_SYSTEM = (
    "You are a creative director interviewing a client. "
    "Ask smart, high-impact follow-up questions that will meaningfully improve "
    "the final output. Don't ask obvious questions — be insightful. "
    "If the client says 'just figure it out', respect that."
)


def build_interview_prompt(
    user_request: str,
    content_type: str,
    target_platform: str,
    target_audience: str,
    constraints: dict | None = None,
    interview_reason: str = "",
) -> str:
    """Build the interview follow-up questions prompt.

    Args:
        user_request: Original user request.
        content_type: Classified content type from intake.
        target_platform: Target platform.
        target_audience: Target audience description.
        constraints: Any constraints identified during intake.
        interview_reason: Why the intake node decided an interview was needed.

    Returns:
        Formatted prompt string for Claude.
    """
    constraints_str = ""
    if constraints:
        parts = [f"- {k}: {v}" for k, v in constraints.items() if v is not None]
        if parts:
            constraints_str = "\nKnown constraints:\n" + "\n".join(parts)

    return f"""Based on the client's request, generate follow-up questions that would
significantly improve the quality of the final output.

CLIENT REQUEST: {user_request}

WHAT WE KNOW:
- Content type: {content_type}
- Target platform: {target_platform}
- Target audience: {target_audience}{constraints_str}

WHY WE'RE ASKING: {interview_reason}

Generate 2-4 follow-up questions. For each question:
1. Explain briefly why it matters (in parentheses)
2. Provide 2-3 example answers so the client understands what you're looking for
3. Prioritize by impact — the first question should be the most important

FORMAT your response as natural text that I'll show directly to the client.
Be conversational and professional. Start with a brief acknowledgment of their request,
then ask your questions.

Example format:
"Great idea for a [type]! I have a few quick questions to make sure we nail this:

1. **Who's the primary audience?** (This shapes the tone and visual style)
   For example: Gen Z consumers, B2B executives, fitness enthusiasts

2. **What mood are you going for?** (This guides music, pacing, and color grading)
   For example: Energetic and fast-paced, calm and professional, dramatic and cinematic"

RULES:
- Maximum 4 questions
- Don't ask what's already clear from the request
- If the request mentions a specific reference or style, don't ask about style
- Every question should meaningfully change the output
- End with: "Or just say 'go ahead' and I'll use my best judgment!"
"""
