from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib import messages
from django.contrib.auth.models import User
from myapp.models import Doctor, Patient

def staff_login(request):
    """
    Dedicated login view for staff members.
    Verifies that the user is a staff member and NOT a doctor or patient.
    """
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(username=username, password=password)

        if user is not None:
            # 1. Must be marked as staff in Django Admin
            if not user.is_staff:
                messages.error(request, "Access denied. This portal is for staff only.")
                return render(request, "myapp/staff_login.html")

            # 2. Check for Doctor profile
            if Doctor.objects.filter(user=user).exists():
                messages.error(request, "Access denied. Doctors cannot login as staff.")
                return render(request, "myapp/staff_login.html")

            # 3. Check for Patient profile
            if Patient.objects.filter(user=user).exists():
                messages.error(request, "Access denied. Patients cannot login as staff.")
                return render(request, "myapp/staff_login.html")

            login(request, user)
            return redirect("myapp:staff_dashboard")
        else:
            messages.error(request, "Invalid username or password.")
            return render(request, "myapp/staff_login.html")

    return render(request, "myapp/staff_login.html")
