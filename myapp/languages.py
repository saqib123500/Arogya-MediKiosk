# myapp/languages.py

def store_patient_language(request, language):
    """
    Store the patient's selected language in the current session.
    """

    if language:
        request.session["patient_language"] = language
        request.session.modified = True

    return language


def get_patient_language(request):
    """
    Get the patient's previously selected language.
    Defaults to English.
    """

    return request.session.get("patient_language", "en")