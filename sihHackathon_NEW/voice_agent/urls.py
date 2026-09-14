from django.urls import path
from . import views

urlpatterns = [
    path("", views.voice_agent, name="voice_agent"),
    path("process/", views.process_voice, name="process_voice"),
    path("reset/", views.reset_interview_view, name="reset_interview"),
]

