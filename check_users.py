#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.contrib.auth.models import User
from myapp.models import Patient

print("Users in database:")
for user in User.objects.all():
    print(f"  - {user.username} (is_active: {user.is_active})")
    if hasattr(user, 'patient_profile'):
        print(f"    Patient: {user.patient_profile.name}")
    elif hasattr(user, 'doctor_profile'):
        print(f"    Doctor: {user.doctor_profile.name}")

print(f"\nTotal users: {User.objects.count()}")
print(f"Total patients: {Patient.objects.count()}")