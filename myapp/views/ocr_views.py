import os

from paddleocr import PaddleOCR
from pdf2image import convert_from_path

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from myapp.models import Patient, MedicalDocument

from myapp.services.medical_extractor import (
    extract_significant_information
)


# ---------------------------------------------------------
# PADDLE OCR
# ---------------------------------------------------------

ocr = PaddleOCR(
    lang="en"
)


def preprocess_image(image_path):
    """
    Improve image quality before sending it to PaddleOCR.
    """

    image = Image.open(image_path)

    # Convert to grayscale
    image = ImageOps.grayscale(image)

    # Upscale image
    width, height = image.size

    image = image.resize(
        (width * 2, height * 2),
        Image.Resampling.LANCZOS
    )

    # Improve contrast
    image = ImageEnhance.Contrast(image).enhance(1.8)

    # Sharpen text
    image = ImageEnhance.Sharpness(image).enhance(2.0)

    # Remove small noise
    image = image.filter(
        ImageFilter.MedianFilter(size=3)
    )

    return image


def extract_text_from_image(image_path):
    """
    Preprocess an image and extract text using PaddleOCR.
    """

    processed_image = preprocess_image(
        image_path
    )

    # Save temporary processed image
    processed_path = f"{image_path}_processed.png"

    processed_image.save(
        processed_path,
        "PNG"
    )

    try:

        result = ocr.predict(
            processed_path
        )

        extracted_text = []

        for page_result in result:

            data = page_result.json

            if isinstance(data, dict):
                data = data.get("res", data)

            texts = data.get(
                "rec_texts",
                []
            )

            extracted_text.extend(
                texts
            )

        return "\n".join(
            extracted_text
        )

    finally:

        if os.path.exists(
            processed_path
        ):
            os.remove(
                processed_path
            )


def extract_text_from_file(file_path):
    """
    Extract text from an image or PDF using PaddleOCR.
    """

    extension = os.path.splitext(file_path)[1].lower()

    # ---------------------------------------------------------
    # IMAGE
    # ---------------------------------------------------------

    if extension in [".jpg", ".jpeg", ".png", ".webp"]:

        return extract_text_from_image(file_path)

    # ---------------------------------------------------------
    # PDF
    # ---------------------------------------------------------

    elif extension == ".pdf":

        pages = convert_from_path(
            file_path,
            dpi=200
        )

        extracted_text = []

        for index, page in enumerate(pages):

            temp_image_path = f"{file_path}_page_{index}.png"

            page.save(
                temp_image_path,
                "PNG"
            )

            try:

                text = extract_text_from_image(
                    temp_image_path
                )

                extracted_text.append(text)

            finally:

                if os.path.exists(temp_image_path):
                    os.remove(temp_image_path)

        return "\n\n".join(extracted_text)

    else:

        raise ValueError(
            "Unsupported file format."
        )


# ---------------------------------------------------------
# MEDICAL DOCUMENT UPLOAD
# ---------------------------------------------------------

def medical_document_upload(request, patient_id):

    # ---------------------------------------------------------
    # AUTHORIZATION
    # ---------------------------------------------------------

    if (
        request.user.is_authenticated
        and hasattr(request.user, "patient_profile")
        and request.user.patient_profile.id != patient_id
    ):
        return redirect(
            "myapp:patient_dashboard"
        )

    if (
        not request.user.is_authenticated
        and request.session.get("patient_flow_id") != patient_id
    ):
        return redirect(
            "myapp:patient_login"
        )

    patient = get_object_or_404(
        Patient,
        pk=patient_id
    )

    # ---------------------------------------------------------
    # POST
    # ---------------------------------------------------------

    if request.method == "POST":

        uploaded_file = request.FILES.get(
            "medical_document"
        )

        if not uploaded_file:

            messages.error(
                request,
                "Please select a medical document."
            )

            return render(
                request,
                "myapp/medical_document.html",
                {
                    "patient": patient
                }
            )

        # -----------------------------------------------------
        # VALIDATE FILE TYPE
        # -----------------------------------------------------

        allowed_extensions = [
            ".jpg",
            ".jpeg",
            ".png",
            ".webp",
            ".pdf",
        ]

        extension = os.path.splitext(
            uploaded_file.name
        )[1].lower()

        if extension not in allowed_extensions:

            messages.error(
                request,
                "Only JPG, JPEG, PNG, WEBP and PDF files are supported."
            )

            return render(
                request,
                "myapp/medical_document.html",
                {
                    "patient": patient
                }
            )

        # -----------------------------------------------------
        # SAVE DOCUMENT
        # -----------------------------------------------------

        medical_document = MedicalDocument.objects.create(
            patient=patient,
            document=uploaded_file,
            document_type="Medical Document"
        )

        file_path = medical_document.document.path

        # -----------------------------------------------------
        # PADDLE OCR
        # -----------------------------------------------------

        try:

            extracted_text = extract_text_from_file(
                file_path
            )

        except Exception as error:

            medical_document.delete()

            messages.error(
                request,
                f"OCR failed: {error}"
            )

            return render(
                request,
                "myapp/medical_document.html",
                {
                    "patient": patient
                }
            )

        # -----------------------------------------------------
        # EXTRACT SIGNIFICANT INFORMATION
        # -----------------------------------------------------

        try:

            structured_data = extract_significant_information(
                extracted_text
            )

        except Exception as error:

            structured_data = {
                "error": "Information extraction failed.",
                "details": str(error),
            }

        # -----------------------------------------------------
        # SAVE OCR + STRUCTURED DATA
        # -----------------------------------------------------

        medical_document.raw_text = extracted_text

        medical_document.structured_data = structured_data

        medical_document.save()

        # -----------------------------------------------------
        # SHOW OCR RESULTS
        # -----------------------------------------------------

        return render(
            request,
            "myapp/ocr_results.html",
            {
                "patient": patient,
                "document": medical_document,
                "ocr_text": extracted_text,
                "structured_data": structured_data,
            }
        )

    # ---------------------------------------------------------
    # GET
    # ---------------------------------------------------------

    return render(
        request,
        "myapp/medical_document.html",
        {
            "patient": patient
        }
    )


# ---------------------------------------------------------
# MEDICAL DOCUMENT INFORMATION
# ---------------------------------------------------------

def medical_document_info(request, document_id):

    if not request.user.is_authenticated:

        return JsonResponse(
            {
                "success": False,
                "error": "Authentication required."
            },
            status=401
        )

    if not hasattr(
        request.user,
        "patient_profile"
    ):

        return JsonResponse(
            {
                "success": False,
                "error": "Unauthorized."
            },
            status=403
        )

    document = get_object_or_404(
        MedicalDocument,
        pk=document_id,
        patient=request.user.patient_profile
    )

    return JsonResponse(
        {
            "success": True,
            "document_type": document.document_type,
            "uploaded_at": document.uploaded_at.strftime(
                "%d %b %Y, %I:%M %p"
            ),
            "structured_data": (
                document.structured_data or {}
            ),
        }
    )