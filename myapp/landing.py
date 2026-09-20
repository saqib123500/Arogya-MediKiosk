from django.shortcuts import render, redirect
from django.contrib.auth.views import LoginView
from django.urls import reverse
from urllib.parse import urlencode
from django.http import HttpResponseRedirect
from myapp.models import Patient
from myapp.forms import PatientForm
from myapp.utils import assign_doctor, generate_token
from myapp.languages import store_patient_language
from django.db import transaction



def landing(request):
    if request.user.is_authenticated:
        if request.user.is_staff:
            return redirect("myapp:staff_dashboard")
        if hasattr(request.user, "doctor_profile"):
            return redirect("myapp:doctor_dashboard")
        if hasattr(request.user, "patient_profile"):
            return redirect("myapp:patient_dashboard")
    return render(request, "myapp/landing.html")


def _symptoms_redirect(request, patient_id):
    language = store_patient_language(request)
    url = reverse("myapp:symptoms", kwargs={"patient_id": patient_id})
    if language:
        url = f"{url}?{urlencode({'language': language})}"
    return HttpResponseRedirect(url)





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


class StaffLoginView(LoginView):
    """Sign staff in and take them to the front-desk dashboard."""

    template_name = "myapp/login.html"
    redirect_authenticated_user = True

    def form_valid(self, form):
        """Check that the user is not a doctor before allowing staff login."""
        user = form.get_user()
        
        # Prevent doctors from logging in via staff login
        if hasattr(user, "doctor_profile"):
            form.add_error(None, "Invalid username or password.")
            return self.form_invalid(form)
        
        return super().form_valid(form)

    def get_success_url(self):
        redirect_to = self.get_redirect_url()
        return redirect_to or reverse("myapp:staff_dashboard")





