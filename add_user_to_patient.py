#!/usr/bin/env python
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'myproject.settings')
django.setup()

from django.contrib.auth.models import User
from myapp.models import Patient

# List all patients without user accounts
patients_without_users = Patient.objects.filter(user__isnull=True)

print("Patients without User accounts:")
for patient in patients_without_users:
    print(f"  - {patient.name} (ID: {patient.id}, Phone: {patient.phone_number})")

if patients_without_users.exists():
    print(f"\nTotal patients without user accounts: {patients_without_users.count()}")
    
    # Example: Create user for first patient
    if patients_without_users.exists():
        patient = patients_without_users.first()
        username = input(f"\nEnter username for {patient.name}: ")
        password = input("Enter password: ")
        
        try:
            user = User.objects.create_user(
                username=username,
                password=password
            )
            patient.user = user
            patient.save()
            print(f"✓ User account created for {patient.name}")
        except Exception as e:
            print(f"✗ Error creating user: {e}")
else:
    print("All patients have user accounts.")