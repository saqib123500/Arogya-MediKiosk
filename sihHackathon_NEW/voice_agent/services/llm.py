import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")
)

SYSTEM_PROMPT = """
You are a friendly AI patient-intake assistant.

Your job in this Phase 1 prototype is to have a natural, concise conversation
with the patient.

Rules:
- Ask simple questions that are easy to answer verbally.
- Keep responses short because they will be converted to speech.
- Do not diagnose medical conditions.
- Do not invent patient information.
- If the patient gives useful information, acknowledge it naturally.
- If the patient's answer is unclear, ask a simple clarification question.
- Support multilingual and code-switched conversations when possible.
"""


def generate_response(transcript):
    """
    Generate the assistant's response from the patient's transcript.
    """

    response = client.responses.create(
        model="gpt-5.6-luna",
        instructions=SYSTEM_PROMPT,
        input=transcript,
    )

    return response.output_text.strip()