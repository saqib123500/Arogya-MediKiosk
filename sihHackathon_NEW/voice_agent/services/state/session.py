from ...schemas.patient import PatientState

SESSION_KEY = "patient_state"
INTERVIEW_STATUS_KEY = "interview_status"

STATUS_NEW = "new"
STATUS_IN_PROGRESS = "in_progress"
STATUS_COMPLETED = "completed"



def get_patient_state(request) -> PatientState:
    """
    Get the current patient state from the Django session.

    If no patient state exists, return a new empty PatientState.
    """

    state_data = request.session.get(SESSION_KEY)

    if not state_data:
        return PatientState()

    return PatientState(**state_data)


def save_patient_state(
    request,
    state: PatientState,
) -> None:
    """
    Save the current patient state to the Django session.
    """

    request.session[SESSION_KEY] = state.model_dump()

    # Explicitly mark the session as modified.
    request.session.modified = True


def clear_patient_state(request) -> None:
    """
    Clear the current patient state from the Django session.
    """

    request.session.pop(SESSION_KEY, None)
    request.session.modified = True
    
def get_interview_status(request) -> str:
    """
    Get the current interview status.
    """

    return request.session.get(
        INTERVIEW_STATUS_KEY,
        STATUS_NEW,
    )


def save_interview_status(
    request,
    status: str,
) -> None:
    """
    Save the current interview status.
    """

    request.session[INTERVIEW_STATUS_KEY] = status
    request.session.modified = True


def reset_interview(request) -> None:
    """
    Reset the patient state and interview status.
    """

    request.session.pop(SESSION_KEY, None)
    request.session.pop(INTERVIEW_STATUS_KEY, None)
    request.session.modified = True