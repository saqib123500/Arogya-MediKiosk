"""
medical_document_extractor.py
============================================================

Medical information extraction layer for Arogya-MediKiosk.

Responsibilities:
    OCR text
        ↓
    document classification
        ↓
    medical information extraction
        ↓
    validated structured data

This module intentionally DOES NOT store patient-identifying
metadata such as:

    - patient name
    - age
    - sex/gender
    - patient ID
    - ABHA ID
    - phone number
    - address
    - clinic/hospital name
    - doctor name

The complete OCR text should remain separately in
MedicalDocument.raw_text.

Packages used:
    - re
    - rapidfuzz
    - pydantic
    - pandas
    - dateparser
"""

import re
from typing import List, Optional, Dict, Any, Tuple

import pandas as pd
import dateparser
from rapidfuzz import fuzz, process
from pydantic import BaseModel, Field


# ============================================================
# GENERAL UTILITIES
# ============================================================

def clean_text(value: str) -> str:
    """Normalize OCR text without destroying useful information."""
    if value is None:
        return ""

    value = str(value)
    value = value.replace("\r", "\n")
    # Normalize common OCR bullet characters.
    value = re.sub(r"^[¢©®•●◦▪■«»]+", "", value)
    # Normalize whitespace.
    value = re.sub(r"[ \t]+", " ", value)
    # Remove excessive blank lines.
    value = re.sub(r"\n{3,}", "\n\n", value)

    return value.strip()


def clean_line(value: str) -> str:
    """Clean a single OCR line."""
    value = clean_text(value)
    value = value.strip(" :-|,.;")
    return value


def unique_strings(values: List[str]) -> List[str]:
    """Remove duplicate strings while preserving order."""
    result = []
    seen = set()
    for value in values:
        value = clean_line(value)
        if not value:
            continue
        key = value.lower()
        if key not in seen:
            seen.add(key)
            result.append(value)
    return result


def split_lines(text: str) -> List[str]:
    """Convert OCR text into useful non-empty lines."""
    lines = []
    for line in clean_text(text).splitlines():
        line = line.strip()
        if not line:
            continue
        line = re.sub(r"[ \t]+", " ", line)
        line = line.strip(" :-|,.;")
        if line:
            lines.append(line)
    return lines


# ============================================================
# PYDANTIC DATA MODELS
# ============================================================

class Medication(BaseModel):
    name: str
    form: str = ""
    strength: str = ""
    dose: str = ""
    frequency: str = ""
    duration: str = ""
    route: str = ""
    instructions: str = ""
    raw_text: str = ""


class LabResult(BaseModel):
    test_name: str
    value: str = ""
    unit: str = ""
    reference_range: str = ""
    flag: str = ""
    raw_text: str = ""


class VitalSign(BaseModel):
    name: str
    value: str
    unit: str = ""
    raw_text: str = ""


class MedicalExtraction(BaseModel):
    """Final structured medical information."""
    document_type: str = "Medical Document"
    report_date: str = ""
    diagnosis: List[str] = Field(default_factory=list)
    symptoms: List[str] = Field(default_factory=list)
    medications: List[Medication] = Field(default_factory=list)
    allergies: List[str] = Field(default_factory=list)
    vital_signs: List[VitalSign] = Field(default_factory=list)
    lab_results: List[LabResult] = Field(default_factory=list)
    imaging_findings: List[str] = Field(default_factory=list)
    clinical_findings: List[str] = Field(default_factory=list)
    impression: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    other_significant_information: List[str] = Field(default_factory=list)


# ============================================================
# MEDICATION VOCABULARY
# ============================================================

KNOWN_MEDICINES = [
    "CALPOL", "DELCON", "LEVOLIN", "MEFTAL-P", "PARACETAMOL",
    "ACETAMINOPHEN", "IBUPROFEN", "AMOXICILLIN", "AZITHROMYCIN",
    "CETIRIZINE", "LEVOCETIRIZINE", "MONTELUKAST", "OMEPRAZOLE",
    "PANTOPRAZOLE", "ONDANSETRON", "DOMPERIDONE", "METFORMIN",
    "AMLODIPINE", "LOSARTAN", "ATORVASTATIN", "ASPIRIN",
    "INSULIN", "SALBUTAMOL", "BUDESONIDE", "FORMOTEROL",
]

MEDICATION_FORMS = {
    "syp": "Syrup", "syrup": "Syrup",
    "tab": "Tablet", "tablet": "Tablet",
    "cap": "Capsule", "capsule": "Capsule",
    "inj": "Injection", "injection": "Injection",
    "drop": "Drops", "drops": "Drops",
    "cream": "Cream", "ointment": "Ointment",
    "gel": "Gel", "lotion": "Lotion",
    "solution": "Solution", "suspension": "Suspension",
    "powder": "Powder", "sachet": "Sachet",
    "patch": "Patch", "spray": "Spray",
    "inhaler": "Inhaler",
}


# ============================================================
# EXTRACTION HELPERS
# ============================================================

def correct_medicine_name(candidate: str) -> str:
    candidate = clean_line(candidate)
    if not candidate: return ""
    normalized = re.sub(r"[^A-Za-z0-9\-]", "", candidate).upper()
    if not normalized: return ""

    for medicine in KNOWN_MEDICINES:
        if normalized == re.sub(r"[^A-Za-z0-9\-]", "", medicine).upper():
            return medicine

    matches = process.extract(normalized, KNOWN_MEDICINES, scorer=fuzz.ratio, limit=1)
    if matches and matches[0][1] >= 85:
        return matches[0][0]
    return candidate

def extract_form(text: str) -> str:
    lower_text = text.lower()
    for keyword, form in MEDICATION_FORMS.items():
        if re.search(rf"\b{re.escape(keyword)}\b", lower_text):
            return form
    return ""

def extract_strength(text: str) -> str:
    # (250/5) or 500 mg or 100 mcg/5ml
    match = re.search(r"\(\s*(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)\s*\)", text, re.IGNORECASE)
    if match: return f"{match.group(1)} mg/{match.group(2)} mL"
    
    match = re.search(r"\b(\d+(?:\.\d+)?)\s*(mg|mcg|µg|ug|g|IU)\s*(?:/\s*(\d+(?:\.\d+)?)\s*(ml|mL))?\b", text, re.IGNORECASE)
    if match:
        val, unit, vol, vol_unit = match.groups()
        unit = "mcg" if unit.lower() in ("µg", "ug") else unit
        return f"{val} {unit}/{vol} {vol_unit}" if vol else f"{val} {unit}"
    return ""

def extract_dose(text: str) -> str:
    match = re.search(r"\b(\d+(?:\.\d+)?)\s*(ml|mL|tablet|tab|capsule|cap|drop|puff)s?\b", text, re.IGNORECASE)
    if match: return f"{match.group(1)} {match.group(2).lower()}"
    return ""

def extract_frequency(text: str) -> str:
    patterns = {
        r"\b(TDS|TID)\b": "Three times daily",
        r"\b(BD|BID)\b": "Twice daily",
        r"\b(OD)\b": "Once daily",
        r"\b(QID)\b": "Four times daily",
        r"\b(SOS)\b": "As needed (SOS)",
        r"\b(every\s+\d+\s*hours?)\b": "Every X hours", # Simplified
    }
    for pat, val in patterns.items():
        if re.search(pat, text, re.IGNORECASE): return val
    
    match = re.search(r"\bQ\s*(\d+)\s*H\b", text, re.IGNORECASE)
    if match: return f"Every {match.group(1)} hours"
    return ""

def extract_duration(text: str) -> str:
    match = re.search(r"\bx\s*(\d+)\s*(d|day|week|month)s?\b", text, re.IGNORECASE)
    if match: return f"{match.group(1)} {match.group(2).lower()}s"
    return ""

def extract_route(text: str) -> str:
    routes = {"oral": r"oral|PO|by mouth", "iv": r"intravenous|IV", "im": r"intramuscular|IM", "sc": r"subcutaneous|SC"}
    for route, pat in routes.items():
        if re.search(rf"\b({pat})\b", text, re.IGNORECASE): return route
    return ""

def extract_instructions(text: str) -> str:
    instructions = []
    patterns = {"After food": r"after\s+food", "Before food": r"before\s+food", "With food": r"with\s+food", "At bedtime": r"at\s+bedtime"}
    for val, pat in patterns.items():
        if re.search(pat, text, re.IGNORECASE): instructions.append(val)
    return ", ".join(instructions)


# ============================================================
# MAIN EXTRACTION LOGIC
# ============================================================

def looks_like_medication_start(line: str) -> bool:
    """Determines if a line marks the beginning of a medication entry."""
    lower = line.lower()
    # 1. Contains a known medicine
    for med in KNOWN_MEDICINES:
        if re.search(rf"\b{re.escape(med.lower())}\b", lower): return True
    # 2. Starts with a medicine form
    for form in MEDICATION_FORMS:
        if re.search(rf"^\s*{re.escape(form)}\b", lower): return True
    return False

def extract_medications(lines: List[str]) -> List[Medication]:
    meds = []
    current_med = None

    for line in lines:
        line_c = clean_line(line)
        if not line_c: continue

        if looks_like_medication_start(line_c):
            if current_med: meds.append(current_med)
            
            name = extract_medicine_name(line_c)
            current_med = Medication(
                name=name or "Unknown Medication",
                form=extract_form(line_c),
                strength=extract_strength(line_c),
                dose=extract_dose(line_c),
                frequency=extract_frequency(line_c),
                duration=extract_duration(line_c),
                route=extract_route(line_c),
                instructions=extract_instructions(line_c),
                raw_text=line_c
            )
        elif current_med:
            # Merge missing details into current medication
            s = extract_strength(line_c)
            if s and not current_med.strength: current_med.strength = s
            d = extract_dose(line_c)
            if d and not current_med.dose: current_med.dose = d
            f = extract_frequency(line_c)
            if f and not current_med.frequency: current_med.frequency = f
            dr = extract_duration(line_c)
            if dr and not current_med.duration: current_med.duration = dr
            r = extract_route(line_c)
            if r and not current_med.route: current_med.route = r
            i = extract_instructions(line_c)
            if i: current_med.instructions = (current_med.instructions + ", " + i) if current_med.instructions else i
            current_med.raw_text += " " + line_c

    if current_med: meds.append(current_med)
    return meds

def extract_medicine_name(text: str) -> str:
    # Remove prefixes, strengths, and frequencies to isolate name
    val = re.sub(r"^\s*\d+[\.\)\-:]\s*", "", text)
    val = re.sub(r"^\s*(?:SYP|TAB|CAP|INJ|DROP|CREAM|GEL|Syp|Tab|Cap|Inj)\.?\s+", "", val, flags=re.IGNORECASE)
    val = re.sub(r"\(\s*\d+.*?\)", " ", val)
    val = re.sub(r"\b\d+.*?(mg|mcg|g|IU|ml)\b", " ", val, flags=re.IGNORECASE)
    val = re.sub(r"\b(?:TDS|TID|BD|BID|OD|QID|SOS|Q\d+H)\b", " ", val, flags=re.IGNORECASE)
    val = clean_line(val)
    
    # Try known meds first
    for word in val.split():
        corrected = correct_medicine_name(word)
        if corrected in KNOWN_MEDICINES: return corrected
    
    return val if val else "Unknown Medication"

def extract_labs(lines: List[str]) -> List[LabResult]:
    results = []
    for line in lines:
        for test in COMMON_LAB_TESTS:
            if re.search(rf"\b{re.escape(test)}\b", line, re.IGNORECASE):
                # Look for a number in the line
                match = re.search(r"(\d+(?:\.\d+)?)", line)
                if match:
                    val = match.group(1)
                    # Try to find unit
                    unit_match = re.search(r"([A-Za-z/µμ%]+)", line[match.end():])
                    unit = unit_match.group(1) if unit_match else ""
                    # Flag
                    flag = "High" if re.search(r"\b(High|H|Elevated)\b", line, re.IGNORECASE) else \
                            "Low" if re.search(r"\b(Low|L|Decreased)\b", line, re.IGNORECASE) else ""
                    
                    results.append(LabResult(
                        test_name=normalize_lab_name(test),
                        value=val,
                        unit=unit,
                        flag=flag,
                        raw_text=line
                    ))
                    break
    return results

def extract_vitals(lines: List[str]) -> List[VitalSign]:
    vitals = []
    patterns = {
        "Blood Pressure": r"BP\s*[:\-]?\s*(\d{2,3}/\d{2,3})",
        "Heart Rate": r"(?:HR|Pulse)\s*[:\-]?\s*(\d{2,3})",
        "Temperature": r"(?:Temp)\s*[:\-]?\s*(\d+(?:\.\d+)?)",
        "SpO2": r"SpO2\s*[:\-]?\s*(\d{2,3})",
    }
    for name, pat in patterns.items():
        for line in lines:
            match = re.search(pat, line, re.IGNORECASE)
            if match:
                vitals.append(VitalSign(name=name, value=match.group(1), raw_text=line))
                break
    return vitals

def extract_section_content(lines: List[str], keywords: List[str]) -> List[str]:
    content = []
    inside = False
    for line in lines:
        # Flexible heading check: allow non-alphanumeric OCR noise before the keyword
        if any(re.search(rf"^\s*[^a-zA-Z0-9]*{re.escape(k)}", line, re.IGNORECASE) for k in keywords):
            inside = True
            # If the line contains text after the heading (e.g., "Impression: Normal"), keep that text
            for k in keywords:
                match = re.search(rf"{re.escape(k)}\s*[:\-]?\s*(.+)$", line, re.IGNORECASE)
                if match:
                    content.append(match.group(1))
                    break
            continue
        if inside:
            # Stop if we hit another major section
            if any(re.search(rf"^\s*[^a-zA-Z0-9]*{re.escape(k)}", line, re.IGNORECASE) for k in ["Findings", "Impression", "Diagnosis", "Medications", "History", "Conclusion", "Observation"]):
                break
            content.append(line)
    return unique_strings(content)

def normalize_lab_name(candidate: str) -> str:
    match = process.extractOne(candidate, COMMON_LAB_TESTS, scorer=fuzz.ratio)
    return match[0].upper() if match and match[1] >= 85 else candidate.upper()

# ============================================================
# MAIN API
# ============================================================

def extract_medical_document(text: str) -> MedicalExtraction:
    text = clean_text(text)
    if not text: return MedicalExtraction()
    lines = split_lines(text)

    # Classification
    doc_type = "Medical Document"
    if any(term in text.lower() for term in ["ct scan", "mri", "x-ray", "ultrasound"]): doc_type = "Radiology Report"
    elif any(term in text.lower() for term in ["hemoglobin", "glucose", "creatinine"]): doc_type = "Laboratory Report"
    elif any(term in text.lower() for term in ["prescription", "tablet", "syrup"]): doc_type = "Prescription"

    # Date
    date_match = re.search(r"(\d{1,2}\s+[A-Za-z]{3,9},?\s+\d{2,4})", text)
    report_date = normalize_report_date(date_match.group(1)) if date_match else ""

    imaging = extract_section_content(lines, ["Findings", "Observations", "Observation"])
    clinical = extract_section_content(lines, ["Clinical Examination", "Examination"])
    impression = extract_section_content(lines, ["Impression", "Conclusion", "Conclusions"])

    # Fallback: If no structured findings were found, search for medical keywords across the text
    other_info = extract_other_significant_information(lines)
    if not imaging and not clinical and not impression:
        keywords = ["fracture", "swelling", "abnormality", "hemorrhage", "hematoma", "lesion", "mass", "clear"]
        for line in lines:
            if any(k in line.lower() for k in keywords):
                other_info.append(line)

    return MedicalExtraction(
        document_type=doc_type,
        report_date=report_date,
        diagnosis=extract_label_values(lines, ["diagnosis", "diagnosed with"]),
        symptoms=extract_label_values(lines, ["symptoms", "complaints"]),
        medications=extract_medications(lines),
        allergies=extract_label_values(lines, ["allergies", "allergic to"]),
        vital_signs=extract_vitals(lines),
        lab_results=extract_labs(lines),
        imaging_findings=imaging,
        clinical_findings=clinical,
        impression=impression,
        recommendations=extract_section_content(lines, ["Recommendations", "Advice"]),
        other_significant_information=unique_strings(other_info)
    )

def extract_significant_information(text: str) -> dict:
    return extract_medical_document(text).model_dump()

def extract_medical_document_json(text: str) -> dict:
    return extract_significant_information(text)

# Re-using helper functions from original for compatibility
def extract_label_values(lines, labels):
    res = []
    for line in lines:
        for l in labels:
            # Allow some OCR noise at the start of the line
            if re.search(rf"^\s*[^a-zA-Z0-9]*{re.escape(l)}\s*[:\-]\s*(.+)$", line, re.IGNORECASE):
                res.append(line.split(":", 1)[-1].strip())
    return unique_strings(res)

def extract_other_significant_information(lines):
    keywords = ["history", "remarks", "comments"]
    res = []
    for line in lines:
        if any(k in line.lower() for k in keywords): res.append(line)
    return unique_strings(res)

def normalize_report_date(text: str) -> str:
    parsed = dateparser.parse(text)
    return parsed.strftime("%d %b %Y") if parsed else text

# ============================================================
# LAB TEST LIST (Copied from original for completeness)
# ============================================================
COMMON_LAB_TESTS = [
    "hemoglobin", "haemoglobin", "hb", "wbc", "white blood cell", "tlc", "rbc", 
    "platelet", "neutrophils", "lymphocytes", "monocytes", "eosinophils", "basophils", 
    "esr", "crp", "glucose", "fbs", "rbs", "hba1c", "creatinine", "urea", 
    "sodium", "potassium", "chloride", "calcium", "bilirubin", "sgot", "sgpt", 
    "alp", "albumin", "cholesterol", "triglycerides", "hdl", "ldl", "tsh", 
    "t3", "t4", "vitamin d", "vitamin b12", "ferritin", "iron"
]

# Update to myapp/services/medical_document_extractor.py

# 1. Add a Noise Cleaning function
def clean_ocr_noise(text: str) -> str:
    """Remove common OCR artifacts to make the text more readable."""
    # Remove lone symbols and common OCR noise
    text = re.sub(r"['`\"‘’„]", "", text) # Remove quotes/ticks
    text = re.sub(r"\b[A-Z]\b", "", text) # Remove lone uppercase letters (often OCR noise)
    text = re.sub(r"\s+", " ", text) # Normalize whitespace
    return text.strip()

# 2. Update extract_section_content to use Fuzzy Matching
def extract_section_content(lines: List[str], keywords: List[str]) -> List[str]:
    content = []
    inside = False
    
    for line in lines:
        line_c = clean_line(line)
        if not line_c: continue
        
        # Check if the line starts with something similar to our keywords
        # We split the line and check the first word's similarity to any keyword
        first_word = line_c.split()[0] if line_c.split() else ""
        best_match = None
        highest_score = 0
        
        for k in keywords:
            score = fuzz.ratio(first_word.lower(), k.lower())
            if score > 70 and score > highest_score:
                highest_score = score
                best_match = k
        
        if best_match:
            inside = True
            # Extract text after the header
            # Try to find the actual keyword or the fuzzy match in the line
            match = re.search(rf"({re.escape(first_word)})\s*[:\-]?\s*(.+)$", line_c, re.IGNORECASE)
            if match:
                content.append(match.group(2))
            continue
            
        if inside:
            # Stop if we hit another major section (using fuzzy matching again)
            major_headers = ["Findings", "Impression", "Diagnosis", "Medications", "History", "Conclusion"]
            for mh in major_headers:
                if fuzz.ratio(first_word.lower(), mh.lower()) > 80:
                    inside = False
                    break
            
            if inside:
                content.append(line_c)
                
    return unique_strings([clean_ocr_noise(s) for s in content])

# 3. Update extract_medical_document fallback
# In the fallback section:
# instead of: other_info.append(line)
# use: other_info.append(clean_ocr_noise(line))

# Update to myapp/services/medical_document_extractor.py

def extract_medications(lines: List[str]) -> List[Medication]:
    """
    HEAVY-DUTY SPOTTER:
    Instead of parsing lines, this scans every word in the document
    against the KNOWN_MEDICINES list using fuzzy matching.
    """
    meds = []
    
    for line in lines:
        # Split line into individual 'chunks' of text
        words = line.split()
        
        for word in words:
            # Clean the word of common OCR noise (e.g., 'EOLPOL' -> 'CALPOL')
            clean_word = re.sub(r"[^A-Za-z0-9]", "", word).upper()
            if not clean_word: continue
            
            # Fuzzy match against known medicines
            # We use a slightly lower threshold (80) to catch misspellings like 'EOLPOL'
            match = process.extractOne(clean_word, KNOWN_MEDICINES, scorer=fuzz.ratio)
            
            if match and match[1] >= 80:
                medicine_name = match[0]
                
                # Once we find a medicine name, we look at the surrounding words 
                # in the original line to find dose/frequency/form
                med = Medication(
                    name=medicine_name,
                    form=extract_form(line),
                    strength=extract_strength(line),
                    dose=extract_dose(line),
                    frequency=extract_frequency(line),
                    duration=extract_duration(line),
                    route=extract_route(line),
                    instructions=extract_instructions(line),
                    raw_text=line
                )
                
                if not medication_exists(meds, med):
                    meds.append(med)
                    
    return meds

