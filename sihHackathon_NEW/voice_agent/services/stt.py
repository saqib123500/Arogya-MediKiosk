import os

from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def transcribe_audio(audio_file):
    """
    Convert recorded patient audio into text.
    """

    audio_bytes = audio_file.read()

    transcription = client.audio.transcriptions.create(
        model="gpt-4o-mini-transcribe",
        file=(
            audio_file.name,
            audio_bytes,
            audio_file.content_type,
        ),
    )

    return transcription.text