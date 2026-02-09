"""Caption style presets and ASS format builder.

Provides named caption styles (tiktok, youtube, cinematic, minimal, bold,
karaoke, none) as dicts with ASS subtitle parameters.  Also has a
word-by-word SRT splitter that takes faster-whisper segments with
word-level timestamps and emits one SRT entry per word.
"""

from __future__ import annotations

from utils.srt import format_timestamp

# ── Colour helpers ─────────────────────────────────────────────────────
# ASS uses &HAABBGGRR (alpha, blue, green, red).
# We accept "#RRGGBB" or "RRGGBB" hex strings for ergonomics.


def _hex_to_ass(hex_color: str) -> str:
    """Convert '#RRGGBB' to ASS '&H00BBGGRR' (alpha=00 → fully opaque)."""
    h = hex_color.lstrip("#")
    r, g, b = h[0:2], h[2:4], h[4:6]
    return f"&H00{b}{g}{r}"


# ── Style presets ──────────────────────────────────────────────────────

CAPTION_STYLES: dict[str, dict] = {
    "tiktok": {
        "FontName": "Montserrat Bold",
        "FontSize": 28,
        "PrimaryColour": "&H00FFFFFF",
        "OutlineColour": "&H00000000",
        "BackColour": "&H80000000",
        "Outline": 3,
        "Shadow": 0,
        "Alignment": 2,
        "MarginV": 50,
        "Bold": 1,
    },
    "youtube": {
        "FontName": "Arial",
        "FontSize": 22,
        "PrimaryColour": "&H00FFFFFF",
        "OutlineColour": "&H00000000",
        "BackColour": "&H80000000",
        "Outline": 2,
        "Shadow": 0,
        "Alignment": 2,
        "MarginV": 30,
        "Bold": 0,
    },
    "cinematic": {
        "FontName": "Georgia",
        "FontSize": 20,
        "PrimaryColour": "&H00E0E0E0",
        "OutlineColour": "&H00000000",
        "BackColour": "&H00000000",
        "Outline": 1,
        "Shadow": 1,
        "Alignment": 2,
        "MarginV": 40,
        "Bold": 0,
    },
    "minimal": {
        "FontName": "Helvetica",
        "FontSize": 18,
        "PrimaryColour": "&H00FFFFFF",
        "OutlineColour": "&H00000000",
        "BackColour": "&H00000000",
        "Outline": 1,
        "Shadow": 0,
        "Alignment": 2,
        "MarginV": 25,
        "Bold": 0,
    },
    "bold": {
        "FontName": "Impact",
        "FontSize": 32,
        "PrimaryColour": "&H0000FFFF",   # Yellow
        "OutlineColour": "&H00000000",
        "BackColour": "&H80000000",
        "Outline": 3,
        "Shadow": 2,
        "Alignment": 2,
        "MarginV": 45,
        "Bold": 1,
    },
    "karaoke": {
        "FontName": "Montserrat Bold",
        "FontSize": 30,
        "PrimaryColour": "&H0000FFFF",   # Yellow highlight
        "OutlineColour": "&H00000000",
        "BackColour": "&H80000000",
        "Outline": 3,
        "Shadow": 0,
        "Alignment": 2,
        "MarginV": 50,
        "Bold": 1,
    },
    "none": {},
}


def get_style_names() -> list[str]:
    """Return available caption style names."""
    return list(CAPTION_STYLES.keys())


def get_style(name: str) -> dict:
    """Get a caption style dict by name, defaulting to 'youtube'."""
    return dict(CAPTION_STYLES.get(name, CAPTION_STYLES["youtube"]))


def build_ass_style_string(
    style_name: str = "youtube",
    overrides: dict | None = None,
) -> str:
    """Build an ASS force_style string from a preset + optional overrides.

    Returns a string like:
      FontName=Arial,FontSize=22,PrimaryColour=&H00FFFFFF,...

    Suitable for the ffmpeg ``subtitles`` filter's ``force_style`` option.
    """
    if style_name == "none":
        return ""

    params = get_style(style_name)
    if overrides:
        # Accept hex colour overrides like "#FF0000"
        for key in ("PrimaryColour", "OutlineColour", "BackColour"):
            if key in overrides and isinstance(overrides[key], str) and overrides[key].startswith("#"):
                overrides[key] = _hex_to_ass(overrides[key])
        params.update(overrides)

    return ",".join(f"{k}={v}" for k, v in params.items())


# ── Word-by-word SRT ───────────────────────────────────────────────────

def write_word_srt(segments, output_path: str) -> int:
    """Write one-word-per-entry SRT file from faster-whisper segments.

    Args:
        segments: Iterable of faster-whisper Segment objects with ``.words``.
        output_path: File path for the output SRT file.

    Returns:
        Number of SRT entries written.
    """
    index = 0
    with open(output_path, "w", encoding="utf-8") as f:
        for segment in segments:
            words = list(segment.words) if segment.words else []
            if not words:
                # Fallback: treat the whole segment as one entry
                index += 1
                f.write(f"{index}\n")
                f.write(
                    f"{format_timestamp(segment.start)} --> "
                    f"{format_timestamp(segment.end)}\n"
                )
                f.write(f"{segment.text.strip()}\n\n")
                continue

            for w in words:
                index += 1
                f.write(f"{index}\n")
                f.write(
                    f"{format_timestamp(w.start)} --> "
                    f"{format_timestamp(w.end)}\n"
                )
                f.write(f"{w.word.strip()}\n\n")

    return index
