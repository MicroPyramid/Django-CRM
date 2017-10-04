from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt


@login_required
def home(request):
    return render(request, 'index.html')


@csrf_exempt
def login(request):
    return render(request, 'login.html')
