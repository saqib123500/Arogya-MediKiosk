from django.urls import path
from .views.patient_login import patient_login
from .views.staff_login import staff_login
from .views.staff_dashboard import staff_dashboard, assign_doctor
from .patient_form import (
    patient_form,
    patient_registration,
    patient_list,
    token_confirmation,
    patient_detail,
    patient_dashboard,
    book_appointment_ajax,
    patient_tokens_ajax
)
from .views.index import index
from .doctor_dashboard import (
    doctor_dashboard,
    prescribe_token_ajax,
    patient_visit_history_ajax
)
from .symptoms import symptoms_form, save_symptoms
from .views.ocr_views import medical_document_upload, medical_document_info
app_name = "myapp"
urlpatterns = [
    path('home/', index, name='index'),
    path("patient-form/", patient_form, name="patient_form"),
    path("patient-registration/", patient_registration, name="patient_registration"),
    path("symptoms/<int:patient_id>/", symptoms_form, name="symptoms"),
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
    path('staff/login/', staff_login, name='staff_login'),
    path('staff/dashboard/', staff_dashboard, name='staff_dashboard'),
    path('staff/assign-doctor/<int:pk>/', assign_doctor, name='assign_doctor'),
    path('patients/detail/<int:pk>/', patient_detail, name='patient_detail'),
    path('patients/dashboard/', patient_dashboard, name='patient_dashboard'),
    path("patients/<int:patient_id>/medical-document/",medical_document_upload,name="medical_document_upload",),
    path("medical-document/<int:document_id>/info/",medical_document_info,name="medical_document_info",),
]
