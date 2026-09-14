from django.shortcuts import render, redirect
from django.utils import timezone
from datetime import timedelta
import random

from .models import Patient


# =============================================================
# HOME
# =============================================================

def home(request):

    return render(
        request,
        "medikiosk/patient/home.html"
    )


# =============================================================
# LOGIN / OTP VERIFICATION
# =============================================================

def login_page(request):

    if request.method == "POST":

        action = request.POST.get("action")

        abha = request.POST.get(
            "abha",
            ""
        ).replace("-", "").strip()

        otp = request.POST.get(
            "otp",
            ""
        ).strip()

        # =====================================================
        # SEND OTP
        # =====================================================

        if action == "send_otp":

            if len(abha) != 14 or not abha.isdigit():

                return render(
                    request,
                    "medikiosk/patient/LoginPage.html",
                    {
                        "error": "Please enter a valid 14-digit ABHA ID.",
                        "abha": abha,
                    }
                )

            # -------------------------------------------------
            # Generate OTP
            # -------------------------------------------------

            otp = str(
                random.randint(
                    100000,
                    999999
                )
            )

            request.session["pending_abha"] = abha

            request.session["pending_otp"] = otp

            request.session["otp_expires_at"] = (
                timezone.now()
                + timedelta(minutes=2)
            ).isoformat()

            request.session.modified = True

            # -------------------------------------------------
            # OTP Simulator
            # -------------------------------------------------

            print(
                "\n========== OTP SIMULATOR =========="
            )

            print(
                f"ABHA ID: {abha}"
            )

            print(
                f"Your OTP is: {otp}"
            )

            print(
                "====================================\n"
            )

            return render(
                request,
                "medikiosk/patient/LoginPage.html",
                {
                    "otp_sent": True,
                    "abha": abha,
                }
            )

        # =====================================================
        # VERIFY OTP
        # =====================================================

        if action == "verify_otp":

            pending_abha = request.session.get(
                "pending_abha"
            )

            expected_otp = request.session.get(
                "pending_otp"
            )

            expires_at = request.session.get(
                "otp_expires_at"
            )

            # -------------------------------------------------
            # No pending ABHA
            # -------------------------------------------------

            if not pending_abha:

                return render(
                    request,
                    "medikiosk/patient/LoginPage.html",
                    {
                        "error": "Please enter your ABHA ID first."
                    }
                )

            # -------------------------------------------------
            # No OTP
            # -------------------------------------------------

            if not expected_otp:

                return render(
                    request,
                    "medikiosk/patient/LoginPage.html",
                    {
                        "abha": pending_abha,
                        "otp_sent": True,
                        "error": "OTP was not generated yet."
                    }
                )

            # -------------------------------------------------
            # Check OTP expiry
            # -------------------------------------------------

            if expires_at:

                expiry_time = timezone.datetime.fromisoformat(
                    expires_at
                )

                if timezone.now() >= expiry_time:

                    request.session.pop(
                        "pending_abha",
                        None
                    )

                    request.session.pop(
                        "pending_otp",
                        None
                    )

                    request.session.pop(
                        "otp_expires_at",
                        None
                    )

                    request.session.modified = True

                    return render(
                        request,
                        "medikiosk/patient/LoginPage.html",
                        {
                            "error":
                            "OTP has expired. Please request a new OTP."
                        }
                    )

            # -------------------------------------------------
            # Wrong OTP
            # -------------------------------------------------

            if otp != expected_otp:

                return render(
                    request,
                    "medikiosk/patient/LoginPage.html",
                    {
                        "otp_sent": True,
                        "abha": pending_abha,
                        "error": "Wrong OTP"
                    }
                )

            # =================================================
            # CORRECT OTP
            # =================================================

            request.session["verified_abha"] = pending_abha

            # -------------------------------------------------
            # Clear temporary OTP information
            # -------------------------------------------------

            request.session.pop(
                "pending_abha",
                None
            )

            request.session.pop(
                "pending_otp",
                None
            )

            request.session.pop(
                "otp_expires_at",
                None
            )

            request.session.modified = True

            # -------------------------------------------------
            # Go directly to Patient Form
            # -------------------------------------------------

            return redirect(
                "patient_form"
            )

    # =========================================================
    # DISPLAY LOGIN PAGE
    # =========================================================

    return render(
        request,
        "medikiosk/patient/LoginPage.html"
    )


# =============================================================
# PATIENT FORM
# =============================================================

def patient_form(request):

    # ---------------------------------------------------------
    # CHECK ABHA VERIFICATION
    # ---------------------------------------------------------

    verified_abha = request.session.get(
        "verified_abha"
    )

    if not verified_abha:

        return redirect(
            "login"
        )

    # =========================================================
    # SAVE PATIENT
    # =========================================================

    if request.method == "POST":

        patient = Patient.objects.create(

            # -------------------------------------------------
            # Basic Details
            # -------------------------------------------------

            name=request.POST.get(
                "name",
                ""
            ),

            age=request.POST.get(
                "age",
                ""
            ),

            gender=request.POST.get(
                "gender",
                ""
            ),

            contact=request.POST.get(
                "contact",
                ""
            ),

            address=request.POST.get(
                "address",
                ""
            ),

            # -------------------------------------------------
            # Verified ABHA
            # -------------------------------------------------

            abha=verified_abha,

            # -------------------------------------------------
            # Chief Complaint
            # -------------------------------------------------

            complaint=request.POST.get(
                "complaint",
                ""
            ),

            # -------------------------------------------------
            # Dashavidha Pariksha
            # -------------------------------------------------

            prakriti=request.POST.get(
                "prakriti",
                ""
            ),

            vikriti=request.POST.get(
                "vikriti",
                ""
            ),

            sara=request.POST.get(
                "sara",
                ""
            ),

            samhanana=request.POST.get(
                "samhanana",
                ""
            ),

            pramana=request.POST.get(
                "pramana",
                ""
            ),

            satmya=request.POST.get(
                "satmya",
                ""
            ),

            satva=request.POST.get(
                "satva",
                ""
            ),

            ahara_shakti=request.POST.get(
                "ahara_shakti",
                ""
            ),

            vyayama_shakti=request.POST.get(
                "vyayama_shakti",
                ""
            ),

            vaya=request.POST.get(
                "vaya",
                ""
            ),

            # -------------------------------------------------
            # Verification Status
            # -------------------------------------------------

            is_verified=True
        )

        # -----------------------------------------------------
        # Store Patient ID
        # -----------------------------------------------------

        request.session["patient_id"] = patient.id

        # -----------------------------------------------------
        # Remove verified ABHA after patient is saved
        # -----------------------------------------------------

        request.session.pop(
            "verified_abha",
            None
        )

        request.session.modified = True

        # -----------------------------------------------------
        # Go to Medical Documents
        # -----------------------------------------------------

        return redirect(
            "medical_documents"
        )

    # =========================================================
    # DISPLAY PATIENT FORM
    # =========================================================

    return render(
        request,
        "medikiosk/patient/patient_form.html"
    )
    
    