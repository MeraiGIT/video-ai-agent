"""Audio mixing capability — wraps ffmpeg_service.mix_audio_layers."""

import logging

logger = logging.getLogger(__name__)


def execute(params: dict, state: dict, ctx: dict) -> dict:
    """Mix multiple audio tracks with volume and fade control.

    params:
        layers: list[dict] — each with {path, volume, fade_in, fade_out, delay}
    """
    layers = params.get("layers", [])
    if not layers:
        # Auto-build from state
        built_layers = []
        vo = state.get("voiceover_path", "")
        music = state.get("music_path", "")
        if vo:
            built_layers.append({"path": vo, "volume": 1.0, "fade_in": 0.0, "fade_out": 0.0, "delay": 0.0})
        if music:
            built_layers.append({"path": music, "volume": 0.3, "fade_in": 1.0, "fade_out": 1.0, "delay": 0.0})
        for sfx in state.get("sfx_paths", []):
            built_layers.append({"path": sfx, "volume": 0.8, "fade_in": 0.0, "fade_out": 0.0, "delay": 0.0})
        layers = built_layers

    if not layers:
        raise ValueError("No audio layers to mix")

    job_id = state.get("job_id", "unknown")

    from services.ffmpeg_service import mix_audio_layers
    path = mix_audio_layers(layers, job_id)

    return {
        "path": path,
        "model": "ffmpeg",
        "cost": 0.0,
    }
