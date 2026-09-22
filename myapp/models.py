from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

phone_regex = RegexValidator(
    regex=r'^\d{10}$',
    message="Phone number must be exactly 10 digits."
)

class Patient(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="patient_profile",
    )

    GENDER_CHOICES = [
        ("male", "Male"),
        ("female", "Female"),
        ("other", "Other"),
    ]

    PRAKRITI_CHOICES = [
        ("vata", "Vata (Air + Space)"),
        ("pitta", "Pitta (Fire + Water)"),
        ("kapha", "Kapha (Earth + Water)"),
        ("vata_pitta", "Vata-Pitta (Air-Space + Fire-Water)"),
        ("pitta_kapha", "Pitta-Kapha (Fire-Water + Earth-Water)"),
        ("vata_kapha", "Vata-Kapha (Air-Space + Earth-Water)"),
        ("tridoshaja", "Tridoshaja (all three balanced)"),
    ]

    VIKRITI_CHOICES = [
        ("vata", "Vata Vikriti (Air + Space)"),
        ("pitta", "Pitta Vikriti (Fire + Water)"),
        ("kapha", "Kapha Vikriti (Earth + Water)"),
        ("dwidoshaja", "Dwidoshaja (two doshas involved)"),
        ("sannipataja", "Sannipataja (all three doshas involved)"),
        ("none", "No significant Vikriti"),
    ]

    PRAVARA_SCALE_CHOICES = [
        ("pravara", "Pravara"),
        ("madhyama", "Madhyama"),
        ("avara", "Avara"),
    ]

    VAYA_CHOICES = [
        ("bala", "Bala (childhood: up to 16 years)"),
        ("madhya", "Madhya (middle age: 16-70 years)"),
        ("vriddha", "Vriddha (old age: above 70 years)"),
    ]

    # Basic Details
    name = models.CharField(max_length=150)
    age = models.PositiveIntegerField()
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES)
    phone_number = models.CharField(
        validators=[phone_regex],
        max_length=10,
        blank=True,
    )
    address = models.TextField()
    abha_number = models.CharField(
        max_length=17,
        blank=True,
        null=True,
        unique=True
    )
    abha_address = models.CharField(max_length=100, blank=True, null=True)
    abha_verified = models.BooleanField(default=False)
    abha_verified_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    complaint = models.TextField()

    # Dashavidha Pariksha
    prakriti = models.CharField(max_length=20, choices=PRAKRITI_CHOICES)
    vikriti = models.CharField(max_length=20, choices=VIKRITI_CHOICES)
    sara = models.CharField(max_length=20, choices=PRAVARA_SCALE_CHOICES)
    samhanana = models.CharField(max_length=20, choices=PRAVARA_SCALE_CHOICES)
    pramana = models.CharField(max_length=20, choices=PRAVARA_SCALE_CHOICES)
    satmya = models.CharField(max_length=20, choices=PRAVARA_SCALE_CHOICES)
    satva = models.CharField(max_length=20, choices=PRAVARA_SCALE_CHOICES)
    ahara_shakti = models.CharField(max_length=20, choices=PRAVARA_SCALE_CHOICES)
    vyayama_shakti = models.CharField(max_length=20, choices=PRAVARA_SCALE_CHOICES)
    vaya = models.CharField(max_length=20, choices=VAYA_CHOICES)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
    
class Doctor(models.Model):
    SPECIALTY_CHOICES = [
        ("vata", "Vata Specialist"),
        ("pitta", "Pitta Specialist"),
        ("kapha", "Kapha Specialist"),
        ("general", "General Physician"),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="doctor_profile"
    )

    name = models.CharField(max_length=150)

    specialty = models.CharField(
        max_length=20,
        choices=SPECIALTY_CHOICES
    )

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"Dr. {self.name} ({self.get_specialty_display()})"


class Token(models.Model):
    STATUS_CHOICES = [
        ("waiting", "Waiting"),
        ("seen", "Seen"),
        ("cancelled", "Cancelled"),
    ]

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="tokens"
    )

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name="tokens"
    )

    token_number = models.PositiveIntegerField()

    date = models.DateField()

    appointment_datetime = models.DateTimeField(
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default="waiting"
    )
    triage_level = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="KTAS priority level (1: Critical to 5: Non-Urgent)"
    )
    triage_recommendation = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["doctor", "date", "token_number"],
                name="unique_token_per_doctor_per_date",
            )
        ]

    def __str__(self):
        return (
            f"Token {self.token_number} — "
            f"{self.patient.name} — "
            f"{self.doctor.name}"
        )
    


class Prescription(models.Model):
    token = models.OneToOneField(
        Token,
        on_delete=models.CASCADE,
        related_name="prescription"
    )

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="prescriptions"
    )

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name="prescriptions"
    )

    diagnosis = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Prescription — {self.patient.name} — {self.created_at:%d %b %Y}"


class PrescriptionItem(models.Model):
    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.CASCADE,
        related_name="items"
    )

    medicine_name = models.CharField(max_length=200)
    dosage = models.CharField(max_length=100, blank=True)
    timing = models.CharField(max_length=100, blank=True)
    duration = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.medicine_name


class ABDMToken(models.Model):
    access_token = models.TextField()

    token_type = models.CharField(
        max_length=50,
        default="Bearer"
    )

    expires_at = models.DateTimeField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"ABDM token {self.id}"
    
class Symptom(models.Model):
    patient = models.OneToOneField(
        Patient,
        on_delete=models.CASCADE,
        related_name="symptom_record"
    )
    non_pain_symptoms = models.JSONField(default=list, blank=True)
    fever_temperature = models.CharField(max_length=50, blank=True)
    fever_duration = models.CharField(max_length=50, blank=True)
    other_symptoms = models.TextField(blank=True)
    language = models.CharField(max_length=10, blank=True)

    # Vitals for Triage ML
    sbp = models.IntegerField(null=True, blank=True)
    dbp = models.IntegerField(null=True, blank=True)
    hr = models.IntegerField(null=True, blank=True)
    rr = models.IntegerField(null=True, blank=True)
    saturation = models.IntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Symptoms — {self.patient.name}"


class PainSymptom(models.Model):
    symptom_record = models.ForeignKey(
        Symptom,
        on_delete=models.CASCADE,
        related_name="pain_symptoms"
    )
    location = models.CharField(max_length=50)

    site = models.TextField(blank=True)
    onset = models.TextField(blank=True)
    character = models.TextField(blank=True)
    radiation = models.TextField(blank=True)
    associations = models.TextField(blank=True)
    time_course = models.TextField(blank=True)
    exacerbating_relieving = models.TextField(blank=True)
    severity = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.location} — {self.symptom_record.patient.name}"

        
class PatientHistory(models.Model):

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="history"
    )

    token = models.ForeignKey(
        Token,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="visit_history"
    )

    complaint = models.TextField(blank=True)

    symptoms = models.JSONField(
        default=list,
        blank=True
    )

    other_symptoms = models.TextField(
        blank=True
    )

    fever_temperature = models.CharField(
        max_length=50,
        blank=True
    )

    fever_duration = models.CharField(
        max_length=50,
        blank=True
    )

    visit_date = models.DateTimeField(
        auto_now_add=True
    )

    visit_data = models.JSONField(
        default=dict,
        blank=True
    )

    def __str__(self):
        return (
            f"History — {self.patient.name} — "
            f"{self.visit_date:%d %b %Y}"
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
        return f"{self.patient} - {self.document.name}"