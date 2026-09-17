import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from myapp.models import Patient, Symptom, PainSymptom, PatientHistory


def symptoms_form(request, patient_id):
    if (
        not request.user.is_authenticated
        and request.session.get("patient_flow_id") != patient_id
    ):
        return redirect("myapp:patient_login")

    patient = get_object_or_404(Patient, pk=patient_id)
    current_token = patient.tokens.order_by('-created_at').first()

    return render(request, 'myapp/symptoms.html', {
        'patient': patient,
        'current_token': current_token,
    })


@require_POST
def save_symptoms(request, patient_id):
    if (
        not request.user.is_authenticated
        and request.session.get("patient_flow_id") != patient_id
    ):
        return JsonResponse(
            {"success": False, "error": "Patient session has expired."},
            status=403,
        )

    patient = get_object_or_404(Patient, pk=patient_id)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"success": False, "error": "Invalid JSON"}, status=400)

    symptom_record, _ = Symptom.objects.update_or_create(
        patient=patient,
        defaults={
            "non_pain_symptoms": data.get("non_pain_symptoms", []),
            "fever_temperature": data.get("fever_temperature", ""),
            "fever_duration": data.get("fever_duration", ""),
            "other_symptoms": data.get("other_symptoms", ""),
            "language": data.get("language", ""),
        }
    )

    symptom_record.pain_symptoms.all().delete()

    for location, socrates in data.get("pain_symptoms", {}).items():
        PainSymptom.objects.create(
            symptom_record=symptom_record,
            location=location,
            site=socrates.get("S1", ""),
            onset=socrates.get("O", ""),
            character=socrates.get("C", ""),
            radiation=socrates.get("R", ""),
            associations=socrates.get("A", ""),
            time_course=socrates.get("T", ""),
            exacerbating_relieving=socrates.get("E", ""),
            severity=socrates.get("S2", ""),
        )

    PatientHistory.objects.create(
        patient=patient,
        complaint=patient.complaint,
        symptoms=data.get("non_pain_symptoms", []),
        other_symptoms=data.get("other_symptoms", ""),
        fever_temperature=data.get("fever_temperature", ""),
        fever_duration=data.get("fever_duration", ""),
    )    

    current_token = patient.tokens.order_by('-created_at').first()

    return JsonResponse({
        "success": True,
        "token_id": current_token.id if current_token else None,
    })
