from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect


def patient_login(request):
    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")

        # Check that both fields are provided
        if not username or not password:
            return render(
                request,
                "myapp/patient_login.html",
                {
                    "error": "Please enter your username and password.",
                    "username": username,
                },
            )

        # Authenticate the patient
        user = authenticate(
            request,
            username=username,
            password=password,
        )

        # Invalid credentials
        if user is None:
            return render(
                request,
                "myapp/patient_login.html",
                {
                    "error": "Invalid username or password.",
                    "username": username,
                },
            )

        # Make sure this account belongs to a patient
        if not hasattr(user, "patient_profile"):
            return render(
                request,
                "myapp/patient_login.html",
                {
                    "error": "This account is not registered as a patient.",
                    "username": username,
                },
            )

        # Log the patient in
        login(request, user)

        # Get the patient's database record
        patient = user.patient_profile

        # Store the patient ID for the patient flow
        request.session["patient_flow_id"] = patient.id
        request.session.modified = True

        # Patient goes directly to the patient dashboard
        return redirect("myapp:patient_dashboard")

    return render(
        request,
        "myapp/patient_login.html"
    )
    
    