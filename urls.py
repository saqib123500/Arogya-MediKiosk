from django.urls import path
from .views.start import start, landing

app_name = "myapp"

urlpatterns = [
    path("", start, name="start"),
    path("landing/", landing, name="landing"),
]
