import os

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from django.test import RequestFactory
from voice_agent.schemas.patient import PatientState
from voice_agent.services.state.session import (
    get_patient_state,
    save_patient_state,
    clear_patient_state,
)


# Create a fake Django request
factory = RequestFactory()
request = factory.get("/voice/")

# Attach a session to the request
from django.contrib.sessions.middleware import SessionMiddleware

middleware = SessionMiddleware(lambda request: None)
middleware.process_request(request)
request.session.save()


# Start with an empty patient
state = PatientState()

print("Initial state:")
print(state)


# Save patient information
state = PatientState(
    FullName="Rahul",
    Age=24,
)

save_patient_state(request, state)

# Retrieve it again
loaded_state = get_patient_state(request)

print("\nLoaded state:")
print(loaded_state)


# Test that the values survived
assert loaded_state.FullName == "Rahul"
assert loaded_state.Age == 24

print("\n✅ Session state test passed!")


# Test clearing the state
clear_patient_state(request)

cleared_state = get_patient_state(request)

print("\nAfter clearing:")
print(cleared_state)

assert cleared_state.FullName is None
assert cleared_state.Age is None

print("\n✅ Session clear test passed!")

