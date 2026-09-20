from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.cache import never_cache

from myapp.models import Patient, Token


@login_required
@never_cache
def index(request):
    total_patients = Patient.objects.count()
    recent_patients = Patient.objects.all().order_by('-created_at')[:5]

    today = timezone.localdate()

    # Today's appointments, grouped by doctor in the template via {% regroup %}.
    # Cancelled tokens are excluded — they aren't a "live" appointment anymore.
    todays_tokens = (
        Token.objects
        .filter(date=today)
        .exclude(status="cancelled")
        .select_related("doctor", "patient")
        .order_by("doctor__name", "token_number")
    )

    return render(request, 'myapp/index.html', {
        'total_patients': total_patients,
        'recent_patients': recent_patients,
        'today': today,
        'todays_tokens': todays_tokens,
    })