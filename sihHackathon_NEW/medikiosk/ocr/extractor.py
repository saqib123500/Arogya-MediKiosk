import json
import re


class MedicalTextExtractor:

    def extract(self, text):

        data = {
            "document": {
                "document_type": None,
                "report_date": None,
                "doctor": None,
                "hospital": None,
                "department": None,
            },

            "patient": {
                "name": None,
                "age": None,
                "date_of_birth": None,
                "gender": None,
                "abha_id": None,
                "phone": None,
                "address": None,
                "blood_group": None,
            },

            "chief_complaint": None,

            "symptoms": [],

            "medical_history": [],

            "surgical_history": [],

            "family_history": [],

            "allergies": [],

            "medications": [],

            "diagnoses": [],

            "vitals": {
                "blood_pressure": None,
                "pulse": None,
                "temperature": None,
                "respiratory_rate": None,
                "oxygen_saturation": None,
                "height": None,
                "weight": None,
                "bmi": None,
            },

            "laboratory_results": [],

            "imaging": [],

            "clinical_observations": [],

            "procedures": [],

            "follow_up": [],

            "additional_information": [],

            "raw_text": text,
        }

        lines = [
            line.strip()
            for line in text.splitlines()
            if line.strip()
        ]

        # =====================================================
        # PATIENT INFORMATION
        # =====================================================

        for i, line in enumerate(lines):

            lower = line.lower()

            # -------------------------------------------------
            # Name
            # -------------------------------------------------

            if lower in ["name:", "patient name:"]:

                if i + 1 < len(lines):
                    data["patient"]["name"] = lines[i + 1]

            elif lower.startswith("patient name:"):

                value = line.split(":", 1)[1].strip()

                if value:
                    data["patient"]["name"] = value

            # -------------------------------------------------
            # Age
            # -------------------------------------------------

            if lower == "age:" and i + 1 < len(lines):

                match = re.search(
                    r"\d+",
                    lines[i + 1]
                )

                if match:
                    data["patient"]["age"] = int(
                        match.group()
                    )

            elif lower.startswith("age:"):

                match = re.search(
                    r"\d+",
                    line
                )

                if match:
                    data["patient"]["age"] = int(
                        match.group()
                    )

            # -------------------------------------------------
            # Date of Birth
            # -------------------------------------------------

            if lower.startswith("dob:"):

                value = line.split(":", 1)[1].strip()

                if value:
                    data["patient"]["date_of_birth"] = value

            # -------------------------------------------------
            # Gender
            # -------------------------------------------------

            if lower == "gender:" and i + 1 < len(lines):

                gender = lines[i + 1].lower()

                if gender in ["male", "female", "other"]:
                    data["patient"]["gender"] = gender

            elif lower.startswith("gender:"):

                gender = line.split(":", 1)[1].strip().lower()

                if gender in ["male", "female", "other"]:
                    data["patient"]["gender"] = gender

            # -------------------------------------------------
            # ABHA
            # -------------------------------------------------

            if "abha" in lower:

                match = re.search(
                    r"\d{2}-\d{4}-\d{4}-\d{4}",
                    line
                )

                if match:
                    data["patient"]["abha_id"] = match.group()

            # -------------------------------------------------
            # Phone
            # -------------------------------------------------

            if any(
                word in lower
                for word in ["phone", "mobile", "contact"]
            ):

                match = re.search(
                    r"\+?\d[\d\s-]{8,14}\d",
                    line
                )

                if match:
                    data["patient"]["phone"] = (
                        match.group().strip()
                    )

            # -------------------------------------------------
            # Blood Group
            # -------------------------------------------------

            if "blood group" in lower:

                match = re.search(
                    r"(A|B|AB|O)\s*[+-]",
                    line,
                    re.IGNORECASE
                )

                if match:
                    data["patient"]["blood_group"] = (
                        match.group().replace(" ", "")
                    )

            # =================================================
            # MEDICAL HISTORY
            # =================================================

            if lower.startswith(
                ("medical history:", "history:")
            ):

                value = line.split(":", 1)[-1].strip()

                if value:
                    data["medical_history"].append(value)

            # =================================================
            # SURGERY
            # =================================================

            if lower.startswith(
                ("surgeries:", "surgery:", "surgical history:")
            ):

                value = line.split(":", 1)[-1].strip()

                if value:
                    data["surgical_history"].append(value)

            # =================================================
            # FAMILY HISTORY
            # =================================================

            if lower.startswith("family history:"):

                value = line.split(":", 1)[-1].strip()

                if value:
                    data["family_history"].append(value)

            # =================================================
            # ALLERGIES
            # =================================================

            if lower.startswith("allergies:"):

                value = line.split(":", 1)[-1].strip()

                if value:
                    data["allergies"].append(value)

            # =================================================
            # CHIEF COMPLAINT
            # =================================================

            if lower.startswith(
                ("chief complaint:", "complaint:", "main complaint:")
            ):

                value = line.split(":", 1)[-1].strip()

                if value:
                    data["chief_complaint"] = value

            # =================================================
            # SYMPTOMS
            # =================================================

            if lower.startswith("symptoms:"):

                value = line.split(":", 1)[-1].strip()

                if value:
                    data["symptoms"].append(value)

            # =================================================
            # BLOOD PRESSURE
            # =================================================

            if "blood pressure" in lower:

                match = re.search(
                    r"(\d{2,3})\s*/\s*(\d{2,3})",
                    line
                )

                if match:

                    data["vitals"]["blood_pressure"] = (
                        f"{match.group(1)}/{match.group(2)} mmHg"
                    )

            # =================================================
            # PULSE
            # =================================================

            if lower.startswith("pulse"):

                match = re.search(
                    r"\d{2,3}",
                    line
                )

                if match:

                    data["vitals"]["pulse"] = (
                        f"{match.group()} bpm"
                    )

            # =================================================
            # TEMPERATURE
            # =================================================

            if "temperature" in lower:

                match = re.search(
                    r"\d+[.,]\d+",
                    line
                )

                if match:

                    temperature = (
                        match.group()
                        .replace(",", ".")
                    )

                    data["vitals"]["temperature"] = (
                        f"{temperature} °C"
                    )

            # =================================================
            # RESPIRATORY RATE
            # =================================================

            if "respiratory" in lower:

                match = re.search(
                    r"\d{1,2}",
                    line
                )

                if match:

                    data["vitals"]["respiratory_rate"] = (
                        f"{match.group()}/min"
                    )

            # =================================================
            # OXYGEN SATURATION
            # =================================================

            if any(
                word in lower
                for word in ["spo2", "oxygen saturation", "o2 saturation"]
            ):

                match = re.search(
                    r"\d{2,3}\s*%",
                    line
                )

                if match:

                    data["vitals"]["oxygen_saturation"] = (
                        match.group()
                    )

            # =================================================
            # HEIGHT
            # =================================================

            if lower.startswith("height"):

                match = re.search(
                    r"\d+(?:\.\d+)?\s*(?:cm|m|ft|feet)",
                    line,
                    re.IGNORECASE
                )

                if match:
                    data["vitals"]["height"] = match.group()

            # =================================================
            # WEIGHT
            # =================================================

            if lower.startswith("weight"):

                match = re.search(
                    r"\d+(?:\.\d+)?\s*kg",
                    line,
                    re.IGNORECASE
                )

                if match:
                    data["vitals"]["weight"] = match.group()

            # =================================================
            # BMI
            # =================================================

            if re.search(r"\bbmi\b", lower):

                match = re.search(
                    r"\d+(?:\.\d+)?",
                    line
                )

                if match:
                    data["vitals"]["bmi"] = match.group()

            # =================================================
            # MEDICATIONS
            # =================================================

            if lower.startswith(
                ("medication:", "medications:", "medicine:")
            ):

                value = line.split(":", 1)[-1].strip()

                if value:
                    data["medications"].append({
                        "raw": value
                    })

            # =================================================
            # DIAGNOSIS
            # =================================================

            if lower.startswith(
                ("diagnosis:", "diagnoses:")
            ):

                value = line.split(":", 1)[-1].strip()

                if value:
                    data["diagnoses"].append(value)

            # =================================================
            # LABORATORY RESULTS
            # =================================================

            if lower.startswith(
                (
                    "lab:",
                    "laboratory:",
                    "lab result:",
                    "laboratory result:"
                )
            ):

                value = line.split(":", 1)[-1].strip()

                if value:
                    data["laboratory_results"].append({
                        "raw": value
                    })

            # =================================================
            # IMAGING
            # =================================================

            if lower.startswith(
                (
                    "x-ray:",
                    "xray:",
                    "ct:",
                    "mri:",
                    "ultrasound:",
                    "imaging:"
                )
            ):

                value = line.split(":", 1)[-1].strip()

                if value:
                    data["imaging"].append({
                        "raw": value
                    })

            # =================================================
            # CLINICAL OBSERVATIONS
            # =================================================

            if lower.startswith(
                (
                    "observation:",
                    "observations:",
                    "clinical observation:",
                    "doctor's observations:"
                )
            ):

                value = line.split(":", 1)[-1].strip()

                if value:
                    data["clinical_observations"].append(value)

            # =================================================
            # PROCEDURES
            # =================================================

            if lower.startswith(
                ("procedure:", "procedures:")
            ):

                value = line.split(":", 1)[-1].strip()

                if value:
                    data["procedures"].append(value)

            # =================================================
            # FOLLOW-UP
            # =================================================

            if lower.startswith(
                (
                    "follow-up:",
                    "follow up:",
                    "next steps:",
                    "plan:"
                )
            ):

                value = line.split(":", 1)[-1].strip()

                if value:
                    data["follow_up"].append(value)

            # =================================================
            # DOCTOR
            # =================================================

            if lower.startswith(
                ("dr.", "doctor:", "physician:")
            ):

                if lower.startswith("dr."):
                    data["document"]["doctor"] = line

                else:
                    value = line.split(":", 1)[-1].strip()

                    if value:
                        data["document"]["doctor"] = value

            # =================================================
            # HOSPITAL
            # =================================================

            if lower.startswith(
                ("hospital:", "clinic:", "healthcare center:")
            ):

                value = line.split(":", 1)[-1].strip()

                if value:
                    data["document"]["hospital"] = value

            # =================================================
            # DEPARTMENT
            # =================================================

            if lower.startswith("department:"):

                value = line.split(":", 1)[-1].strip()

                if value:
                    data["document"]["department"] = value

            # =================================================
            # DATE
            # =================================================

            date_match = re.search(
                r"\b\d{4}-\d{2}-\d{2}\b",
                line
            )

            if date_match:

                data["document"]["report_date"] = (
                    date_match.group()
                )

        # =====================================================
        # DOCUMENT TYPE DETECTION
        # =====================================================

        full_text = text.lower()

        if "blood test" in full_text or "laboratory" in full_text:
            data["document"]["document_type"] = "laboratory_report"

        elif "prescription" in full_text:
            data["document"]["document_type"] = "prescription"

        elif (
            "x-ray" in full_text
            or "mri" in full_text
            or "ct scan" in full_text
            or "ultrasound" in full_text
        ):
            data["document"]["document_type"] = "imaging_report"

        elif "discharge summary" in full_text:
            data["document"]["document_type"] = "discharge_summary"

        elif "general check-up" in full_text:
            data["document"]["document_type"] = "general_checkup"

        else:
            data["document"]["document_type"] = "medical_document"

        return data


# =============================================================
# TEST
# =============================================================

if __name__ == "__main__":

    sample_text = """
    GENERAL CHECK-UP REPORT

    PATIENT DETAILS

    Name:
    Jane Doe

    Age:
    50

    Gender:
    Female

    Blood Group: O+

    MEDICAL HISTORY

    Hypertension, started 2015

    Surgeries: Appendectomy

    Allergies: No known allergies

    VITALS

    Blood pressure: 140/90 mmHg
    Pulse: 76 bpm
    Temperature: 36.8 C
    Respiratory rate: 16 /min
    SpO2: 97%

    DIAGNOSIS:
    Hypertension

    MEDICATIONS:
    Hydrochlorothiazide 25 mg once daily

    DOCTOR'S OBSERVATIONS:
    Alert and in no distress

    FOLLOW-UP:
    Follow-up check-up

    Dr. A. Smith

    2025-06-22
    """

    extractor = MedicalTextExtractor()

    result = extractor.extract(sample_text)

    print("\n========== STRUCTURED MEDICAL DATA ==========\n")

    print(
        json.dumps(
            result,
            indent=4,
            ensure_ascii=False
        )
    )

    print("\n==============================================\n")
    