from ...schemas.patient import PatientState


INITIAL_QUESTION = "Hello! What is your full name?"


CORE_FIELDS = [
    "FullName",
    "Age",
    "Gender",
    "Contact_Number",
    "Address",
    "Chief_Complaint",
]


QUESTIONS = {
    "FullName": "What is your full name?",
    "Age": "How old are you?",
    "Gender": "What is your gender?",
    "Contact_Number": "What is your contact number?",
    "Address": "What is your address?",
    "Chief_Complaint": "What health problem are you experiencing today?",
}


def get_missing_fields(state: PatientState) -> list[str]:
    """
    Return all required core fields that have not
    yet been collected.
    """

    return [
        field
        for field in CORE_FIELDS
        if getattr(state, field) is None
    ]


def get_next_missing_field(state: PatientState) -> str | None:
    """
    Select the first missing core field.

    Fields already present in PatientState are skipped.
    """

    missing_fields = get_missing_fields(state)

    if not missing_fields:
        return None

    return missing_fields[0]


def get_next_question(state: PatientState) -> str | None:
    """
    Return a question for the next missing field.

    Returns None when all core fields are complete.
    """

    next_field = get_next_missing_field(state)

    if next_field is None:
        return None

    return QUESTIONS[next_field]


def get_initial_question(state: PatientState) -> str | None:
    """
    Return the first question only when starting
    a completely new interview.
    """

    if state.FullName is None:
        return INITIAL_QUESTION

    return None

