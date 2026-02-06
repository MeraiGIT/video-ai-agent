from faster_whisper import WhisperModel
from config import settings
from utils.file_manager import get_job_path
from utils.srt import write_srt

_model = None


def _get_model() -> WhisperModel:
    """Lazy-load the Whisper model as a singleton."""
    global _model
    if _model is None:
        _model = WhisperModel(
            settings.WHISPER_MODEL_SIZE,
            compute_type="int8",
        )
    return _model


def transcribe_to_srt(audio_path: str, job_id: str) -> str:
    """Transcribe audio to SRT subtitle file with word-level timestamps."""
    model = _get_model()
    segments, _info = model.transcribe(audio_path, word_timestamps=True)
    # segments is a generator, must be consumed
    segments_list = list(segments)
    srt_path = get_job_path(job_id, "captions.srt")
    write_srt(segments_list, srt_path)
    return srt_path
