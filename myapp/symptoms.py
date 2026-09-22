import json
import requests

from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction

from myapp.models import (
    Patient,
    Symptom,
    PainSymptom,
    PatientHistory,
)


# =============================================================
# SYMPTOMS FORM
# =============================================================

def symptoms_form(request, patient_id):

    # ---------------------------------------------------------
    # AUTHENTICATED PATIENT
    # ---------------------------------------------------------

    if (
        request.user.is_authenticated
        and hasattr(request.user, "patient_profile")
        and request.user.patient_profile.id != patient_id
    ):
        return redirect("myapp:patient_dashboard")

    # ---------------------------------------------------------
    # SESSION-BASED PATIENT FLOW
    # ---------------------------------------------------------

    if (
        not request.user.is_authenticated
        and request.session.get("patient_flow_id") != patient_id
    ):
        return redirect("myapp:patient_login")

    # ---------------------------------------------------------
    # GET PATIENT
    # ---------------------------------------------------------

    patient = get_object_or_404(
        Patient,
        pk=patient_id,
    )

    # ---------------------------------------------------------
    # CURRENT TOKEN
    # ---------------------------------------------------------

    current_token = (
        patient.tokens
        .order_by("-created_at")
        .first()
    )

    # ---------------------------------------------------------
    # RENDER PAGE
    # ---------------------------------------------------------

    return render(
        request,
        "myapp/symptoms.html",
        {
            "patient": patient,
            "current_token": current_token,
        },
    )


# =============================================================
# SAVE SYMPTOMS
# =============================================================

@require_POST
def save_symptoms(request, patient_id):

    # ---------------------------------------------------------
    # AUTHENTICATION / SESSION CHECK
    # ---------------------------------------------------------

    if (
        request.user.is_authenticated
        and hasattr(request.user, "patient_profile")
        and request.user.patient_profile.id != patient_id
    ):
        return JsonResponse(
            {
                "success": False,
                "error": (
                    "You are not authorized to save symptoms "
                    "for this patient."
                ),
            },
            status=403,
        )

    if (
        not request.user.is_authenticated
        and request.session.get("patient_flow_id") != patient_id
    ):
        return JsonResponse(
            {
                "success": False,
                "error": "Patient session expired.",
            },
            status=403,
        )

    # ---------------------------------------------------------
    # GET PATIENT
    # ---------------------------------------------------------

    patient = get_object_or_404(
        Patient,
        pk=patient_id,
    )

    # ---------------------------------------------------------
    # READ JSON
    # ---------------------------------------------------------

    try:

        data = json.loads(request.body)

    except json.JSONDecodeError:

        return JsonResponse(
            {
                "success": False,
                "error": "Invalid JSON data.",
            },
            status=400,
        )

    # ---------------------------------------------------------
    # CURRENT TOKEN
    # ---------------------------------------------------------

    current_token = (
        patient.tokens
        .order_by("-created_at")
        .first()
    )

    # =========================================================
    # READ NEW FRONTEND FORMAT
    # =========================================================

    complaint = str(
        data.get("complaint", "")
    ).strip()

    non_pain_symptoms = data.get(
        "symptoms",
        [],
    )

    if not isinstance(
        non_pain_symptoms,
        list,
    ):
        non_pain_symptoms = []

    other_symptoms = str(
        data.get(
            "other_symptoms",
            "",
        )
    ).strip()

    fever_temperature = str(
        data.get(
            "fever_temperature",
            "",
        )
    ).strip()

    fever_duration = str(
        data.get(
            "fever_duration",
            "",
        )
    ).strip()

    # =========================================================
    # PAIN
    # =========================================================

    pain_data = data.get(
        "pain"
    )

    if not isinstance(
        pain_data,
        dict,
    ):
        pain_data = {}

    has_pain = (
        pain_data.get(
            "has_pain",
            False,
        )
        is True
    )

    pain_location = str(
        pain_data.get(
            "location",
            "",
        )
    ).strip()

    socrates = pain_data.get(
        "socrates",
        {}
    )

    if not isinstance(
        socrates,
        dict,
    ):
        socrates = {}

    # ---------------------------------------------------------
    # CREATE INTERNAL PAIN STRUCTURE
    #
    # This preserves compatibility with your existing
    # PatientHistory / dashboard structure.
    # ---------------------------------------------------------

    pain_symptoms = {}

    if has_pain and pain_location:

        pain_symptoms[pain_location] = {

            "S1": socrates.get(
                "site",
                "",
            ),

            "O": socrates.get(
                "onset",
                "",
            ),

            "C": socrates.get(
                "character",
                "",
            ),

            "R": socrates.get(
                "radiation",
                "",
            ),

            "A": socrates.get(
                "associated_symptoms",
                "",
            ),

            "T": socrates.get(
                "timing",
                "",
            ),

            "E": socrates.get(
                "exacerbating_relieving",
                "",
            ),

            "S2": socrates.get(
                "severity",
                0,
            ),
        }

    # =========================================================
    # NRS PAIN
    # =========================================================

    nrs_pain = socrates.get(
        "severity"
    )

    if nrs_pain in (
        None,
        "",
    ):
        nrs_pain = None

    # =========================================================
    # VITALS
    #
    # The current symptoms page does not collect vitals yet.
    # Keep these as None so your existing model structure
    # remains compatible.
    # =========================================================

    sbp = data.get("sbp")
    dbp = data.get("dbp")
    hr = data.get("hr")
    rr = data.get("rr")
    saturation = data.get("saturation")

    # =========================================================
    # SAVE EVERYTHING
    # =========================================================

    with transaction.atomic():

        # -----------------------------------------------------
        # SYMPTOM RECORD
        # -----------------------------------------------------

        symptom_record, created = (
            Symptom.objects.update_or_create(

                patient=patient,

                defaults={

                    "non_pain_symptoms":
                        non_pain_symptoms,

                    "fever_temperature":
                        fever_temperature,

                    "fever_duration":
                        fever_duration,

                    "other_symptoms":
                        other_symptoms,

                    "language":
                        data.get(
                            "language",
                            "",
                        ),

                    "sbp":
                        sbp,

                    "dbp":
                        dbp,

                    "hr":
                        hr,

                    "rr":
                        rr,

                    "saturation":
                        saturation,
                },
            )
        )

        # -----------------------------------------------------
        # REMOVE OLD PAIN RECORDS
        # -----------------------------------------------------

        symptom_record.pain_symptoms.all().delete()

        # -----------------------------------------------------
        # SAVE NEW PAIN RECORD
        # -----------------------------------------------------

        if has_pain and pain_location:

            PainSymptom.objects.create(

                symptom_record=symptom_record,

                location=pain_location,

                site=socrates.get(
                    "site",
                    "",
                ),

                onset=socrates.get(
                    "onset",
                    "",
                ),

                character=socrates.get(
                    "character",
                    "",
                ),

                radiation=socrates.get(
                    "radiation",
                    "",
                ),

                associations=socrates.get(
                    "associated_symptoms",
                    "",
                ),

                time_course=socrates.get(
                    "timing",
                    "",
                ),

                exacerbating_relieving=socrates.get(
                    "exacerbating_relieving",
                    "",
                ),

                severity=(
                    socrates.get(
                        "severity",
                        0,
                    )
                ),
            )

        # =====================================================
        # PATIENT HISTORY
        # =====================================================

        history = PatientHistory.objects.create(

            patient=patient,

            token=current_token,

            # IMPORTANT:
            # Use the complaint submitted on the symptoms page.
            complaint=complaint,

            symptoms=non_pain_symptoms,

            other_symptoms=other_symptoms,

            fever_temperature=fever_temperature,

            fever_duration=fever_duration,

            visit_data={

                # =============================================
                # PATIENT
                # =============================================

                "patient": {

                    "name":
                        patient.name,

                    "age":
                        patient.age,

                    "gender":
                        patient.get_gender_display(),

                    "phone_number":
                        patient.phone_number,
                },

                # =============================================
                # DASHAVIDHA
                # =============================================

                "dashavidha": {

                    "prakriti":
                        patient.get_prakriti_display(),

                    "vikriti":
                        patient.get_vikriti_display(),

                    "sara":
                        patient.get_sara_display(),

                    "samhanana":
                        patient.get_samhanana_display(),

                    "pramana":
                        patient.get_pramana_display(),

                    "satmya":
                        patient.get_satmya_display(),

                    "satva":
                        patient.get_satva_display(),

                    "ahara_shakti":
                        patient.get_ahara_shakti_display(),

                    "vyayama_shakti":
                        patient.get_vyayama_shakti_display(),

                    "vaya":
                        patient.get_vaya_display(),
                },

                # =============================================
                # COMPLAINT
                # =============================================

                "complaint":
                    complaint,

                # =============================================
                # GENERAL SYMPTOMS
                # =============================================

                "symptoms":
                    non_pain_symptoms,

                # =============================================
                # OTHER SYMPTOMS
                # =============================================

                "other_symptoms":
                    other_symptoms,

                # =============================================
                # FEVER
                # =============================================

                "fever": {

                    "temperature":
                        fever_temperature,

                    "duration":
                        fever_duration,
                },

                # =============================================
                # PAIN
                # =============================================

                "pain": {

                    "has_pain":
                        has_pain,

                    "location":
                        pain_location,

                    "socrates":
                        socrates,
                },

                # =============================================
                # COMPATIBILITY WITH OLD STRUCTURE
                # =============================================

                "pain_symptoms":
                    pain_symptoms,

                # =============================================
                # VITALS
                # =============================================

                "vitals": {

                    "sbp":
                        sbp,

                    "dbp":
                        dbp,

                    "hr":
                        hr,

                    "rr":
                        rr,

                    "saturation":
                        saturation,
                },

                # =============================================
                # NRS PAIN
                # =============================================

                "nrs_pain":
                    nrs_pain,
            },
        )

    # =========================================================
    # TRIAGE
    # =========================================================

    if current_token:

        try:

            # -------------------------------------------------
            # GENDER
            # -------------------------------------------------

            gender = (
                str(
                    patient.gender
                ).lower()
                if patient.gender
                else ""
            )

            if gender == "male":

                sex = 1

            elif gender == "female":

                sex = 2

            else:

                sex = 2

            # -------------------------------------------------
            # PAIN
            # -------------------------------------------------

            pain_present = (
                has_pain
                and bool(pain_location)
            )

            # -------------------------------------------------
            # TEMPERATURE
            # -------------------------------------------------

            temperature = (
                symptom_record.fever_temperature
            )

            try:

                bt = float(
                    temperature
                )

            except (
                TypeError,
                ValueError,
            ):

                bt = 36.6

            # -------------------------------------------------
            # NRS
            # -------------------------------------------------

            try:

                triage_nrs = (
                    float(nrs_pain)
                    if nrs_pain is not None
                    else 0
                )

            except (
                TypeError,
                ValueError,
            ):

                triage_nrs = 0

            # -------------------------------------------------
            # TRIAGE PAYLOAD
            # -------------------------------------------------

            triage_payload = {

                "age":
                    patient.age,

                "sex":
                    sex,

                "mental":
                    1,

                "pain":
                    1
                    if pain_present
                    else 0,

                "nrs_pain":
                    triage_nrs,

                "sbp":
                    symptom_record.sbp or 120,

                "dbp":
                    symptom_record.dbp or 80,

                "hr":
                    symptom_record.hr or 75,

                "rr":
                    symptom_record.rr or 18,

                "bt":
                    bt,

                "saturation":
                    symptom_record.saturation or 98,
            }

            # -------------------------------------------------
            # TRIAGE API
            # -------------------------------------------------

            response = requests.post(

                "http://localhost:8001/predict",

                json=triage_payload,

                timeout=2,
            )

            # -------------------------------------------------
            # SAVE TRIAGE
            # -------------------------------------------------

            if response.status_code == 200:

                result = response.json()

                current_token.triage_level = (
                    result.get(
                        "priority_level"
                    )
                )

                current_token.triage_recommendation = (
                    result.get(
                        "description"
                    )
                )

                current_token.save(
                    update_fields=[
                        "triage_level",
                        "triage_recommendation",
                    ]
                )

        except Exception as e:

            print(
                f"Triage API Error: {e}"
            )

    # =========================================================
    # SUCCESS
    # =========================================================

    return JsonResponse(
        {
            "success": True,

            "history_id":
                history.id,

            "token_id":
                (
                    current_token.id
                    if current_token
                    else None
                ),
        }
    )