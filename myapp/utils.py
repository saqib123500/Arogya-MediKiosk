from django.utils import timezone
from myapp.models import Doctor, Token
from django.db import IntegrityError, transaction

# Your Prakriti field allows combined types (e.g. "vata_pitta") — we match
# on the first-listed dosha as the primary constitution, and route
# "tridoshaja" (balanced/all three) to a General Physician.
PRAKRITI_TO_SPECIALTY = {
    "vata": "vata",
    "pitta": "pitta",
    "kapha": "kapha",
    "vata_pitta": "vata",
    "pitta_kapha": "pitta",
    "vata_kapha": "vata",
    "tridoshaja": "general",
}

def assign_doctor(patient):
    specialty = PRAKRITI_TO_SPECIALTY.get(patient.prakriti, "general")
    doctor = Doctor.objects.filter(specialty=specialty, is_active=True).first()
    if not doctor:
        # fallback if no matching specialist is available
        doctor = Doctor.objects.filter(specialty="general", is_active=True).first()
    return doctor

def generate_token(patient, doctor, appointment_datetime=None):
    today = timezone.localdate()
    token_date = appointment_datetime.date() if appointment_datetime else today

    for _ in range(5):
        try:
            with transaction.atomic():
                last_token = (
                    Token.objects
                    .filter(doctor=doctor, date=token_date)
                    .order_by("-token_number")
                    .first()
                )

                next_number = (
                    last_token.token_number + 1
                    if last_token
                    else 1
                )

                return Token.objects.create(
                    patient=patient,
                    doctor=doctor,
                    token_number=next_number,
                    date=token_date,
                    appointment_datetime=appointment_datetime,
                )

        except IntegrityError:
            # Another request created the same token number.
            # Retry and get the new latest token.
            continue

    raise IntegrityError(
        "Could not generate a unique token after multiple attempts."
    )