from ...schemas.patient import PatientState


def apply_updates(
    current_state: PatientState,
    updates: dict,
) -> PatientState:
    """
    Apply extracted patient information to the current state.

    Only fields present in `updates` are changed.
    Existing information is preserved.
    """

    updated_data = current_state.model_dump()

    for field, value in updates.items():
        if field in PatientState.model_fields and value is not None:
            updated_data[field] = value

    return PatientState(**updated_data)