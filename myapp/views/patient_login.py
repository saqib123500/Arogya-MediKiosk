from django.contrib.auth import authenticate, login
from django.shortcuts import render, redirect


def patient_login(request):

    if request.method == "POST":
        username = request.POST.get("username", "").strip()
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)

        if user and hasattr(user, "patient_profile"):
            login(request, user)
            return redirect("myapp:patient_dashboard")

        return render(request, "myapp/patient_login.html", {
            "error": "Invalid patient username or password.",
            "username": username,
        })

    return render(request, "myapp/patient_login.html")
