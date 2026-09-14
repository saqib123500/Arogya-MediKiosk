from ...schemas.patient import PatientState
from .manager import apply_updates
from .question_engine import get_next_question
from .updater import extract_state_updates


def process_patient_message(
    patient_message: str,
    current_state: PatientState,
) -> tuple[PatientState, dict, str | None, bool]:
    """
    Process one patient message.

    Returns:
        updated_state
        state_updates
        next_question
        is_complete
    """

    # 1. Extract information from the patient's message.
    updates = extract_state_updates(
        patient_message,
        current_state,
    )

    # 2. Apply the extracted information.
    updated_state = apply_updates(
        current_state,
        updates,
    )

    # 3. Determine the next question.
    next_question = get_next_question(
        updated_state,
    )

    # 4. Determine whether the core intake is complete.
    is_complete = next_question is None

    return (
        updated_state,
        updates,
        next_question,
        is_complete,
    )
    
