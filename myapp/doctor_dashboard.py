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
@login_required
@never_cache
def doctor_dashboard(request):

    # ---------------------------------------------------------
    # CHECK DOCTOR PROFILE
    # ---------------------------------------------------------

    if not hasattr(request.user, "doctor_profile"):
        return redirect("myapp:index")

    doctor = request.user.doctor_profile

    # ---------------------------------------------------------
    # CHECK DOCTOR ACTIVE STATUS
    # ---------------------------------------------------------

    if not doctor.is_active:
        return redirect("myapp:index")

    # ---------------------------------------------------------
    # TODAY
    # ---------------------------------------------------------

    today = timezone.localdate()

    # ---------------------------------------------------------
    # TODAY'S PATIENT TOKENS
    # ---------------------------------------------------------
    # Also load the patient's symptom record so that the
    # prescribe popup can display vital signs.
    # ---------------------------------------------------------

    todays_tokens = (
        Token.objects
        .filter(
            doctor=doctor,
            date=today
        )
        .select_related(
            "patient",
            "patient__symptom_record",
        )
        .order_by("token_number")
    )

    # ---------------------------------------------------------
    # STATISTICS
    # ---------------------------------------------------------

    waiting_count = todays_tokens.filter(
        status="waiting"
    ).count()

    seen_count = todays_tokens.filter(
        status="seen"
    ).count()

    total_today = todays_tokens.count()

    # ---------------------------------------------------------
    # TOTAL REGISTERED PATIENTS
    # ---------------------------------------------------------

    total_patients = Patient.objects.count()

    # ---------------------------------------------------------
    # RECENT PRESCRIPTIONS
    # ---------------------------------------------------------

    recent_prescriptions = (
        Prescription.objects
        .filter(doctor=doctor)
        .select_related(
            "patient",
            "token",
        )
        .prefetch_related(
            "items"
        )
        .order_by("-created_at")[:5]
    )

    # ---------------------------------------------------------
    # CONTEXT
    # ---------------------------------------------------------

    context = {
        "doctor": doctor,
        "today": today,
        "todays_tokens": todays_tokens,

        "waiting_count": waiting_count,
        "seen_count": seen_count,
        "total_today": total_today,
        "total_patients": total_patients,

        "recent_prescriptions":
            recent_prescriptions,
    }

    # ---------------------------------------------------------
    # RENDER
    # ---------------------------------------------------------

    return render(
        request,
        "myapp/doctor_dashboard.html",
        context
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
@login_required
@require_POST
def prescribe_token_ajax(request, token_id):

    # ---------------------------------------------------------
    # DOCTOR AUTHORIZATION
    # ---------------------------------------------------------

    if not hasattr(request.user, "doctor_profile"):
        return JsonResponse(
            {
                "success": False,
                "error": "Not authorized."
            },
            status=403
        )

    doctor = request.user.doctor_profile

    # ---------------------------------------------------------
    # GET TOKEN
    # ---------------------------------------------------------

    token = get_object_or_404(
        Token,
        pk=token_id,
        doctor=doctor
    )

    # ---------------------------------------------------------
    # PREVENT DUPLICATE PRESCRIPTION
    # ---------------------------------------------------------

    if hasattr(token, "prescription"):
        return JsonResponse(
            {
                "success": False,
                "error": "This token already has a prescription."
            },
            status=400
        )

    # ---------------------------------------------------------
    # DIAGNOSIS / NOTES
    # ---------------------------------------------------------

    diagnosis = request.POST.get(
        "diagnosis",
        ""
    ).strip()

    notes = request.POST.get(
        "notes",
        ""
    ).strip()

    # ---------------------------------------------------------
    # VITAL SIGNS TAKEN BY DOCTOR
    # ---------------------------------------------------------

    sbp = request.POST.get(
        "sbp",
        ""
    ).strip()

    dbp = request.POST.get(
        "dbp",
        ""
    ).strip()

    hr = request.POST.get(
        "hr",
        ""
    ).strip()

    rr = request.POST.get(
        "rr",
        ""
    ).strip()

    saturation = request.POST.get(
        "saturation",
        ""
    ).strip()

    # ---------------------------------------------------------
    # MEDICINES
    # ---------------------------------------------------------

    medicine_names = request.POST.getlist(
        "medicine_name[]"
    )

    dosages = request.POST.getlist(
        "dosage[]"
    )

    timings = request.POST.getlist(
        "timing[]"
    )

    durations = request.POST.getlist(
        "duration[]"
    )

    # ---------------------------------------------------------
    # PREPARE MEDICINES
    # ---------------------------------------------------------

    items_to_create = []

    for i, name in enumerate(medicine_names):

        name = name.strip()

        if not name:
            continue

        items_to_create.append(
            {
                "medicine_name": name,

                "dosage":
                    dosages[i].strip()
                    if i < len(dosages)
                    else "",

                "timing":
                    timings[i].strip()
                    if i < len(timings)
                    else "",

                "duration":
                    durations[i].strip()
                    if i < len(durations)
                    else "",
            }
        )

    # ---------------------------------------------------------
    # REQUIRE AT LEAST ONE MEDICINE
    # ---------------------------------------------------------

    if not items_to_create:
        return JsonResponse(
            {
                "success": False,
                "error": "Add at least one medicine."
            },
            status=400
        )

    # =========================================================
    # SAVE EVERYTHING
    # =========================================================

    with transaction.atomic():

    

        symptom_record, created = Symptom.objects.get_or_create(
        patient=token.patient
    )

    symptom_record.sbp = sbp or None
    symptom_record.dbp = dbp or None
    symptom_record.hr = hr or None
    symptom_record.rr = rr or None
    symptom_record.saturation = saturation or None

    symptom_record.save(
        update_fields=[
            "sbp",
            "dbp",
            "hr",
            "rr",
            "saturation",
        ]
    )


    # -----------------------------------------------------
    # SAVE PRESCRIPTION
    # -----------------------------------------------------

    prescription = Prescription.objects.create(
        token=token,
        patient=token.patient,
        doctor=doctor,
        diagnosis=diagnosis,
        notes=notes,
    )


    # -----------------------------------------------------
    # SAVE MEDICINES
    # -----------------------------------------------------

    PrescriptionItem.objects.bulk_create([
        PrescriptionItem(
            prescription=prescription,
            **item
        )
        for item in items_to_create
    ])


    # -----------------------------------------------------
    # UPDATE PATIENT HISTORY SNAPSHOT
    # -----------------------------------------------------

    history = (
        PatientHistory.objects
        .filter(
            patient=token.patient,
            token=token,
        )
        .order_by("-visit_date")
        .first()
    )

    if history:

        visit_data = history.visit_data or {}

        visit_data["vitals"] = {
            "sbp": sbp or None,
            "dbp": dbp or None,
            "hr": hr or None,
            "rr": rr or None,
            "saturation": saturation or None,
        }

        history.visit_data = visit_data

        history.save(
            update_fields=[
                "visit_data"
            ]
        )


    # -----------------------------------------------------
    # MARK TOKEN AS SEEN
    # -----------------------------------------------------

    token.status = "seen"

    token.save(
        update_fields=[
            "status"
        ]
    )

    # ---------------------------------------------------------
    # SUCCESS
    # ---------------------------------------------------------

    return JsonResponse(
        {
            "success": True,

            "message":
                f"Prescription saved for "
                f"{token.patient.name}.",

            "token_id":
                token.id,
        }
    )


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
 