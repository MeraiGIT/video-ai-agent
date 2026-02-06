import json
import anthropic
from config import settings

client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
MODEL = "claude-sonnet-4-5-20250929"


def modify_script(current_script: str, user_request: str) -> str:
    """Revise a script based on the user's natural-language feedback."""
    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=(
            "You are a video script editor. The user has a script and wants changes. "
            "Apply their requested changes while maintaining the script's quality, "
            "natural tone, and ~120-150 word length. Return ONLY the revised script text."
        ),
        messages=[
            {
                "role": "user",
                "content": (
                    f"Current script:\n\n{current_script}\n\n"
                    f"Requested changes: {user_request}\n\n"
                    "Return ONLY the revised narration text."
                ),
            }
        ],
    )
    return response.content[0].text.strip()


def modify_scenes(current_scenes: list[dict], user_request: str) -> list[dict]:
    """Revise scene plan based on user feedback. Returns updated scenes list."""
    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=(
            "You are a video scene editor. The user has a scene plan and wants changes. "
            "Apply their requested changes. Return ONLY the complete updated JSON array "
            "of scenes in the same format. Do not omit any scenes."
        ),
        messages=[
            {
                "role": "user",
                "content": (
                    f"Current scenes:\n\n{json.dumps(current_scenes, indent=2)}\n\n"
                    f"Requested changes: {user_request}\n\n"
                    "Return ONLY the complete JSON array of all scenes."
                ),
            }
        ],
    )
    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        text = text.rsplit("```", 1)[0]
    return json.loads(text)


def interpret_regeneration_request(user_request: str, scenes: list[dict]) -> list[int]:
    """Parse user request to determine which scene indices to regenerate.

    Returns list of 0-based scene indices.
    """
    scene_summaries = [
        {"scene_number": s["scene_number"], "visual": s["visual_description"][:60]}
        for s in scenes
    ]
    response = client.messages.create(
        model=MODEL,
        max_tokens=256,
        system=(
            "You extract scene numbers from user requests. "
            "Return ONLY a JSON array of 0-based indices. "
            f"There are {len(scenes)} scenes (indices 0-{len(scenes) - 1})."
        ),
        messages=[
            {
                "role": "user",
                "content": (
                    f"Scenes: {json.dumps(scene_summaries)}\n\n"
                    f"User request: {user_request}\n\n"
                    "Return ONLY a JSON array of 0-based indices to regenerate."
                ),
            }
        ],
    )
    text = response.content[0].text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[1]
        text = text.rsplit("```", 1)[0]
    return json.loads(text)
