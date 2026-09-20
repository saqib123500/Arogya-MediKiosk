from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from ..patient_form import staff_required
from myapp.models import Patient, Doctor, Token
from myapp.utils import generate_token

@staff_required
def staff_dashboard(request):
    """
    Staff Dashboard: Manage patients, assign doctors, and monitor tokens.
    """
    today = timezone.localdate()
    patients = Patient.objects.prefetch_related('tokens').all().order_by('-created_at')
    doctors = Doctor.objects.filter(is_active=True)

    # Attach latest token to each patient for the table
    for p in patients:
        p.latest_token = p.tokens.order_by('-created_at').first()

    # Fetch today's tokens that are waiting
    todays_tokens = (
        Token.objects
        .filter(date=today, status="waiting")
        .select_related("doctor", "patient")
        .order_by("token_number")
    )

    return render(
        request,
        "myapp/staff_dashboard.html",
        {
            "patients": patients,
            "doctors": doctors,
            "todays_tokens": todays_tokens,
            "waiting_count": todays_tokens.count(),
        }
    )

@staff_required
def assign_doctor(request, pk):
    """
    View to manually assign a doctor to a patient and generate a token.
    """
    patient = get_object_or_404(Patient, pk=pk)
    doctors = Doctor.objects.filter(is_active=True)

    if request.method == "POST":
        doctor_id = request.POST.get("doctor_id")
        if not doctor_id:
            messages.error(request, "Please select a doctor.")
            return render(request, "myapp/assign_doctor.html", {"patient": patient, "doctors": doctors})

        doctor = get_object_or_404(Doctor, pk=doctor_id, is_active=True)

        # Cancel existing active tokens for this patient to avoid duplicates
        Token.objects.filter(patient=patient, status="active").update(status="cancelled")

        # Generate new token
        token = generate_token(patient, doctor)

        messages.success(request, f"Patient {patient.name} assigned to Dr. {doctor.name}. Token #{token.token_number} generated.")
        return redirect("myapp:staff_dashboard")

    return render(request, "myapp/assign_doctor.html", {
        "patient": patient,
        "doctors": doctors
    })

