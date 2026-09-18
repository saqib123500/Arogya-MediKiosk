#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.contrib.auth.models import User
from myapp.models import Patient

print("Patients in database:")
for patient in Patient.objects.all():
    if patient.user:
        print(f"  - {patient.name} (ID: {patient.id})")
        print(f"    User: {patient.user.username} (ID: {patient.user.id})")
    else:
        print(f"  - {patient.name} (ID: {patient.id})")
        print(f"    No user account")

print(f"\nTotal patients: {Patient.objects.count()}")

print("\nUsers without patient profiles:")
for user in User.objects.all():
    if not hasattr(user, 'patient_profile') and not hasattr(user, 'doctor_profile'):
        print(f"  - {user.username} (ID: {user.id})")