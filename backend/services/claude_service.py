import json
import anthropic
from config import settings

client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

MODEL = "claude-sonnet-4-5-20250929"


def generate_script(topic: str, character_context: str = "") -> str:
    """Generate a 45-second video narration script."""
    extra = ""
    if character_context:
        extra = (
            f"\n\nIMPORTANT CHARACTER CONTEXT: {character_context}\n"
            "Incorporate this character naturally into the script."
        )

    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=(
            "You are a professional short-form video script writer. "
            "Write scripts that are engaging, conversational, and optimized "
            "for voice narration. Keep language natural and punchy."
        ),
        messages=[
            {
                "role": "user",
                "content": f"""Write a 45-second video narration script about: {topic}{extra}

REQUIREMENTS:
- Hook in the first 3 seconds (surprising fact, bold claim, or question)
- Clear value delivered in the body
- Conversational tone, written for voice narration (not reading)
- Strong call to action at the end
- Total length: ~120-150 words (roughly 45 seconds when spoken)

OUTPUT: Write ONLY the narration text, broken into natural paragraphs.
Do NOT include scene directions, timestamps, or formatting markers.
Just the words that will be spoken aloud.""",
            }
        ],
    )
    return response.content[0].text


def plan_scenes_from_script(
    script: str,
    character_description: str = "",
) -> list[dict]:
    """Break a script into visual scenes with image prompts.

    If character_description is provided, it will be embedded in every
    image prompt for character consistency across scenes.
    """
    character_instruction = ""
    if character_description:
        character_instruction = f"""
CRITICAL — CHARACTER CONSISTENCY:
The video features this character: {character_description}

You MUST include this exact character description in EVERY image_prompt.
Each scene's image_prompt should start with the character description,
then describe the scene-specific action and setting. This ensures the
same character appears consistently across all generated images.

Example image_prompt format:
"[Character description], [scene-specific action and setting], cinematic, professional, 16:9, photorealistic"
"""

    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=(
            "You are a video scene planner and visual director. "
            "You break narration scripts into visual scenes and write "
            "detailed image generation prompts. Return ONLY valid JSON."
        ),
        messages=[
            {
                "role": "user",
                "content": f"""Break this narration script into 4-6 visual scenes:

{script}
{character_instruction}
For each scene, provide:
1. scene_number: Sequential number
2. narration: The exact words spoken during this scene
3. visual_description: What the viewer should see
4. image_prompt: A detailed prompt for an AI image generator (include style: cinematic, professional, 16:9 aspect ratio, high quality, photorealistic)
5. duration: How long this scene lasts in seconds (all durations should sum to ~45 seconds)

OUTPUT FORMAT - Return ONLY a JSON array:
[
  {{
    "scene_number": 1,
    "narration": "...",
    "visual_description": "...",
    "image_prompt": "...",
    "duration": 8
  }}
]""",
            }
        ],
    )

    text = response.content[0].text.strip()
    # Handle potential markdown code blocks
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        text = text.rsplit("```", 1)[0]
    return json.loads(text)


def analyze_user_request(
    topic: str,
    uploaded_files: list[dict] | None = None,
    available_models: str = "",
) -> dict:
    """Analyze a user's request and produce a generation plan.

    Returns a dict with:
      - character_description: str or "" if no character involved
      - recommended_video_model: str model id
      - use_reference_images: bool
      - reasoning: str (explanation for the user)
    """
    files_section = ""
    if uploaded_files:
        file_descs = []
        for f in uploaded_files:
            file_descs.append(f"- {f.get('filename', 'file')} (type: {f.get('type', 'unknown')})")
        files_section = (
            "\n\nUser uploaded these files:\n"
            + "\n".join(file_descs)
            + "\n\nConsider these files when planning. Images of people/pets/characters "
            "suggest the user wants character consistency."
        )

    response = client.messages.create(
        model=MODEL,
        max_tokens=1024,
        system=(
            "You are a professional AI content creation director. "
            "Analyze the user's video request and determine the optimal "
            "generation strategy. Return ONLY valid JSON."
        ),
        messages=[
            {
                "role": "user",
                "content": f"""Analyze this video creation request:

Topic: {topic}{files_section}

{available_models}

Based on the topic and any uploaded files, determine:
1. Does this request involve specific characters (people, pets, mascots, named individuals)?
   If yes, describe them concisely for image generation consistency.
2. What video model would be optimal? Consider:
   - Character consistency needs → kling_ref (only model with reference-to-video)
   - Standard videos with user's chosen model → respect their choice
   - Cost optimization → veo is cheapest, seedance is highest quality
3. Should we use reference images (from uploads) for image generation?

Return ONLY this JSON:
{{
  "character_description": "Concise visual description of the main character, or empty string if none",
  "recommended_video_model": "model_id",
  "use_reference_images": true/false,
  "reasoning": "Brief explanation of your recommendations"
}}""",
            }
        ],
    )

    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        text = text.rsplit("```", 1)[0]
    return json.loads(text)
