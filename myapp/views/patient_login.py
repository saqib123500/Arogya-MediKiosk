from django.shortcuts import render, redirect
from django.utils import timezone
from datetime import timedelta
import random


def patient_login(request):

    if request.method == "POST":
        action = request.POST.get("action")
        abha = request.POST.get("abha", "").replace("-", "").strip()
        otp = request.POST.get("otp", "").strip()

        # =====================================================
        # SEND OTP
        # =====================================================
        if action == "send_otp":

            if len(abha) != 14 or not abha.isdigit():
                return render(request, "myapp/patient_login.html", {
                    "error": "Please enter a valid 14-digit ABHA ID.",
                    "abha": abha,
                })

            # TODO: replace this block with your real ABDM API call
            # to actually send an OTP to the patient's registered mobile.
            otp = str(random.randint(100000, 999999))

            request.session["pending_abha"] = abha
            request.session["pending_otp"] = otp
            request.session["otp_expires_at"] = (
                timezone.now() + timedelta(minutes=2)
            ).isoformat()
            request.session.modified = True

            print(f"\n=== OTP SIMULATOR === ABHA: {abha} OTP: {otp} ===\n")

            return render(request, "myapp/patient_login.html", {
                "otp_sent": True,
                "abha": abha,
            })

        # =====================================================
        # VERIFY OTP
        # =====================================================
        if action == "verify_otp":

            pending_abha = request.session.get("pending_abha")
            expected_otp = request.session.get("pending_otp")
            expires_at = request.session.get("otp_expires_at")

            if not pending_abha:
                return render(request, "myapp/patient_login.html", {
                    "error": "Please enter your ABHA ID first."
                })

            if not expected_otp:
                return render(request, "myapp/patient_login.html", {
                    "abha": pending_abha,
                    "otp_sent": True,
                    "error": "OTP was not generated yet.",
                })

            if expires_at:
                expiry_time = timezone.datetime.fromisoformat(expires_at)
                if timezone.now() >= expiry_time:
                    request.session.pop("pending_abha", None)
                    request.session.pop("pending_otp", None)
                    request.session.pop("otp_expires_at", None)
                    request.session.modified = True
                    return render(request, "myapp/patient_login.html", {
                        "error": "OTP has expired. Please request a new OTP."
                    })

            if otp != expected_otp:
                return render(request, "myapp/patient_login.html", {
                    "otp_sent": True,
                    "abha": pending_abha,
                    "error": "Wrong OTP",
                })

            # =================================================
            # CORRECT OTP
            # =================================================
            request.session["verified_abha_number"] = pending_abha
            request.session.pop("pending_abha", None)
            request.session.pop("pending_otp", None)
            request.session.pop("otp_expires_at", None)
            request.session.modified = True

            return redirect("myapp:patient_form")

    return render(request, "myapp/patient_login.html")