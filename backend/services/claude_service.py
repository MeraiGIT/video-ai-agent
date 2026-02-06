import json
import anthropic
from config import settings

client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

MODEL = "claude-sonnet-4-5-20250929"


def generate_script(topic: str) -> str:
    """Generate a 45-second video narration script."""
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
                "content": f"""Write a 45-second video narration script about: {topic}

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


def plan_scenes_from_script(script: str) -> list[dict]:
    """Break a script into visual scenes with image prompts."""
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
