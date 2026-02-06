import subprocess
from utils.file_manager import get_job_path


def _run_ffmpeg(cmd: list[str]):
    """Run an FFmpeg command and raise on failure."""
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"FFmpeg failed (exit {result.returncode}):\n{result.stderr}"
        )


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
    _run_ffmpeg(cmd)
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
    _run_ffmpeg(cmd)
    return output_path


def burn_subtitles(
    video_path: str, srt_path: str, job_id: str
) -> str:
    """Burn SRT subtitles into the video.

    Uses the subtitles filter with forced styling for consistent look.
    """
    output_path = get_job_path(job_id, "final.mp4")

    # Escape special characters in path for FFmpeg subtitles filter
    escaped_srt = srt_path.replace("\\", "\\\\").replace(":", "\\:").replace("'", "\\'")

    style = (
        "FontSize=22,PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,Outline=2,"
        "BackColour=&H80000000,Shadow=0,"
        "Alignment=2,MarginV=30,"
        "FontName=Arial"
    )

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        video_path,
        "-vf",
        f"subtitles={escaped_srt}:force_style='{style}'",
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
    _run_ffmpeg(cmd)
    return output_path
