from voice_agent.schemas.patient import PatientState
from voice_agent.services.state.manager import apply_updates
from voice_agent.services.state.question_engine import (
    get_missing_fields,
    get_next_question,
)


# Start with an empty patient
state = PatientState()

print("Initial state:")
print(state)


# Simulate information extracted from the patient's speech
updates = {
    "FullName": "Rahul",
    "Age": 24,
}

state = apply_updates(state, updates)

print("\nAfter first update:")
print(state)

print("\nMissing fields:")
print(get_missing_fields(state))

print("\nNext question:")
print(get_next_question(state))


# Simulate the patient providing more information
updates = {
    "Gender": "Male",
    "Chief_Complaint": "Headache for three days",
}

state = apply_updates(state, updates)

print("\nAfter second update:")
print(state)

print("\nMissing fields:")
print(get_missing_fields(state))

print("\nNext question:")
print(get_next_question(state))


# Simulate a correction
updates = {
    "Age": 25,
}

state = apply_updates(state, updates)

print("\nAfter age correction:")
print(state)