from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from django.views.decorators.cache import never_cache
from myapp.models import Patient, Doctor, Token, Prescription, PrescriptionItem, PatientHistory, Symptom
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
 

@login_required
@never_cache
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
@never_cache
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
    
    # Get symptom information
    symptom_record = getattr(patient, "symptom_record", None)
    symptoms_data = None
    
    if symptom_record:
        symptom_labels = {
            "fever": "Fever",
            "dizziness": "Dizziness",
            "weakness": "Weakness",
            "tiredness": "Tiredness",
            "cough": "Cough",
            "cold": "Cold",
            "nausea": "Nausea",
            "vomiting": "Vomiting",
            "diarrhea": "Diarrhea",
            "breathingDifficulty": "Breathing Difficulty",
            "itching": "Itching",
            "skinRash": "Skin Rash",
            "headache": "Headache",
            "chestPain": "Chest Pain",
            "stomachPain": "Stomach Pain",
            "backPain": "Back Pain",
            "jointPain": "Joint Pain",
            "musclePain": "Muscle Pain",
            "soreThroat": "Sore Throat",
        }
        
        selected_symptom_ids = symptom_record.non_pain_symptoms if symptom_record else []
        
        if symptom_record:
            selected_symptom_ids += list(
                symptom_record.pain_symptoms.values_list("location", flat=True)
            )
        
        symptoms_data = [
            symptom_labels.get(symptom_id, symptom_id)
            for symptom_id in selected_symptom_ids
        ]
    
    # Get dashavidha information
    dashavidha = [
        ("Prakriti", patient.get_prakriti_display()),
        ("Vikriti", patient.get_vikriti_display()),
        ("Sara", patient.get_sara_display()),
        ("Samhanana", patient.get_samhanana_display()),
        ("Pramana", patient.get_pramana_display()),
        ("Satmya", patient.get_satmya_display()),
        ("Satva", patient.get_satva_display()),
        ("Ahara Shakti", patient.get_ahara_shakti_display()),
        ("Vyayama Shakti", patient.get_vyayama_shakti_display()),
        ("Vaya", patient.get_vaya_display()),
    ]
 
    return render(request, "myapp/_patient_visit_history_modal.html", {
        "patient": patient,
        "tokens": tokens,
        "history": history,
        "symptoms_data": symptoms_data,
        "dashavidha": dashavidha,
    })
 