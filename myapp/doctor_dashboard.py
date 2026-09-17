from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from myapp.models import Patient, Doctor, Token, Prescription, PrescriptionItem, PatientHistory
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
 

@login_required
def doctor_dashboard(request):

    # Check whether the logged-in user has a Doctor profile
    if not hasattr(request.user, "doctor_profile"):
        return redirect("myapp:index")

    doctor = request.user.doctor_profile

    # Prevent inactive doctors from accessing the dashboard
    if not doctor.is_active:
        return redirect("myapp:index")

    today = timezone.localdate()

    # Today's tokens for this doctor
    todays_tokens = (
        Token.objects
        .filter(
            doctor=doctor,
            date=today
        )
        .select_related("patient")
        .order_by("token_number")
    )

    # Waiting and seen counts
    waiting_count = todays_tokens.filter(status="waiting").count()
    seen_count = todays_tokens.filter(status="seen").count()
    total_today = todays_tokens.count()

    # All patients
    total_patients = Patient.objects.count()

    # Recent prescriptions written by this doctor
    recent_prescriptions = (
        Prescription.objects
        .filter(doctor=doctor)
        .select_related("patient", "token")
        .order_by("-created_at")[:5]
    )

    context = {
        "doctor": doctor,
        "today": today,
        "todays_tokens": todays_tokens,
        "waiting_count": waiting_count,
        "seen_count": seen_count,
        "total_today": total_today,
        "total_patients": total_patients,
        "recent_prescriptions": recent_prescriptions,
    }

    return render(
        request,
        "myapp/doctor_dashboard.html",
        context
    )

@login_required
@require_POST
def prescribe_token_ajax(request, token_id):
    if not hasattr(request.user, "doctor_profile"):
        return JsonResponse({"success": False, "error": "Not authorized."}, status=403)

    doctor = request.user.doctor_profile
    token = get_object_or_404(Token, pk=token_id, doctor=doctor)

    if hasattr(token, "prescription"):
        return JsonResponse({"success": False, "error": "This token already has a prescription."}, status=400)

    diagnosis = request.POST.get("diagnosis", "").strip()
    notes = request.POST.get("notes", "").strip()

    medicine_names = request.POST.getlist("medicine_name[]")
    dosages = request.POST.getlist("dosage[]")
    timings = request.POST.getlist("timing[]")
    durations = request.POST.getlist("duration[]")

    items_to_create = []
    for i, name in enumerate(medicine_names):
        name = name.strip()
        if not name:
            continue
        items_to_create.append({
            "medicine_name": name,
            "dosage": dosages[i].strip() if i < len(dosages) else "",
            "timing": timings[i].strip() if i < len(timings) else "",
            "duration": durations[i].strip() if i < len(durations) else "",
        })

    if not items_to_create:
        return JsonResponse({"success": False, "error": "Add at least one medicine."}, status=400)

    with transaction.atomic():
        prescription = Prescription.objects.create(
            token=token,
            patient=token.patient,
            doctor=doctor,
            diagnosis=diagnosis,
            notes=notes,
        )

        PrescriptionItem.objects.bulk_create([
            PrescriptionItem(prescription=prescription, **item) for item in items_to_create
        ])

        token.status = "seen"
        token.save(update_fields=["status"])

    return JsonResponse({
        "success": True,
        "message": f"Prescription saved for {token.patient.name}.",
        "token_id": token.id,
    })



@login_required
def patient_visit_history_ajax(request, patient_id):
    if not hasattr(request.user, "doctor_profile"):
        return JsonResponse({"success": False, "error": "Not authorized."}, status=403)
 
    patient = get_object_or_404(Patient, pk=patient_id)
 
    tokens = (
        Token.objects
        .filter(patient=patient)
        .select_related("doctor")
        .prefetch_related("prescription__items")
        .order_by("-created_at")
    )

    history = PatientHistory.objects.filter(
        patient=patient
    ).order_by("-visit_date")
 
    return render(request, "myapp/_patient_visit_history_modal.html", {
        "patient": patient,
        "tokens": tokens,
        "history": history,
    })
 