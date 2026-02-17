from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone
from .models import Attendance
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def login_view(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']
        print(f"Attempting login for user: {username}")

        user = authenticate(request, username=username, password=password)
        if user:
            print(f"User authenticated: {user}")
            login(request, user)
            return redirect('dashboard')
        else:
            print("Authentication failed")
            return render(request, 'attendance/login.html', {'error': 'Invalid credentials'})

    return render(request, 'attendance/login.html')



@login_required
def dashboard(request):
    today = timezone.now().date()
    attendance, created = Attendance.objects.get_or_create(
        user=request.user,
        date=today
    )

    if request.method == "POST":
        if 'clock_in' in request.POST:
            attendance.clock_in = timezone.now().time()
            attendance.save()

        if 'clock_out' in request.POST:
            attendance.clock_out = timezone.now().time()
            attendance.save()

    records = Attendance.objects.filter(user=request.user).order_by('-date')
    return render(request, 'attendance/dashboard.html', {
        'attendance': attendance,
        'records': records
    })


def logout_view(request):
    logout(request)
    return redirect('login')

#@login_required

