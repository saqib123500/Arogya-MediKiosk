
from django.db import models


class Patient(models.Model):
    GENDER_CHOICES = [
        ("male", "Male"),
        ("female", "Female"),
        ("other", "Other"),
    ]

    VAYA_CHOICES = [
        ("bala", "Bala"),
        ("madhya", "Madhya"),
        ("vriddha", "Vriddha"),
    ]

    # Basic Details
    name = models.CharField(max_length=150)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES)
    contact = models.CharField(max_length=15)
    address = models.TextField()

    # ABHA
    abha = models.CharField(
        max_length=14,
        blank=True,
        db_index=True
    )

    complaint = models.TextField()

    # Dashavidha Pariksha
    prakriti = models.TextField()
    vikriti = models.TextField()
    sara = models.TextField()
    samhanana = models.TextField()
    pramana = models.TextField()
    satmya = models.TextField()
    satva = models.TextField()
    ahara_shakti = models.TextField()
    vyayama_shakti = models.TextField()
    vaya = models.CharField(
        max_length=20,
        choices=VAYA_CHOICES
    )

    # Verification
    otp = models.CharField(
        max_length=6,
        blank=True
    )

    is_verified = models.BooleanField(
        default=False
    )
    is_confirmed = models.BooleanField(
        default=False
)

    otp_expires_at = models.DateTimeField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )


class MedicalDocument(models.Model):

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="medical_documents"
    )

    document = models.FileField(
        upload_to="medical_documents/"
    )

    document_type = models.CharField(
        max_length=100,
        blank=True
    )

    raw_text = models.TextField(
        blank=True
    )

    structured_data = models.JSONField(
        default=dict,
        blank=True
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.patient.name} - {self.document.name}"
    
    
    def __str__(self):
        return f"{self.name} - {self.abha}"
    
    