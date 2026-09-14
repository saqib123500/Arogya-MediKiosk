import base64

from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

from .services.state.question_engine import get_initial_question
from .services.stt import transcribe_audio
from .services.tts import synthesize_speech
from .services.state.controller import process_patient_message

from .services.state.session import (
    get_patient_state,
    save_patient_state,
    reset_interview,
)


def voice_agent(request):
    current_state = get_patient_state(request)

    return render(
        request,
        "voice_agent/index.html",
        {
            "initial_question": get_initial_question(current_state),
        },
    )


@csrf_exempt
def process_voice(request):
    if request.method != "POST":
        return JsonResponse(
            {"error": "Only POST requests are allowed."},
            status=405,
        )

    audio_file = request.FILES.get("audio")

    if not audio_file:
        return JsonResponse(
            {"error": "No audio file received."},
            status=400,
        )

    try:
        # 1. Convert patient's audio to text.
        transcript = transcribe_audio(audio_file)

        # 2. Load the patient's existing state.
        current_state = get_patient_state(request)

        # 3. Extract information and update the state.
        updated_state, updates, next_question, is_complete = (
            process_patient_message(
                transcript,
                current_state,
            )
        )

        # 4. Save the updated state.
        save_patient_state(
            request,
            updated_state,
        )

        # 5. Use the next question as the assistant response.
        response_text = next_question

        # 6. If there are no more core questions,
        # tell the patient that the basic intake is complete.
        if response_text is None:
            response_text = (
                "Thank you. I have collected the basic information "
                "for your intake."
            )

        # 7. Convert the assistant response to speech.
        audio_bytes = synthesize_speech(response_text)

        audio_base64 = base64.b64encode(
            audio_bytes
        ).decode("utf-8")

        return JsonResponse(
            {
                "transcript": transcript,
                "response": response_text,
                "updates": updates,
                "state": updated_state.model_dump(),
                "audio": audio_base64,
                "audio_type": "audio/mpeg",
                "is_complete": is_complete,
            }
        )

    except Exception as e:
        return JsonResponse(
            {"error": str(e)},
            status=500,
        )


@csrf_exempt
def reset_interview_view(request):
    """
    Start a completely new patient interview.
    """

    if request.method != "POST":
        return JsonResponse(
            {"error": "Only POST requests are allowed."},
            status=405,
        )

    reset_interview(request)

    state = get_patient_state(request)

    return JsonResponse(
        {
            "message": "Interview reset successfully.",
            "initial_question": get_initial_question(state),
            "state": state.model_dump(),
        }
    )
    
    