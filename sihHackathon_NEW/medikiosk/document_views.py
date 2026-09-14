from django.shortcuts import render


def medical_documents(request):

    return render(
        request,
        "medikiosk/patient/medical_documents.html"
    )