from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.contrib.auth.models import User
from myapp.models import Patient, Token, Doctor, PatientHistory, MedicalDocument
from myapp.forms import PatientForm, PatientRegistrationForm
from myapp.utils import assign_doctor, generate_token

from django.contrib.auth import login
from django.db.models import Q, Prefetch
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache
from django.utils.dateparse import parse_datetime
from django.db import transaction
from functools import wraps

from django.http import JsonResponse
from django.shortcuts import get_object_or_404

from myapp.models import PatientHistory
def visit_history_info(request, history_id):

    history = get_object_or_404(
        PatientHistory.objects.select_related(
            "patient",
            "token__doctor",
            "token__prescription",
        ),
        id=history_id,
    )

    patient = history.patient
    token = history.token

    visit_data = history.visit_data or {}
    dashavidha = visit_data.get("dashavidha", {})
    

    # ---------------------------------------------------------
    # DOCTOR
    # ---------------------------------------------------------

    doctor_name = None

    if token and token.doctor:
        doctor_name = token.doctor.name


    # ---------------------------------------------------------
    # TRIAGE
    # ---------------------------------------------------------

    triage = {}

    if token:

        triage = {
            "level": token.triage_level,
            "recommendation":
                token.triage_recommendation,
        }


    # ---------------------------------------------------------
    # PRESCRIPTION
    # ---------------------------------------------------------

    prescription_data = None

    if token:

        try:

            prescription = token.prescription

            prescription_data = {
                "diagnosis":
                    prescription.diagnosis,

                "notes":
                    prescription.notes,

                "items": [
                    {
                        "medicine_name":
                            item.medicine_name,

                        "dosage":
                            item.dosage,

                        "timing":
                            item.timing,

                        "duration":
                            item.duration,
                    }

                    for item in prescription.items.all()
                ],
            }

        except Exception:

            prescription_data = None


    # ---------------------------------------------------------
    # RESPONSE
    # ---------------------------------------------------------

    return JsonResponse({
    "success": True,

    "visit_date": history.visit_date.strftime(
        "%d %B %Y, %I:%M %p"
    ),

    "patient": {
        "name": patient.name,
        "age": patient.age,
        "gender": patient.get_gender_display(),
        "phone": patient.phone_number,
    },

    "doctor": doctor_name,

    "token": {
        "number": token.token_number if token else None,
        "date": token.date.strftime("%d %b %Y") if token else None,
        "status": token.get_status_display() if token else None,
    },

    "dashavidha": dashavidha,

    "visit": {
        "complaint": history.complaint,
        "symptoms": history.symptoms or [],
        "other_symptoms": history.other_symptoms,
        "fever_temperature": history.fever_temperature,
        "fever_duration": history.fever_duration,
    },

    "visit_data": visit_data,

    "triage": triage,

    "prescription": prescription_data,
})

def staff_required(view):
    """Allow ONLY front-desk staff. Block patients and doctors."""

    # Apply never_cache to prevent browser from caching protected staff views
    view = never_cache(view)

    @wraps(view)
    def wrapped_view(request, *args, **kwargs):
        # 1. Must be logged in
        if not request.user.is_authenticated:
            return redirect("myapp:staff_login")

        # 2. Must be marked as staff in Django Admin
        if not request.user.is_staff:
            messages.error(request, "Access denied. This portal is for staff only.")
            return redirect("myapp:staff_login")

        if hasattr(request.user, "patient_profile"):
            return redirect("myapp:patient_form")

        if hasattr(request.user, "doctor_profile"):
            return redirect("myapp:doctor_dashboard")

        return view(request, *args, **kwargs)

    return wrapped_view


def _symptoms_redirect(request, patient_id):
    url = reverse(
        "myapp:symptoms",
        kwargs={"patient_id": patient_id}
    )
    return HttpResponseRedirect(url)


def _patient_form(request, pk=None, public_registration=False):

    patient = get_object_or_404(
        Patient,
        pk=pk
    ) if pk else None

    initial_data = {}

    verified_abha = request.session.pop(
        "verified_abha_number",
        None
    )

    if verified_abha and not pk:
        initial_data["abha_number"] = verified_abha

    current_token = (
        patient.tokens.order_by("-created_at").first()
        if patient
        else None
    )

    doctors = Doctor.objects.filter(
        is_active=True
    )

    if request.method == "POST":

        form_class = (
            PatientRegistrationForm
            if public_registration and not patient
            else PatientForm
        )

        form = form_class(
            request.POST,
            instance=patient
        )

        if form.is_valid():

            patient_user = None

            with transaction.atomic():

                saved_patient = form.save(
                    commit=False
                )

                # Handle user account creation/updates
                username = form.cleaned_data.get("username")
                password = form.cleaned_data.get("password")
                
                if public_registration:
                    # Public registration always creates a new user
                    if username and password:
                        patient_user = User.objects.create_user(
                            username=username,
                            password=password,
                        )
                        saved_patient.user = patient_user
                else:
                    # Staff form - handle user account if credentials provided
                    if username and password:
                        # Create new user account
                        if not saved_patient.user:
                            patient_user = User.objects.create_user(
                                username=username,
                                password=password,
                            )
                            saved_patient.user = patient_user
                        else:
                            # Update existing user
                            saved_patient.user.username = username
                            saved_patient.user.set_password(password)
                            saved_patient.user.save()
                    elif username and saved_patient.user:
                        # Update username only
                        saved_patient.user.username = username
                        saved_patient.user.save()

                saved_patient.save()

            if not pk:

                # If this is a new patient account,
                # automatically log the patient in.
                if patient_user:
                    login(
                        request,
                        patient_user
                    )

                if not request.user.is_authenticated:
                    request.session[
                        "patient_flow_id"
                    ] = saved_patient.id

                # Automatically assign a doctor.
                doctor = assign_doctor(
                    saved_patient
                )

                if doctor:
                    generate_token(
                        saved_patient,
                        doctor
                    )
                else:
                    messages.warning(
                        request,
                        "Patient saved, but no doctor is available right now."
                    )

                return _symptoms_redirect(
                    request,
                    saved_patient.id
                )

            else:

                # Editing an existing patient.
                selected_doctor_id = request.POST.get(
                    "doctor"
                )

                if selected_doctor_id:

                    selected_doctor = get_object_or_404(
                        Doctor,
                        pk=selected_doctor_id
                    )

                    if (
                        not current_token
                        or current_token.doctor_id
                        != selected_doctor.id
                    ):

                        new_token = generate_token(
                            saved_patient,
                            selected_doctor
                        )

                        messages.success(
                            request,
                            f"Reassigned to Dr. "
                            f"{selected_doctor.name} "
                            f"— new token #{new_token.token_number}"
                        )

                if not request.user.is_authenticated:
                    request.session[
                        "patient_flow_id"
                    ] = saved_patient.id

                return _symptoms_redirect(
                    request,
                    saved_patient.id
                )

    else:

        form_class = (
            PatientRegistrationForm
            if public_registration and not patient
            else PatientForm
        )

        form = form_class(
            instance=patient,
            initial=initial_data
        )

    return render(
        request,
        "myapp/patient_form.html",
        {
            "form": form,
            "patient": patient,
            "doctors": doctors,
            "current_token": current_token,
            "public_registration": public_registration,
            "base_template": (
                "myapp/public_base.html"
                if public_registration
                else "myapp/base.html"
            ),
        }
    )


@never_cache
def patient_form(request, pk=None):

    # -------------------------------------------------
    # LOGGED-IN PATIENT
    # -------------------------------------------------
    if (
        request.user.is_authenticated
        and hasattr(request.user, "patient_profile")
    ):

        patient = request.user.patient_profile

        # Patient should always work with their own record.
        if pk is not None and pk != patient.id:
            return redirect(
                "myapp:patient_form"
            )

        return _patient_form(
            request,
            pk=patient.id
        )

    # -------------------------------------------------
    # DOCTOR
    # -------------------------------------------------
    if (
        request.user.is_authenticated
        and hasattr(request.user, "doctor_profile")
    ):
        return redirect(
            "myapp:doctor_dashboard"
        )

    # -------------------------------------------------
    # STAFF
    # -------------------------------------------------
    return _patient_form(
        request,
        pk=pk
    )


def patient_registration(request):
    """
    Public registration page that creates
    a patient account.
    """

    return _patient_form(
        request,
        public_registration=True
    )


@never_cache
def patient_dashboard(request):
    

    if not request.user.is_authenticated:
        return redirect(
            "myapp:patient_login"
        )

    if not hasattr(
        request.user,
        "patient_profile"
    ):
        return redirect(
            "myapp:patient_login"
        )

    patient = request.user.patient_profile

    # ---------------------------------------------------------
    # SYMPTOM LABELS
    # ---------------------------------------------------------

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

    # ---------------------------------------------------------
    # SYMPTOMS
    # ---------------------------------------------------------

    symptom_record = getattr(
        patient,
        "symptom_record",
        None
    )

    selected_symptom_ids = (
        list(symptom_record.non_pain_symptoms)
        if symptom_record
        else []
    )

    if symptom_record:
        selected_symptom_ids += list(
            symptom_record.pain_symptoms.values_list(
                "location",
                flat=True
            )
        )

    # ---------------------------------------------------------
    # MEDICAL DOCUMENTS
    #
    # Only show documents that contain meaningful
    # extracted medical information.
    # ---------------------------------------------------------

    significant_fields = {
        "diagnosis",
        "symptoms",
        "medications",
        "allergies",
        "vital_signs",
        "lab_results",
        "imaging_findings",
        "clinical_findings",
        "impression",
        "recommendations",
        "other_significant_information",
    }

    def has_meaningful_value(value):
        """
        Recursively checks whether a value actually contains
        useful information.

        Empty strings, empty lists, empty dictionaries,
        None and whitespace-only values are ignored.
        """

        if value is None:
            return False

        if isinstance(value, str):
            return bool(value.strip())

        if isinstance(value, dict):
            return any(
                has_meaningful_value(v)
                for v in value.values()
            )

        if isinstance(value, (list, tuple, set)):
            return any(
                has_meaningful_value(item)
                for item in value
            )

        return True

    useful_medical_documents = []

    all_medical_documents = (
        patient.medical_documents
        .order_by("-uploaded_at")
    )

    for doc in all_medical_documents:

        structured_data = getattr(
            doc,
            "structured_data",
            None
        )

        # structured_data must be a dictionary
        if not isinstance(
            structured_data,
            dict
        ):
            continue

        # Check only fields that are actually
        # considered significant medical information.
        has_useful_information = any(
            field in structured_data
            and has_meaningful_value(
                structured_data.get(field)
            )
            for field in significant_fields
        )

        if has_useful_information:
            useful_medical_documents.append(doc)

    # ---------------------------------------------------------
    # DASHBOARD
    # ---------------------------------------------------------

    return render(
        request,
        "myapp/patient_dashboard.html",
        {
            "patient": patient,

            "tokens": patient.tokens.select_related(
                "doctor"
            ).order_by(
                "-created_at"
            ),

            "history": PatientHistory.objects.filter(
                patient=patient
            ).order_by(
                "-visit_date"
            ),

            # IMPORTANT:
            # Only useful medical documents are sent
            # to the template.
            "medical_documents": useful_medical_documents,

            "selected_symptoms": [
                symptom_labels.get(
                    symptom_id,
                    symptom_id
                )
                for symptom_id in selected_symptom_ids
            ],

            "dashavidha": [
                (
                    "Prakriti",
                    patient.get_prakriti_display()
                ),
                (
                    "Vikriti",
                    patient.get_vikriti_display()
                ),
                (
                    "Sara",
                    patient.get_sara_display()
                ),
                (
                    "Samhanana",
                    patient.get_samhanana_display()
                ),
                (
                    "Pramana",
                    patient.get_pramana_display()
                ),
                (
                    "Satmya",
                    patient.get_satmya_display()
                ),
                (
                    "Satva",
                    patient.get_satva_display()
                ),
                (
                    "Ahara Shakti",
                    patient.get_ahara_shakti_display()
                ),
                (
                    "Vyayama Shakti",
                    patient.get_vyayama_shakti_display()
                ),
                (
                    "Vaya",
                    patient.get_vaya_display()
                ),
            ],
        }
    )

@staff_required
def token_confirmation(request, token_id):

    token = get_object_or_404(
        Token,
        pk=token_id
    )

    return render(
        request,
        "myapp/token_confirmation.html",
        {
            "token": token
        }
    )


@staff_required
def patient_list(request):

    search_query = request.GET.get(
        "q",
        ""
    ).strip()

    active_tokens = Token.objects.filter(
        status="waiting"
    ).select_related(
        "doctor"
    ).order_by(
        "-created_at"
    )

    latest_tokens = Token.objects.select_related(
        "doctor"
    ).order_by(
        "-created_at"
    )

    patients = Patient.objects.prefetch_related(
        Prefetch(
            "tokens",
            queryset=active_tokens,
            to_attr="active_tokens"
        ),
        Prefetch(
            "tokens",
            queryset=latest_tokens,
            to_attr="latest_tokens"
        ),
    )

    doctors = Doctor.objects.filter(
        is_active=True
    )

    if search_query:

        patients = patients.filter(
            Q(name__icontains=search_query)
            | Q(phone_number__icontains=search_query)
        )

    patients = patients.order_by(
        "-created_at"
    )

    is_ajax = (
        request.headers.get(
            "X-Requested-With"
        ) == "XMLHttpRequest"
    )

    if is_ajax:

        return render(
            request,
            "myapp/_patient_table.html",
            {
                "patients": patients
            }
        )

    return render(
        request,
        "myapp/patient_list.html",
        {
            "patients": patients,
            "search_query": search_query,
            "doctors": doctors,
        }
    )


@staff_required
def index(request):

    total_patients = Patient.objects.count()

    recent_patients = Patient.objects.all().order_by(
        "-created_at"
    )[:5]

    return render(
        request,
        "myapp/index.html",
        {
            "total_patients": total_patients,
            "recent_patients": recent_patients,
        }
    )


@staff_required
@require_POST
def book_appointment_ajax(request, pk):

    patient = get_object_or_404(
        Patient,
        pk=pk
    )

    doctor_id = request.POST.get(
        "doctor_id"
    )

    appointment_dt_raw = request.POST.get(
        "appointment_datetime"
    )

    if not doctor_id:
        return JsonResponse(
            {
                "success": False,
                "error": "Please select a doctor."
            },
            status=400
        )

    if not appointment_dt_raw:
        return JsonResponse(
            {
                "success": False,
                "error": "Please select a date and time."
            },
            status=400
        )

    doctor = get_object_or_404(
        Doctor,
        pk=doctor_id,
        is_active=True
    )

    appointment_dt = parse_datetime(
        appointment_dt_raw
    )

    if appointment_dt is None:
        return JsonResponse(
            {
                "success": False,
                "error": "Invalid date/time format."
            },
            status=400
        )

    if timezone.is_naive(
        appointment_dt
    ):
        appointment_dt = timezone.make_aware(
            appointment_dt
        )

    if appointment_dt < timezone.now():

        return JsonResponse(
            {
                "success": False,
                "error": "Appointment time cannot be in the past."
            },
            status=400
        )

    existing_active = Token.objects.filter(
        patient=patient,
        status="active"
    )

    was_rebooking = existing_active.exists()

    existing_active.update(
        status="cancelled"
    )

    token = generate_token(
        patient,
        doctor
    )

    token.appointment_datetime = appointment_dt

    token.save(
        update_fields=[
            "appointment_datetime"
        ]
    )

    action_word = (
        "Rebooked"
        if was_rebooking
        else "Booked"
    )

    return JsonResponse(
        {
            "success": True,
            "message": (
                f"{action_word} — "
                f"{doctor.name}, "
                f"Token #{token.token_number}"
            ),
            "token_id": token.id,
            "token_number": token.token_number,
            "doctor_name": doctor.name,
            "appointment_datetime": appointment_dt.strftime(
                "%d %b %Y, %I:%M %p"
            ),
        }
    )


@staff_required
def patient_tokens_ajax(
    request,
    patient_id
):

    patient = get_object_or_404(
        Patient,
        pk=patient_id
    )

    tokens = Token.objects.filter(
        patient=patient
    ).select_related(
        "doctor"
    ).order_by(
        "-created_at"
    )

    symptom_record = getattr(
        patient,
        "symptom_record",
        None
    )

    pain_symptoms = (
        symptom_record.pain_symptoms.all()
        if symptom_record
        else []
    )

    history = PatientHistory.objects.filter(
        patient=patient
    ).order_by(
        "-visit_date"
    )

    return render(
        request,
        "myapp/_patient_tokens_modal.html",
        {
            "patient": patient,
            "tokens": tokens,
            "symptom_record": symptom_record,
            "pain_symptoms": pain_symptoms,
            "history": history,
        }
    )
    
# Update to /Users/mohammadsaqib/Arogya-MediKiosk/myapp/patient_form.py


@staff_required
def patient_detail(request, pk):
    """
    Detailed view of patient credentials for staff.
    """
    patient = get_object_or_404(
        Patient.objects.prefetch_related(
            "symptom_record__pain_symptoms"
        ),
        pk=pk
    )

    # Map symptom IDs to labels
    symptom_labels_map = {
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

    # Pre-process general symptoms into labels
    display_symptoms = []
    if hasattr(patient, "symptom_record"):
        for s_id in patient.symptom_record.non_pain_symptoms:
            display_symptoms.append(symptom_labels_map.get(s_id, s_id))

    return render(request, "myapp/patient_detail.html", {
        "patient": patient,
        "display_symptoms": display_symptoms
    })
    
def patient_form_view(request):
    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('myapp:symptoms_form')
