import logging
import os
import shutil
import subprocess
import time
import urllib.request
from pathlib import Path
from urllib.parse import urlparse
from utils.file_manager import get_job_path
from services.caption_styles import build_ass_style_string

logger = logging.getLogger(__name__)

# Timeout for FFmpeg operations (5 minutes for concat/assembly, generous for large videos)
_FFMPEG_TIMEOUT = 300


def check_ffmpeg_available() -> tuple[bool, str]:
    """Check if FFmpeg is installed and return (available, version_string)."""
    path = shutil.which("ffmpeg")
    if not path:
        return False, ""
    try:
        result = subprocess.run(
            ["ffmpeg", "-version"], capture_output=True, text=True, timeout=5
        )
        version_line = result.stdout.split("\n")[0] if result.stdout else "unknown"
        return True, version_line
    except Exception:
        return False, ""


def _run_ffmpeg(cmd: list[str], operation: str = ""):
    """Run an FFmpeg command and raise on failure."""
    available, _ = check_ffmpeg_available()
    if not available:
        raise RuntimeError(
            "FFmpeg is not installed or not found in PATH. "
            "Install it with: brew install ffmpeg (macOS) or apt install ffmpeg (Linux)"
        )
    logger.info("ffmpeg %s: running command", operation or "operation")
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=_FFMPEG_TIMEOUT,
    )
    if result.returncode != 0:
        context = f" during {operation}" if operation else ""
        stderr_lines = result.stderr.strip().split("\n")[-5:]
        raise RuntimeError(
            f"FFmpeg failed{context} (exit {result.returncode}):\n"
            + "\n".join(stderr_lines)
        )
    logger.info("ffmpeg %s: completed", operation or "operation")


def download_if_url(url_or_path: str, job_id: str) -> str:
    """Download an HTTP(S) URL to local workspace. Pass through local paths unchanged."""
    if not url_or_path:
        return url_or_path
    if not url_or_path.startswith(("http://", "https://")):
        return url_or_path

    parsed = urlparse(url_or_path)
    filename = os.path.basename(parsed.path) or f"download_{int(time.time())}"
    # Ensure unique filename to avoid collisions
    name, ext = os.path.splitext(filename)
    if not ext:
        ext = ".mp4"
    local_path = get_job_path(job_id, f"downloads/{name}_{int(time.time())}{ext}")
    os.makedirs(os.path.dirname(local_path), exist_ok=True)

    logger.info("Downloading %s -> %s", url_or_path[:80], local_path)
    urllib.request.urlretrieve(url_or_path, local_path)
    logger.info("Download complete: %s (%.1f MB)", local_path, os.path.getsize(local_path) / 1_048_576)
    return local_path


def concat_videos(video_paths: list[str], job_id: str) -> str:
    """Concatenate videos using filter_complex for codec safety.

    Scales all inputs to 1280x720 and re-encodes to h264.
    This handles different codecs/resolutions from different fal.ai models.
    """
    output_path = get_job_path(job_id, "concatenated.mp4")

    inputs = []
    filter_parts = []
    for i, path in enumerate(video_paths):
        inputs.extend(["-i", path])
        filter_parts.append(
            f"[{i}:v]scale=1280:720:force_original_aspect_ratio=decrease,"
            f"pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=24[v{i}]"
        )

    # Build concat filter
    filter_str = ";".join(filter_parts)
    concat_inputs = "".join(f"[v{i}]" for i in range(len(video_paths)))
    filter_str += f";{concat_inputs}concat=n={len(video_paths)}:v=1:a=0[outv]"

    cmd = (
        ["ffmpeg", "-y"]
        + inputs
        + [
            "-filter_complex",
            filter_str,
            "-map",
            "[outv]",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "23",
            output_path,
        ]
    )
    _run_ffmpeg(cmd, operation="video concatenation")
    return output_path


def overlay_audio(
    video_path: str, audio_path: str, job_id: str
) -> str:
    """Overlay voiceover audio onto the video."""
    output_path = get_job_path(job_id, "assembled.mp4")
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-i",
        audio_path,
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-shortest",
        output_path,
    ]
    _run_ffmpeg(cmd, operation="audio overlay")
    return output_path


def burn_subtitles(
    video_path: str,
    srt_path: str,
    job_id: str,
    style_name: str = "youtube",
    style_overrides: dict | None = None,
) -> str:
    """Burn SRT subtitles into the video.

    Uses the subtitles filter with forced styling.

    Args:
        video_path: Input video file.
        srt_path: SRT subtitle file.
        job_id: Workspace job ID.
        style_name: Caption style preset name (youtube, tiktok, cinematic,
                     minimal, bold, karaoke, none). Defaults to "youtube".
        style_overrides: Optional dict of ASS parameters to override in the
                         preset (e.g. {"FontSize": 26, "PrimaryColour": "#FF0000"}).
    """
    output_path = get_job_path(job_id, "final.mp4")

    # Escape special characters in path for FFmpeg subtitles filter
    escaped_srt = srt_path.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")

    style = build_ass_style_string(style_name, style_overrides)

    vf = f"subtitles={escaped_srt}"
    if style:
        vf += f":force_style='{style}'"

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-vf",
        vf,
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "23",
        "-c:a",
        "copy",
        output_path,
    ]
    _run_ffmpeg(cmd, operation="subtitle burning")
    return output_path


# ── Transitions ────────────────────────────────────────────────────────

# Supported xfade transitions (subset of FFmpeg builtins that look professional)
SUPPORTED_TRANSITIONS = {
    "none", "fade", "dissolve", "wipeleft", "wiperight", "wipeup", "wipedown",
    "slideleft", "slideright", "slideup", "slidedown", "smoothleft", "smoothright",
    "circlecrop", "rectcrop", "distance", "fadeblack", "fadewhite", "radial",
    "hblur",
}


def concat_videos_with_transitions(
    video_paths: list[str],
    job_id: str,
    transition: str = "fade",
    transition_duration: float = 0.5,
) -> str:
    """Concatenate videos with xfade transitions between clips.

    Each pair of adjacent clips gets the specified transition.
    Falls back to simple concat if transition is 'none' or only 1 clip.

    Offset calculation:  offset_i = sum(durations[0..i]) - i * transition_duration

    Args:
        video_paths: List of video file paths (minimum 2 for transitions).
        job_id: Workspace job ID.
        transition: xfade transition name (e.g. 'fade', 'dissolve', 'wipeleft').
        transition_duration: Duration of each transition in seconds (0.3-2.0).
    """
    if transition == "none" or len(video_paths) < 2:
        return concat_videos(video_paths, job_id)

    if transition not in SUPPORTED_TRANSITIONS:
        logger.warning("Unknown transition '%s', falling back to 'fade'", transition)
        transition = "fade"

    transition_duration = max(0.1, min(transition_duration, 2.0))

    output_path = get_job_path(job_id, "concatenated.mp4")

    # Probe durations of each clip
    durations = []
    for path in video_paths:
        dur = _probe_duration(path)
        durations.append(dur)

    # Build xfade filter chain
    inputs = []
    for i, path in enumerate(video_paths):
        inputs.extend(["-i", path])

    n = len(video_paths)
    filter_parts = []

    # Scale all inputs to uniform size first
    for i in range(n):
        filter_parts.append(
            f"[{i}:v]scale=1280:720:force_original_aspect_ratio=decrease,"
            f"pad=1280:720:(ow-iw)/2:(oh-ih)/2,setsar=1,fps=24[v{i}]"
        )

    # Chain xfade transitions: first pair produces [xf0], then [xf0]+[v2] -> [xf1], etc.
    cumulative_dur = durations[0]
    prev_label = "v0"

    for i in range(1, n):
        offset = cumulative_dur - transition_duration
        offset = max(0, offset)  # safety clamp

        out_label = f"xf{i - 1}" if i < n - 1 else "outv"
        filter_parts.append(
            f"[{prev_label}][v{i}]xfade=transition={transition}"
            f":duration={transition_duration}:offset={offset:.3f}[{out_label}]"
        )
        # After xfade, the output duration = cumulative - td + durations[i]
        cumulative_dur = offset + durations[i]
        prev_label = out_label

    filter_str = ";".join(filter_parts)

    cmd = (
        ["ffmpeg", "-y"]
        + inputs
        + [
            "-filter_complex",
            filter_str,
            "-map",
            "[outv]",
            "-c:v",
            "libx264",
            "-preset",
            "fast",
            "-crf",
            "23",
            output_path,
        ]
    )
    _run_ffmpeg(cmd, operation="video concatenation with transitions")
    return output_path


def _probe_duration(video_path: str) -> float:
    """Get video duration in seconds using ffprobe."""
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                video_path,
            ],
            capture_output=True, text=True, timeout=10,
        )
        return float(result.stdout.strip())
    except Exception:
        logger.warning("Could not probe duration of %s, assuming 5.0s", video_path)
        return 5.0


# ── Text overlays ──────────────────────────────────────────────────────

def add_text_overlay_to_video(
    video_path: str,
    text: str,
    job_id: str,
    position: str = "center",
    font_size: int = 48,
    font_color: str = "white",
    font_name: str = "Arial",
    start_time: float = 0.0,
    end_time: float | None = None,
    fade_in: float = 0.5,
    fade_out: float = 0.5,
    output_filename: str = "overlay.mp4",
) -> str:
    """Add a text overlay with fade animation to a video.

    Args:
        video_path: Input video.
        text: Text to display.
        job_id: Workspace job ID.
        position: 'center', 'top', 'bottom', 'top-left', 'bottom-right', etc.
        font_size: Text size.
        font_color: FFmpeg colour name or hex (e.g. 'white', '0xFFFFFF').
        font_name: Font family name.
        start_time: When to show text (seconds from start).
        end_time: When to hide text (None = until end of video).
        fade_in: Fade-in duration in seconds.
        fade_out: Fade-out duration in seconds.
        output_filename: Name of the output file.
    """
    output_path = get_job_path(job_id, output_filename)

    # Position mapping
    x_expr, y_expr = _get_position_expr(position, font_size)

    # Build alpha expression for fade in/out
    if end_time is not None:
        alpha_expr = (
            f"if(lt(t\\,{start_time})\\,0\\,"
            f"if(lt(t\\,{start_time + fade_in})\\,(t-{start_time})/{fade_in}\\,"
            f"if(gt(t\\,{end_time - fade_out})\\,({end_time}-t)/{fade_out}\\,"
            f"if(gt(t\\,{end_time})\\,0\\,1))))"
        )
    else:
        # Fade in, then stay. No fade-out (stays until end).
        alpha_expr = (
            f"if(lt(t\\,{start_time})\\,0\\,"
            f"if(lt(t\\,{start_time + fade_in})\\,(t-{start_time})/{fade_in}\\,1))"
        )

    # Escape text for drawtext
    escaped_text = text.replace("'", "'\\''").replace(":", "\\:")

    drawtext = (
        f"drawtext=text='{escaped_text}'"
        f":fontfile='':fontsize={font_size}:fontcolor={font_color}"
        f":font='{font_name}'"
        f":x={x_expr}:y={y_expr}"
        f":alpha='{alpha_expr}'"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", video_path,
        "-vf", drawtext,
        "-c:v", "libx264",
        "-preset", "fast",
        "-crf", "23",
        "-c:a", "copy",
        output_path,
    ]
    _run_ffmpeg(cmd, operation="text overlay")
    return output_path


def _get_position_expr(position: str, font_size: int) -> tuple[str, str]:
    """Map position name to FFmpeg drawtext x/y expressions."""
    margin = 40
    positions = {
        "center":       ("(w-text_w)/2", "(h-text_h)/2"),
        "top":          ("(w-text_w)/2", str(margin)),
        "bottom":       ("(w-text_w)/2", f"h-text_h-{margin}"),
        "top-left":     (str(margin), str(margin)),
        "top-right":    (f"w-text_w-{margin}", str(margin)),
        "bottom-left":  (str(margin), f"h-text_h-{margin}"),
        "bottom-right": (f"w-text_w-{margin}", f"h-text_h-{margin}"),
    }
    return positions.get(position, positions["center"])


def extract_audio(video_path: str, job_id: str) -> str:
    """Extract audio track from a video file as MP3."""
    output_path = get_job_path(job_id, "extracted_audio.mp3")
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-vn",
        "-acodec",
        "libmp3lame",
        "-b:a",
        "192k",
        output_path,
    ]
    _run_ffmpeg(cmd, operation="audio extraction")
    return output_path


def replace_audio(video_path: str, audio_path: str, job_id: str) -> str:
    """Replace a video's audio track with a different audio file."""
    basename = Path(video_path).stem
    output_path = get_job_path(job_id, f"replaced_{basename}_{int(time.time())}.mp4")
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-i",
        audio_path,
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-map",
        "0:v:0",
        "-map",
        "1:a:0",
        "-shortest",
        output_path,
    ]
    _run_ffmpeg(cmd, operation="audio replacement")
    return output_path


def mix_audio_layers(layers: list[dict], job_id: str) -> str:
    """Mix multiple audio layers with per-layer volume control, fades, and delay.

    Each layer dict:
        path:     str   — audio file path (required)
        volume:   float — 0.0-1.0, default 1.0
        fade_in:  float — fade-in seconds, default 0 (no fade)
        fade_out: float — fade-out seconds, default 0 (no fade)
        delay:    float — delay before layer starts in seconds, default 0
    """
    output_path = get_job_path(job_id, "mixed_audio.mp3")

    inputs = []
    filter_parts = []
    for i, layer in enumerate(layers):
        inputs.extend(["-i", layer["path"]])

        chain = []
        vol = layer.get("volume", 1.0)
        chain.append(f"volume={vol}")

        fade_in = layer.get("fade_in", 0)
        if fade_in > 0:
            chain.append(f"afade=t=in:d={fade_in}")

        fade_out = layer.get("fade_out", 0)
        if fade_out > 0:
            chain.append(f"afade=t=out:d={fade_out}")

        delay_ms = int(layer.get("delay", 0) * 1000)
        if delay_ms > 0:
            chain.append(f"adelay={delay_ms}|{delay_ms}")

        filter_parts.append(f"[{i}:a]{','.join(chain)}[a{i}]")

    mix_inputs = "".join(f"[a{i}]" for i in range(len(layers)))
    filter_str = ";".join(filter_parts) + f";{mix_inputs}amix=inputs={len(layers)}:duration=longest[out]"

    cmd = (
        ["ffmpeg", "-y"]
        + inputs
        + [
            "-filter_complex",
            filter_str,
            "-map",
            "[out]",
            "-acodec",
            "libmp3lame",
            "-b:a",
            "192k",
            output_path,
        ]
    )
    _run_ffmpeg(cmd, operation="audio mixing")
    return output_path
