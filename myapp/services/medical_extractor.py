import re


def clean_value(value):
    """Clean OCR text while preserving useful medical information."""

    value = value.strip()

    value = re.sub(r"\s+", " ", value)

    value = value.strip(" :-|")

    return value


def add_unique(data, category, value):
    """Add a value without creating duplicates."""

    value = clean_value(value)

    if value and value not in data[category]:
        data[category].append(value)


def extract_after_label(lines, labels):
    """
    Find values appearing after labels such as:
    Diagnosis:
    Medication:
    Impression:
    """

    results = []

    pattern = re.compile(
        r"^(?:" +
        "|".join(re.escape(label) for label in labels) +
        r")\s*[:\-]?\s*(.+)$",
        re.IGNORECASE
    )

    for line in lines:

        match = pattern.match(line)

        if match:
            value = clean_value(match.group(1))

            if value:
                results.append(value)

    return results


def extract_significant_information(text):
    """
    Extract medically significant information from OCR text.

    This is a rule-based extractor.
    It does NOT diagnose the patient or infer information.
    It only extracts information explicitly present in the OCR text.
    """

    data = {
        "document_type": "",
        "report_date": "",

        "patient_information": [],

        "diagnosis": [],
        "symptoms": [],
        "medications": [],
        "allergies": [],

        "vital_signs": [],
        "blood_tests": [],
        "urine_tests": [],
        "imaging_findings": [],

        "abnormal_findings": [],

        "clinical_findings": [],
        "recommendations": [],

        "other_significant_information": [],
    }

    if not text:
        return data

    # ---------------------------------------------------------
    # NORMALIZE TEXT
    # ---------------------------------------------------------

    text = text.replace("\r", "\n")

    lines = [
        clean_value(line)
        for line in text.splitlines()
        if clean_value(line)
    ]

    lower_text = text.lower()

    # ---------------------------------------------------------
    # DOCUMENT TYPE
    # ---------------------------------------------------------

    document_types = [
        ("blood report", "Blood Report"),
        ("cbc", "CBC Report"),
        ("complete blood count", "CBC Report"),
        ("lipid profile", "Lipid Profile"),
        ("liver function test", "Liver Function Test"),
        ("lft", "Liver Function Test"),
        ("kidney function test", "Kidney Function Test"),
        ("kft", "Kidney Function Test"),
        ("renal function test", "Kidney Function Test"),
        ("thyroid function test", "Thyroid Function Test"),
        ("thyroid profile", "Thyroid Profile"),
        ("urine routine", "Urine Test"),
        ("urine examination", "Urine Test"),
        ("urinalysis", "Urine Test"),
        ("x-ray", "X-Ray Report"),
        ("xray", "X-Ray Report"),
        ("mri", "MRI Report"),
        ("ct scan", "CT Scan Report"),
        ("computed tomography", "CT Scan Report"),
        ("ultrasound", "Ultrasound Report"),
        ("sonography", "Ultrasound Report"),
        ("echocardiogram", "Echocardiogram"),
        ("ecg", "ECG Report"),
        ("electrocardiogram", "ECG Report"),
        ("prescription", "Prescription"),
        ("medical report", "Medical Report"),
        ("laboratory report", "Laboratory Report"),
        ("lab report", "Laboratory Report"),
        ("diagnostic report", "Diagnostic Report"),
        ("pathology report", "Pathology Report"),
    ]

    for keyword, document_type in document_types:

        if keyword in lower_text:

            data["document_type"] = document_type

            break

    # ---------------------------------------------------------
    # DATE
    # ---------------------------------------------------------

    date_patterns = [
        r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b",
        r"\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b",

        r"\b\d{1,2}\s+"
        r"(?:jan|january|feb|february|mar|march|apr|april|"
        r"may|jun|june|jul|july|aug|august|sep|september|"
        r"oct|october|nov|november|dec|december)"
        r"\s+\d{2,4}\b",
    ]

    for pattern in date_patterns:

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            data["report_date"] = match.group()

            break

    # ---------------------------------------------------------
    # PATIENT INFORMATION
    # ---------------------------------------------------------

    patient_labels = [
        "patient name",
        "patient",
        "name",
        "age",
        "gender",
        "sex",
        "patient id",
        "patient no",
        "patient number",
        "mr no",
        "mrn",
        "uhid",
        "abha id",
    ]

    patient_pattern = re.compile(
        r"^(?:" +
        "|".join(re.escape(label) for label in patient_labels) +
        r")\s*[:#\-]?\s*(.+)$",
        re.IGNORECASE
    )

    for line in lines:

        match = patient_pattern.match(line)

        if match:

            value = clean_value(match.group(1))

            if value:
                add_unique(
                    data,
                    "patient_information",
                    value
                )

    # ---------------------------------------------------------
    # DIAGNOSIS
    # ---------------------------------------------------------

    diagnosis_labels = [
        "diagnosis",
        "clinical diagnosis",
        "diagnosed with",
        "final diagnosis",
        "provisional diagnosis",
    ]

    for value in extract_after_label(
        lines,
        diagnosis_labels
    ):

        add_unique(
            data,
            "diagnosis",
            value
        )

    # ---------------------------------------------------------
    # SYMPTOMS
    # ---------------------------------------------------------

    symptom_labels = [
        "symptom",
        "symptoms",
        "chief complaint",
        "chief complaints",
        "presenting complaint",
        "complaint",
        "complaints",
        "presenting symptoms",
    ]

    for value in extract_after_label(
        lines,
        symptom_labels
    ):

        add_unique(
            data,
            "symptoms",
            value
        )

    # ---------------------------------------------------------
    # MEDICATIONS
    # ---------------------------------------------------------

    medication_labels = [
        "medication",
        "medications",
        "medicine",
        "medicines",
        "drug",
        "drugs",
        "prescription",
        "prescribed medication",
        "current medication",
        "current medications",
        "treatment",
    ]

    for value in extract_after_label(
        lines,
        medication_labels
    ):

        add_unique(
            data,
            "medications",
            value
        )

    # Also detect common dosage patterns.

    dosage_pattern = re.compile(
        r"\b"
        r"[A-Za-z][A-Za-z0-9\-]*"
        r"(?:\s+[A-Za-z][A-Za-z0-9\-]*)?"
        r"\s+"
        r"\d+(?:\.\d+)?"
        r"\s*(?:mg|mcg|g|ml|iu)"
        r"(?:\s+(?:once|twice|thrice|daily|"
        r"od|bd|tds|tid|qid|hs|before|after)"
        r"[A-Za-z\s]*)?",
        re.IGNORECASE
    )

    for line in lines:

        if dosage_pattern.search(line):

            if any(
                word in line.lower()
                for word in [
                    "tablet",
                    "tab",
                    "capsule",
                    "cap",
                    "syrup",
                    "medicine",
                    "medication",
                    "mg",
                    "mcg",
                ]
            ):

                add_unique(
                    data,
                    "medications",
                    line
                )

    # ---------------------------------------------------------
    # ALLERGIES
    # ---------------------------------------------------------

    allergy_labels = [
        "allergy",
        "allergies",
        "allergic to",
        "drug allergy",
        "drug allergies",
    ]

    for value in extract_after_label(
        lines,
        allergy_labels
    ):

        add_unique(
            data,
            "allergies",
            value
        )

    # ---------------------------------------------------------
    # BLOOD PRESSURE
    # ---------------------------------------------------------

    bp_pattern = re.compile(
        r"(?:blood\s*pressure|BP)"
        r"\s*[:\-]?\s*"
        r"(\d{2,3})\s*/\s*(\d{2,3})"
        r"(?:\s*mmHg)?",
        re.IGNORECASE
    )

    for line in lines:

        match = bp_pattern.search(line)

        if match:

            add_unique(
                data,
                "vital_signs",
                f"Blood Pressure: "
                f"{match.group(1)}/{match.group(2)} mmHg"
            )

    # ---------------------------------------------------------
    # HEART RATE / PULSE
    # ---------------------------------------------------------

    heart_pattern = re.compile(
        r"(?:heart\s*rate|pulse|HR)"
        r"\s*[:\-]?\s*"
        r"(\d{2,3})"
        r"\s*(?:bpm)?",
        re.IGNORECASE
    )

    for line in lines:

        match = heart_pattern.search(line)

        if match:

            add_unique(
                data,
                "vital_signs",
                f"Heart Rate: {match.group(1)} bpm"
            )

    # ---------------------------------------------------------
    # TEMPERATURE
    # ---------------------------------------------------------

    temperature_pattern = re.compile(
        r"(?:temperature|temp)"
        r"\s*[:\-]?\s*"
        r"(\d{2,3}(?:\.\d+)?)"
        r"\s*°?\s*([CF])?",
        re.IGNORECASE
    )

    for line in lines:

        match = temperature_pattern.search(line)

        if match:

            unit = match.group(2) or "C"

            add_unique(
                data,
                "vital_signs",
                f"Temperature: "
                f"{match.group(1)} °{unit.upper()}"
            )

    # ---------------------------------------------------------
    # OXYGEN SATURATION
    # ---------------------------------------------------------

    oxygen_pattern = re.compile(
        r"(?:SpO2|SpO₂|oxygen\s+saturation|O2\s+saturation)"
        r"\s*[:\-]?\s*"
        r"(\d{2,3})\s*%?",
        re.IGNORECASE
    )

    for line in lines:

        match = oxygen_pattern.search(line)

        if match:

            add_unique(
                data,
                "vital_signs",
                f"SpO₂: {match.group(1)}%"
            )

    # ---------------------------------------------------------
    # RESPIRATORY RATE
    # ---------------------------------------------------------

    respiratory_pattern = re.compile(
        r"(?:respiratory\s*rate|respiration\s*rate|RR)"
        r"\s*[:\-]?\s*"
        r"(\d{1,3})"
        r"\s*(?:breaths/min|bpm)?",
        re.IGNORECASE
    )

    for line in lines:

        match = respiratory_pattern.search(line)

        if match:

            add_unique(
                data,
                "vital_signs",
                f"Respiratory Rate: {match.group(1)} /min"
            )

    # ---------------------------------------------------------
    # COMMON BLOOD / LAB TESTS
    # ---------------------------------------------------------

    blood_tests = [
        "hemoglobin",
        "haemoglobin",
        "hb",

        "wbc",
        "white blood cell",
        "total leukocyte count",
        "tlc",

        "rbc",
        "red blood cell",
        "red cell count",

        "platelet",
        "platelets",
        "platelet count",

        "neutrophils",
        "lymphocytes",
        "monocytes",
        "eosinophils",
        "basophils",

        "esr",
        "erythrocyte sedimentation rate",
        "crp",
        "c-reactive protein",

        "blood glucose",
        "blood sugar",
        "glucose",
        "fasting glucose",
        "fasting blood sugar",
        "fbs",
        "random glucose",
        "random blood sugar",
        "rbs",
        "postprandial glucose",
        "ppbs",
        "hba1c",
        "glycated hemoglobin",

        "creatinine",
        "serum creatinine",
        "urea",
        "blood urea",

        "sodium",
        "potassium",
        "chloride",
        "calcium",

        "bilirubin",
        "total bilirubin",
        "direct bilirubin",
        "indirect bilirubin",

        "sgot",
        "ast",
        "sgpt",
        "alt",
        "alkaline phosphatase",
        "alp",

        "albumin",
        "total protein",

        "cholesterol",
        "total cholesterol",
        "triglycerides",
        "hdl",
        "ldl",
        "vldl",

        "tsh",
        "t3",
        "t4",
        "free t3",
        "free t4",

        "vitamin d",
        "vitamin b12",
        "folate",

        "iron",
        "ferritin",
    ]

    for line in lines:

        lower_line = line.lower()

        if any(
            test in lower_line
            for test in blood_tests
        ):

            add_unique(
                data,
                "blood_tests",
                line
            )

    # ---------------------------------------------------------
    # URINE TESTS
    # ---------------------------------------------------------

    urine_keywords = [
        "urine",
        "urinalysis",
        "urine routine",
        "urine microscopy",
        "protein in urine",
        "sugar in urine",
        "pus cells",
        "rbc in urine",
        "wbc in urine",
        "epithelial cells",
        "urine culture",
    ]

    for line in lines:

        lower_line = line.lower()

        if any(
            keyword in lower_line
            for keyword in urine_keywords
        ):

            add_unique(
                data,
                "urine_tests",
                line
            )

    # ---------------------------------------------------------
    # IMAGING
    # ---------------------------------------------------------

    imaging_keywords = [
        "x-ray",
        "xray",
        "chest x-ray",
        "mri",
        "ct scan",
        "computed tomography",
        "ultrasound",
        "sonography",
        "echocardiogram",
        "echo",
        "ecg",
        "electrocardiogram",
        "scan",
        "radiology",
        "radiological",
        "imaging",
        "impression",
    ]

    for line in lines:

        lower_line = line.lower()

        if any(
            keyword in lower_line
            for keyword in imaging_keywords
        ):

            add_unique(
                data,
                "imaging_findings",
                line
            )

    # ---------------------------------------------------------
    # CLINICAL FINDINGS
    # ---------------------------------------------------------

    finding_labels = [
        "findings",
        "clinical findings",
        "examination",
        "examination findings",
        "observations",
        "clinical observation",
        "physical examination",
        "impression",
        "conclusion",
    ]

    for value in extract_after_label(
        lines,
        finding_labels
    ):

        add_unique(
            data,
            "clinical_findings",
            value
        )

    # ---------------------------------------------------------
    # RECOMMENDATIONS
    # ---------------------------------------------------------

    recommendation_labels = [
        "recommendation",
        "recommendations",
        "recommended",
        "advice",
        "advised",
        "follow up",
        "follow-up",
        "management",
        "plan",
        "treatment plan",
    ]

    for value in extract_after_label(
        lines,
        recommendation_labels
    ):

        add_unique(
            data,
            "recommendations",
            value
        )

    # ---------------------------------------------------------
    # EXPLICIT ABNORMAL FINDINGS
    # ---------------------------------------------------------

    abnormal_keywords = [
        "abnormal",
        "elevated",
        "decreased",
        "reduced",
        "increased",
        "high",
        "low",
        "critical",
        "positive",
        "out of range",
        "above normal",
        "below normal",
        "flagged",
    ]

    for line in lines:

        lower_line = line.lower()

        if any(
            keyword in lower_line
            for keyword in abnormal_keywords
        ):

            add_unique(
                data,
                "abnormal_findings",
                line
            )

    # ---------------------------------------------------------
    # LAB FLAGS: H / L / HIGH / LOW
    # ---------------------------------------------------------

    lab_flag_pattern = re.compile(
        r"(?:\s|^)"
        r"(?:H|L|HH|LL)"
        r"(?:\s|$)",
        re.IGNORECASE
    )

    for line in lines:

        if lab_flag_pattern.search(line):

            add_unique(
                data,
                "abnormal_findings",
                line
            )

    # ---------------------------------------------------------
    # OTHER SIGNIFICANT INFORMATION
    # ---------------------------------------------------------

    significant_keywords = [
        "past medical history",
        "medical history",
        "past history",
        "family history",
        "surgical history",
        "clinical history",
        "doctor notes",
        "physician notes",
        "remarks",
        "comments",
        "special instructions",
    ]

    for line in lines:

        lower_line = line.lower()

        if any(
            keyword in lower_line
            for keyword in significant_keywords
        ):

            add_unique(
                data,
                "other_significant_information",
                line
            )

    # ---------------------------------------------------------
    # REMOVE GENERIC / EMPTY VALUES
    # ---------------------------------------------------------

    for key in data:

        if isinstance(data[key], list):

            data[key] = [
                value
                for value in data[key]
                if value
            ]

    return data


