from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from myapp.models import Patient, Token, Doctor
from myapp.forms import PatientForm
from myapp.utils import assign_doctor, generate_token
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.db.models import Q, Prefetch
from django.utils import timezone
import json
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils.dateparse import parse_datetime

def _patient_form(request, pk=None, public_registration=False):

    patient = get_object_or_404(Patient, pk=pk) if pk else None
    initial_data = {}
    verified_abha = request.session.pop('verified_abha_number', None)
    if verified_abha and not pk:
        initial_data['abha_number'] = verified_abha
    current_token = patient.tokens.order_by('-created_at').first() if patient else None
    doctors = Doctor.objects.filter(is_active=True)

    if request.method == 'POST':
        form = PatientForm(request.POST, instance=patient)
        if form.is_valid():
            saved_patient = form.save()

            if not pk:
                if not request.user.is_authenticated:
                    request.session['patient_flow_id'] = saved_patient.id

                # New patient — auto-assign a doctor when one is available.
                doctor = assign_doctor(saved_patient)
                if doctor:
                    generate_token(saved_patient, doctor)
                else:
                    messages.warning(request, "Patient saved, but no doctor is available right now.")

                return redirect('myapp:symptoms_form', patient_id=saved_patient.id)
            else:
                # Editing — check if the doctor was manually changed
                selected_doctor_id = request.POST.get('doctor')

                if selected_doctor_id:
                    selected_doctor = get_object_or_404(Doctor, pk=selected_doctor_id)

                    if not current_token or current_token.doctor_id != selected_doctor.id:

                        new_token = generate_token(saved_patient, selected_doctor)
                        print(new_token, saved_patient, selected_doctor, 'newtoken')
                        messages.success(
                            request,
                            f"Reassigned to Dr. {selected_doctor.name} — new token #{new_token.token_number}"
                        )
                return redirect('myapp:patient_list')
    else:
        form = PatientForm(instance=patient, initial=initial_data)

    return render(request, 'myapp/patient_form.html', {
        'form': form,
        'patient': patient,
        'doctors': doctors,
        'current_token': current_token,
        'public_registration': public_registration,
        'base_template': (
            'myapp/public_base.html'
            if public_registration else 'myapp/base.html'
        ),
    })


@login_required
def patient_form(request, pk=None):
    return _patient_form(request, pk=pk)


def patient_registration(request):
    """Public case-taking page for patients who do not have an ABHA ID."""
    return _patient_form(request, public_registration=True)

@login_required
def token_confirmation(request, token_id):
    token = get_object_or_404(Token, pk=token_id)
    return render(request, 'myapp/token_confirmation.html', {'token': token})

@login_required
def patient_list(request):
    search_query = request.GET.get("q", "").strip()
 
    # Used for the Edit/Book Appointment button: only a token that's still
    # waiting can be edited. Booking a new one cancels this.
    active_tokens = Token.objects.filter(
        status="waiting"
    ).select_related("doctor").order_by("-created_at")
 
    # Used for the Status column: the patient's most recent token no matter
    # its status, so "Seen" (and "Cancelled") actually show up once set.
    latest_tokens = Token.objects.select_related("doctor").order_by("-created_at")
 
    patients = Patient.objects.prefetch_related(
        Prefetch("tokens", queryset=active_tokens, to_attr="active_tokens"),
        Prefetch("tokens", queryset=latest_tokens, to_attr="latest_tokens"),
    )
 
    doctors = Doctor.objects.filter(is_active=True)
 
    if search_query:
        patients = patients.filter(
    Q(name__icontains=search_query) | Q(phone_number__icontains=search_query)
)
 
    patients = patients.order_by("-created_at")
 
    is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"
 
    if is_ajax:
        return render(request, "myapp/_patient_table.html", {"patients": patients})
 
    return render(request, "myapp/patient_list.html", {
        "patients": patients,
        "search_query": search_query,
        "doctors": doctors,
    })

@login_required
def index(request):
    total_patients = Patient.objects.count()
    recent_patients = Patient.objects.all().order_by('-created_at')[:5]
    return render(request, 'myapp/index.html', {
        'total_patients': total_patients,
        'recent_patients': recent_patients,
    })




@login_required
@require_POST
def book_appointment_ajax(request, pk):
    patient = get_object_or_404(Patient, pk=pk)

    doctor_id = request.POST.get("doctor_id")
    appointment_dt_raw = request.POST.get("appointment_datetime")

    if not doctor_id:
        return JsonResponse({"success": False, "error": "Please select a doctor."}, status=400)

    if not appointment_dt_raw:
        return JsonResponse({"success": False, "error": "Please select a date and time."}, status=400)

    doctor = get_object_or_404(Doctor, pk=doctor_id, is_active=True)

    appointment_dt = parse_datetime(appointment_dt_raw)
    if appointment_dt is None:
        return JsonResponse({"success": False, "error": "Invalid date/time format."}, status=400)

    if timezone.is_naive(appointment_dt):
        appointment_dt = timezone.make_aware(appointment_dt)

    if appointment_dt < timezone.now():
        return JsonResponse({"success": False, "error": "Appointment time cannot be in the past."}, status=400)


    existing_active = Token.objects.filter(patient=patient, status='active')
    was_rebooking = existing_active.exists()
    existing_active.update(status='cancelled')

   
    token = generate_token(patient, doctor)
    token.appointment_datetime = appointment_dt
    token.save(update_fields=['appointment_datetime'])

    action_word = "Rebooked" if was_rebooking else "Booked"

    return JsonResponse({
        "success": True,
        "message": f"{action_word} — {doctor.name}, Token #{token.token_number}",
        "token_id": token.id,
        "token_number": token.token_number,
        "doctor_name": doctor.name,
        "appointment_datetime": appointment_dt.strftime("%d %b %Y, %I:%M %p"),
    })

@login_required
def patient_tokens_ajax(request, patient_id):
    patient = get_object_or_404(Patient, pk=patient_id)
    tokens = Token.objects.filter(patient=patient).select_related("doctor").order_by("-created_at")
    symptom_record = getattr(patient, "symptom_record", None)
    pain_symptoms = symptom_record.pain_symptoms.all() if symptom_record else []
    return render(request, "myapp/_patient_tokens_modal.html", {
        "patient": patient,
        "tokens": tokens,
        "symptom_record": symptom_record,
        "pain_symptoms": pain_symptoms,
    })
    


