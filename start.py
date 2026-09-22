from django.shortcuts import render


def start(request):
    return render(request, "myapp/start.html")


def landing(request):
    return render(request, "myapp/landing.html")
