"""Quality gate prompts — Gemini evaluation + Claude optimization.

Two prompts:
1. Gemini evaluation: actually sees/hears the asset and scores it
2. Claude optimization: takes Gemini's feedback and improves the prompt
"""


def build_gemini_eval_prompt(
    asset_type: str,
    creative_brief: dict,
    original_prompt: str,
    step_description: str = "",
) -> str:
    """Build the Gemini vision evaluation prompt.

    Gemini actually SEES the image, WATCHES the video, or LISTENS to the audio.
    It scores 1-10 and provides specific, actionable feedback.
    """
    concept = creative_brief.get("concept", "")
    style = creative_brief.get("visual_style", "")
    tone = creative_brief.get("tone", "")

    if asset_type == "image":
        criteria = """Score each criterion 1-10:
- **Prompt adherence**: Does the image match what was requested?
- **Visual quality**: Resolution, clarity, artifacts, distortions?
- **Style consistency**: Does it match the creative brief's visual style?
- **Composition**: Is the framing, layout, and focal point effective?
- **Technical**: Any deformed hands, faces, text, or anatomical issues?"""
    elif asset_type == "video":
        criteria = """Score each criterion 1-10:
- **Motion quality**: Smooth movement? Jitter, warping, or freezing?
- **Visual coherence**: Do elements stay consistent throughout?
- **Subject integrity**: Does the main subject maintain appearance?
- **Prompt adherence**: Does the video match the requested action/scene?
- **Technical**: Any flickering, morphing artifacts, or resolution drops?"""
    else:  # audio
        criteria = """Score each criterion 1-10:
- **Clarity**: Is the audio clear without distortion or noise?
- **Pronunciation**: Are words pronounced correctly and naturally?
- **Pacing**: Is the delivery speed appropriate for the content?
- **Tone**: Does the voice match the creative brief's tone?
- **Technical**: Any clicks, pops, unnatural pauses, or artifacts?"""

    return f"""You are a quality control expert at a production studio.
Evaluate this {asset_type} against the creative brief and original prompt.

CREATIVE BRIEF:
- Concept: {concept}
- Visual style: {style}
- Tone: {tone}

ORIGINAL PROMPT: {original_prompt}
STEP: {step_description}

{criteria}

Return your evaluation as JSON:
{{
  "overall_score": <float 1-10>,
  "criteria_scores": {{"criterion_name": <float 1-10>, ...}},
  "issues": ["Specific issue 1", "Specific issue 2"],
  "suggestions": ["Specific fix 1", "Specific fix 2"],
  "passed": <true if overall_score >= 7>,
  "summary": "One-sentence quality assessment"
}}"""


def build_prompt_optimization(
    original_prompt: str,
    gemini_analysis: dict,
    model_id: str,
    creative_brief: dict,
    retry_number: int,
) -> str:
    """Build the Claude prompt optimization request.

    Takes Gemini's quality feedback and generates an improved prompt
    that addresses the specific issues found.
    """
    issues = gemini_analysis.get("issues", [])
    suggestions = gemini_analysis.get("suggestions", [])
    score = gemini_analysis.get("overall_score", 0)
    summary = gemini_analysis.get("summary", "")

    issues_str = "\n".join(f"- {i}" for i in issues) if issues else "None specified"
    suggestions_str = "\n".join(f"- {s}" for s in suggestions) if suggestions else "None specified"

    concept = creative_brief.get("concept", "")
    style = creative_brief.get("visual_style", "")

    return f"""The quality gate scored this generation {score}/10.

ORIGINAL PROMPT:
{original_prompt}

QUALITY ISSUES:
{issues_str}

SUGGESTED FIXES:
{suggestions_str}

QUALITY SUMMARY: {summary}

CREATIVE BRIEF CONTEXT:
- Concept: {concept}
- Visual style: {style}

MODEL: {model_id}
RETRY: {retry_number}/3

Generate an IMPROVED prompt that:
1. Addresses each specific issue listed above
2. Maintains the creative brief's style and concept
3. Is formatted appropriately for the {model_id} model
4. Does NOT simply repeat the original — make targeted changes

Return ONLY the improved prompt text, nothing else."""
