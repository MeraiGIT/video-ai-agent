from elevenlabs.client import ElevenLabs
from elevenlabs import save
from config import settings
from utils.file_manager import get_job_path

client = ElevenLabs(api_key=settings.ELEVENLABS_API_KEY)


def generate_tts(text: str, job_id: str) -> str:
    """Generate voiceover audio from text using ElevenLabs."""
    audio = client.text_to_speech.convert(
        voice_id=settings.ELEVENLABS_VOICE_ID,
        text=text,
        model_id="eleven_multilingual_v2",
        output_format="mp3_44100_128",
    )
    output_path = get_job_path(job_id, "voiceover.mp3")
    save(audio, output_path)
    return output_path
