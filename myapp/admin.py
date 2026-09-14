# Register your models here.
# admin.py
from django.contrib import admin
from .models import Patient, Doctor, Token

admin.site.register(Patient)
admin.site.register(Doctor)
admin.site.register(Token)