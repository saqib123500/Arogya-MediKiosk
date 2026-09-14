import json
import os

from dotenv import load_dotenv
from openai import OpenAI

from ...schemas.patient import PatientState


load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


STATE_UPDATE_PROMPT = """
You are the structured patient-state extraction engine for a
multilingual AI patient intake assistant.

Your task is to read ONLY the patient's latest message and extract
every piece of patient information that is explicitly stated.

The patient's message may:
- contain multiple pieces of information
- answer several questions at once
- answer questions out of order
- use informal or conversational language
- contain corrections to previously provided information
- contain multiple languages or code-switching
- describe symptoms naturally rather than using medical terminology

IMPORTANT EXTRACTION RULES:

1. Extract ALL explicitly provided information from the latest message.

2. Do NOT extract only the answer to the question that was most recently asked.
   If the patient gives three pieces of information, extract all three.

3. Never guess, assume, diagnose, or infer information that the patient did
   not explicitly provide.

4. If a field is not mentioned in the latest message, DO NOT include that
   field in the output.

5. Preserve the patient's intended meaning.

6. If the patient explicitly corrects previously provided information,
   return the corrected value.

7. The latest explicit correction takes priority over the previous value.

8. The patient may provide information in any order.

9. Do not create information from the current patient state. The current
   state is provided only to understand previous information and corrections.

10. Do not copy unchanged fields from the current state into the output.
    Return ONLY fields that need to be updated because of the latest message.

11. Chief_Complaint should preserve useful symptom information explicitly
    stated by the patient, such as:
    - symptom
    - duration
    - location
    - severity
    - associated symptoms

12. Do NOT convert a symptom into a diagnosis.
    For example, if the patient says "I have a headache", record the complaint
    as a headache. Do not infer migraine or another diagnosis.

13. Do not interpret vague information as a precise value.
    Preserve approximate or conversational wording when appropriate.

14. The following assessment fields must NEVER be guessed or inferred:
    Prakriti
    Vikriti
    Sara
    Samhanana
    Pramana
    Satmya
    Satva
    Ahara_Shakti
    Vyayama_Shakti

15. Vaya must also only be extracted when explicitly stated by the patient.

16. Age must be extracted only when the patient explicitly gives their age.

17. Gender must be extracted only when explicitly stated.

18. Contact_Number must preserve the phone number given by the patient.

19. Address must preserve the address information given by the patient.

20. Return ONLY a valid JSON object.

21. Do not include explanations, markdown, comments, or code fences.

ALLOWED FIELDS:

FullName
Age
Gender
Contact_Number
Address
Chief_Complaint
Prakriti
Vikriti
Sara
Samhanana
Pramana
Satmya
Satva
Ahara_Shakti
Vyayama_Shakti
Vaya

OUTPUT FORMAT:

Return a JSON object containing ONLY fields that were explicitly provided
or explicitly corrected in the patient's latest message.

Example:

Patient message:
"My name is Rahul, I'm 24 years old and I've had a headache for three days."

Output:
{
    "FullName": "Rahul",
    "Age": 24,
    "Chief_Complaint": "headache for three days"
}

Another example:

Patient message:
"Actually, I'm 25, not 24."

Output:
{
    "Age": 25
}

Another example:

Patient message:
"I live in Mumbai and my number is 9876543210."

Output:
{
    "Address": "Mumbai",
    "Contact_Number": "9876543210"
}

Another example:

Patient message:
"I have a headache since Monday and it's quite severe."

Output:
{
    "Chief_Complaint": "headache since Monday, quite severe"
}
"""


def extract_state_updates(
    patient_message: str,
    current_state: PatientState,
) -> dict:
    """
    Extract all explicitly provided patient information
    from the latest patient message.
    """

    current_state_json = current_state.model_dump(
        exclude_none=True
    )

    prompt = f"""
CURRENT PATIENT STATE:

{json.dumps(
    current_state_json,
    ensure_ascii=False,
    indent=2,
)}

PATIENT'S LATEST MESSAGE:

{patient_message}

TASK:

Extract ALL patient information explicitly provided in the
latest message.

The patient may provide multiple fields at once.

Return ONLY the fields that should be updated because of
the latest message.
"""

    response = client.responses.create(
        model="gpt-5.6-luna",
        instructions=STATE_UPDATE_PROMPT,
        input=prompt,
    )

    raw_output = response.output_text.strip()

    try:
        updates = json.loads(raw_output)

    except json.JSONDecodeError:
        raise ValueError(
            f"LLM returned invalid JSON: {raw_output}"
        )

    if not isinstance(updates, dict):
        raise ValueError(
            "State updates must be a JSON object."
        )

    allowed_fields = set(
        PatientState.model_fields.keys()
    )

    return {
        key: value
        for key, value in updates.items()
        if key in allowed_fields
    }
    
    