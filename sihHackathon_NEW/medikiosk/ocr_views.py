import os
import tempfile

from django.shortcuts import render, redirect, get_object_or_404

from .models import Patient, MedicalDocument
from .forms import MedicalDocumentUploadForm
from .ocr.pipeline import MedicalDocumentPipeline


# ============================================================
# MEDICAL DOCUMENT UPLOAD + OCR
# ============================================================

def medical_document_upload(request):

    # --------------------------------------------------------
    # GET CURRENT PATIENT
    # --------------------------------------------------------

    patient_id = request.session.get("patient_id")

    if not patient_id:
        return redirect("patient_form")

    patient = get_object_or_404(
        Patient,
        id=patient_id
    )

    # --------------------------------------------------------
    # HANDLE DOCUMENT UPLOAD
    # --------------------------------------------------------

    if request.method == "POST":

        form = MedicalDocumentUploadForm(
            request.POST,
            request.FILES
        )

        if form.is_valid():

            uploaded_file = form.cleaned_data["document"]

            # ------------------------------------------------
            # CREATE MEDICAL DOCUMENT
            # ------------------------------------------------

            medical_document = MedicalDocument.objects.create(
                patient=patient,
                document=uploaded_file
            )

            # ------------------------------------------------
            # CREATE TEMPORARY FILE FOR OCR
            # ------------------------------------------------

            temporary_file = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=os.path.splitext(
                    uploaded_file.name
                )[1]
            )

            try:

                # --------------------------------------------
                # WRITE UPLOADED FILE TO TEMPORARY FILE
                # --------------------------------------------

                for chunk in uploaded_file.chunks():
                    temporary_file.write(chunk)

                temporary_file.close()

                # --------------------------------------------
                # RUN OCR PIPELINE
                # --------------------------------------------

                pipeline = MedicalDocumentPipeline()

                result = pipeline.process(
                    temporary_file.name
                )

                # --------------------------------------------
                # DISPLAY OCR RESULT IN TERMINAL
                # --------------------------------------------

                print(
                    "\n========== DJANGO OCR RESULT =========="
                )

                print("RAW TEXT:")
                print(result["raw_text"])

                print("STRUCTURED DATA:")
                print(result["structured_data"])

                print(
                    "=======================================\n"
                )

                # --------------------------------------------
                # SAVE OCR RESULT
                # --------------------------------------------

                medical_document.raw_text = result["raw_text"]

                medical_document.structured_data = (
                    result["structured_data"]
                )

                # --------------------------------------------
                # SAVE DOCUMENT TYPE
                # --------------------------------------------

                medical_document.document_type = (
                    result["structured_data"]
                    .get("document", {})
                    .get("document_type", "")
                )

                medical_document.save()

                # --------------------------------------------
                # SEND STRUCTURED DATA TO REVIEW PAGE
                # --------------------------------------------

                return render(
                    request,
                    "medikiosk/patient/medical_review.html",
                    {
                        "structured_data": result[
                            "structured_data"
                        ],
                        "medical_document": medical_document,
                    }
                )

            finally:

                # --------------------------------------------
                # DELETE TEMPORARY OCR FILE
                # --------------------------------------------

                if os.path.exists(
                    temporary_file.name
                ):
                    os.remove(
                        temporary_file.name
                    )

    else:

        form = MedicalDocumentUploadForm()

    # --------------------------------------------------------
    # DISPLAY UPLOAD PAGE
    # --------------------------------------------------------

    return render(
        request,
        "medikiosk/patient/medical_upload_documents.html",
        {
            "form": form,
            "patient": patient,
        }
    )


# ============================================================
# MEDICAL DOCUMENT CONFIRMATION
# ============================================================

def medical_document_confirm(request):

    # --------------------------------------------------------
    # ONLY ACCEPT POST REQUEST
    # --------------------------------------------------------

    if request.method != "POST":
        return redirect("medical_documents")

    # --------------------------------------------------------
    # GET MEDICAL DOCUMENT ID
    # --------------------------------------------------------

    document_id = request.POST.get(
        "document_id"
    )

    if not document_id:
        return redirect("medical_documents")

    # --------------------------------------------------------
    # GET MEDICAL DOCUMENT
    # --------------------------------------------------------

    medical_document = get_object_or_404(
        MedicalDocument,
        id=document_id
    )

    # --------------------------------------------------------
    # GET EXISTING STRUCTURED DATA
    # --------------------------------------------------------

    structured_data = medical_document.structured_data

    # ========================================================
    # DOCUMENT INFORMATION
    # ========================================================

    document_data = structured_data.get(
        "document",
        {}
    )

    if "document_type" in request.POST:
        document_data["document_type"] = request.POST.get(
            "document_type"
        )

    if "report_date" in request.POST:
        document_data["report_date"] = request.POST.get(
            "report_date"
        )

    if "doctor" in request.POST:
        document_data["doctor"] = request.POST.get(
            "doctor"
        )

    if "hospital" in request.POST:
        document_data["hospital"] = request.POST.get(
            "hospital"
        )

    if "department" in request.POST:
        document_data["department"] = request.POST.get(
            "department"
        )

    structured_data["document"] = document_data

    # ========================================================
    # PATIENT INFORMATION
    # ========================================================

    patient_data = structured_data.get(
        "patient",
        {}
    )

    if "patient_name" in request.POST:
        patient_data["name"] = request.POST.get(
            "patient_name"
        )

    if "patient_age" in request.POST:
        patient_data["age"] = request.POST.get(
            "patient_age"
        )

    if "patient_date_of_birth" in request.POST:
        patient_data["date_of_birth"] = request.POST.get(
            "patient_date_of_birth"
        )

    if "patient_gender" in request.POST:
        patient_data["gender"] = request.POST.get(
            "patient_gender"
        )

    if "patient_abha_id" in request.POST:
        patient_data["abha_id"] = request.POST.get(
            "patient_abha_id"
        )

    if "patient_phone" in request.POST:
        patient_data["phone"] = request.POST.get(
            "patient_phone"
        )

    if "patient_address" in request.POST:
        patient_data["address"] = request.POST.get(
            "patient_address"
        )

    if "patient_blood_group" in request.POST:
        patient_data["blood_group"] = request.POST.get(
            "patient_blood_group"
        )

    structured_data["patient"] = patient_data

    # ========================================================
    # CHIEF COMPLAINT
    # ========================================================

    if "chief_complaint" in request.POST:
        structured_data["chief_complaint"] = request.POST.get(
            "chief_complaint"
        )

    # ========================================================
    # LIST FIELDS
    # ========================================================

    structured_data["medical_history"] = (
        request.POST.getlist(
            "medical_history"
        )
    )

    structured_data["surgical_history"] = (
        request.POST.getlist(
            "surgical_history"
        )
    )

    structured_data["allergies"] = (
        request.POST.getlist(
            "allergies"
        )
    )

    structured_data["medications"] = (
        request.POST.getlist(
            "medications"
        )
    )

    structured_data["diagnoses"] = (
        request.POST.getlist(
            "diagnoses"
        )
    )

    structured_data["clinical_observations"] = (
        request.POST.getlist(
            "clinical_observations"
        )
    )

    structured_data["follow_up"] = (
        request.POST.getlist(
            "follow_up"
        )
    )

    # ========================================================
    # VITALS
    # ========================================================

    vitals = structured_data.get(
        "vitals",
        {}
    )

    if "blood_pressure" in request.POST:
        vitals["blood_pressure"] = request.POST.get(
            "blood_pressure"
        )

    if "pulse" in request.POST:
        vitals["pulse"] = request.POST.get(
            "pulse"
        )

    if "temperature" in request.POST:
        vitals["temperature"] = request.POST.get(
            "temperature"
        )

    if "respiratory_rate" in request.POST:
        vitals["respiratory_rate"] = request.POST.get(
            "respiratory_rate"
        )

    if "oxygen_saturation" in request.POST:
        vitals["oxygen_saturation"] = request.POST.get(
            "oxygen_saturation"
        )

    if "height" in request.POST:
        vitals["height"] = request.POST.get(
            "height"
        )

    if "weight" in request.POST:
        vitals["weight"] = request.POST.get(
            "weight"
        )

    if "bmi" in request.POST:
        vitals["bmi"] = request.POST.get(
            "bmi"
        )

    structured_data["vitals"] = vitals

    # ========================================================
    # SAVE CONFIRMED INFORMATION
    # ========================================================

    medical_document.structured_data = structured_data

    medical_document.is_confirmed = True

    medical_document.save()

    # ========================================================
    # REDIRECT TO MEDICAL DOCUMENTS
    # ========================================================

    return redirect(
        "medical_documents"
    )