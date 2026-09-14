from django.urls import path
from .views.patient_login import patient_login
from .patient_form import *
from .views.index import *
from .doctor_dashboard import *
from .symptoms import *

app_name = "myapp"

urlpatterns = [
    path('home/', index, name='index'),
    path("patient-form/", patient_form, name="patient_form"),
    path("patient-registration/", patient_registration, name="patient_registration"),
    path("patients", patient_list, name='patient_list'),
    path('patients/<int:pk>/edit/', patient_form, name='patient_edit'),
    path('token/<int:token_id>/', token_confirmation, name='token_confirmation'),
    path("doctor-dashboard/", doctor_dashboard, name="doctor_dashboard"),
    path('patients/<int:pk>/book-appointment-ajax/', book_appointment_ajax, name='book_appointment_ajax'),
    path('patients/<int:patient_id>/tokens-ajax/', patient_tokens_ajax, name='patient_tokens_ajax'),
    path('token/<int:token_id>/prescribe-ajax/', prescribe_token_ajax, name='prescribe_token_ajax'),
    path('patients/<int:patient_id>/visit-history-ajax/', patient_visit_history_ajax, name='patient_visit_history_ajax'),
    path('patients/<int:patient_id>/symptoms/', symptoms_form, name='symptoms_form'),
    path('patients/<int:patient_id>/save-symptoms/', save_symptoms, name='save_symptoms'),
    path('patients/login/', patient_login, name='patient_login'),
]
