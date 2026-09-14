from ...schemas.patient import PatientState
from .question_engine import QUESTIONS, get_next_missing_field


def generate_question(state: PatientState) -> str | None:
    """
    Generate the next patient-friendly question.

    The question engine decides which field is missing.
    This function decides how to phrase the question.

    Returns None when the core intake is complete.
    """

    missing_field = get_next_missing_field(state)

    if missing_field is None:
        return None

    return QUESTIONS[missing_field]

