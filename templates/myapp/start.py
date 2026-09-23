from django.http import HttpResponse
from django.shortcuts import render

def start(request):
    return HttpResponse("START VIEW IS WORKING")

def landing(request):
    return render(request, "myapp/landing.html")