from django import forms
from django.contrib.auth.models import User
from .models import Patient


class PatientForm(forms.ModelForm):
    username = forms.CharField(max_length=150, required=False)
    password = forms.CharField(widget=forms.PasswordInput, required=False)
    
    class Meta:
        model = Patient
        fields = [
            "name",
            "age",
            "gender",
            "phone_number",
            "address",
            "abha_number",
            "complaint",
            "prakriti",
            "vikriti",
            "sara",
            "samhanana",
            "pramana",
            "satmya",
            "satva",
            "ahara_shakti",
            "vyayama_shakti",
            "vaya",
        ]

    def clean_phone_number(self):
        """Keep one patient record per contact number.

        Excluding ``self.instance`` is important when the existing patient is
        edited: keeping the same number must remain valid.
        """
        phone_number = self.cleaned_data["phone_number"]
        matching_patients = Patient.objects.filter(phone_number=phone_number)

        if self.instance and self.instance.pk:
            matching_patients = matching_patients.exclude(pk=self.instance.pk)

        if matching_patients.exists():
            raise forms.ValidationError(
                "A patient with this contact number already exists. "
                "Use the existing patient's record instead."
            )

        return phone_number
    
    def clean_username(self):
        username = self.cleaned_data.get("username")
        if username:
            # Check if username already exists (excluding current user if editing)
            existing_users = User.objects.filter(username__iexact=username)
            if self.instance and self.instance.user:
                existing_users = existing_users.exclude(pk=self.instance.user.pk)
            
            if existing_users.exists():
                raise forms.ValidationError("This username is already in use.")
        return username


class PatientRegistrationForm(PatientForm):
    """Public registration form, including credentials for the patient portal."""

    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("This username is already in use.")
        return username
        
