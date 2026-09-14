from django.urls import path
from . import views
from .ocr_views import medical_document_upload,medical_document_confirm
from .document_views import medical_documents

urlpatterns = [
    path("home/", views.home, name="home"),
    path("login/", views.login_page, name="login"),
    path("patient_form/", views.patient_form, name="patient_form"),
    path("medical-document/",medical_document_upload,name="medical_document_upload"),
    path("medical-document/confirm/",medical_document_confirm,name="medical_document_confirm"),
    path("medical-documents/",medical_documents,name="medical_documents"),
    

]