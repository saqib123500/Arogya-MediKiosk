from django.contrib import admin
from .models import Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "age",
        "gender",
        "abha",
        "is_verified",
        "created_at",
    )

    search_fields = (
        "name",
        "abha",
        "contact",
    )

    list_filter = (
        "gender",
        "is_verified",
        "created_at",
    )
    
    