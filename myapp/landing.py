from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView
from django.urls import reverse


def landing(request):
    if request.user.is_authenticated and hasattr(request.user, "doctor_profile"):
        return redirect("myapp:doctor_dashboard")
    return render(request, "myapp/landing.html")


class DoctorLoginView(LoginView):
    template_name = "myapp/login.html"
    redirect_authenticated_user = True

    def get_success_url(self):
        redirect_to = self.get_redirect_url()
        if redirect_to:
            return redirect_to
        if hasattr(self.request.user, "doctor_profile"):
            return reverse("myapp:doctor_dashboard")
        return reverse("myapp:index")








