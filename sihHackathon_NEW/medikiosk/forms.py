from django import forms
from .models import Patient , MedicalDocument


class PatientForm(forms.ModelForm):
    class Meta:
        model = Patient
        fields = [
            "name",
            "age",
            "gender",
            "contact",
            "address",
            "abha",
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
        
class MedicalDocumentUploadForm(forms.ModelForm):

    class Meta:
        model = MedicalDocument
        fields = ["document"]

    def clean_document(self):

        document = self.cleaned_data["document"]

        allowed_types = [
            "image/jpeg",
            "image/png",
        ]

        if document.content_type not in allowed_types:
            raise forms.ValidationError(
                "Please upload a JPG or PNG medical document."
            )

        return document