from urllib import request
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.timezone import localtime
from .models import Attendance
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from .models import Leave
from datetime import date
from django.contrib.admin.views.decorators import staff_member_required



@csrf_exempt
def login_view(request):
    if request.method == "POST":
        username = request.POST['username']
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            return redirect('dashboard')
        else:
            return render(request, 'attendance/login.html', 
             { 'error': 'Invalid credentials',
                'show_create': User.objects.count() == 0
            })

    return render(request, 'attendance/login.html', {
        'show_create': User.objects.count() == 0
    })



def is_admin(user):
    return user.is_superuser

@login_required
@user_passes_test(is_admin)
def add_user(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        email = request.POST.get("email")
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")

        if not all([username, password, email, first_name, last_name]):
            return render(request, "attendance/add_user.html", 
                          {"error": "All fields are required"})

        if User.objects.filter(username=username).exists():
            return render(request, "attendance/add_user.html", 
                          {"error": "Username already exists"})
        
        user = User.objects.create_user(
            username=username,
            password=password,
            email=email,
            first_name=first_name,
            last_name=last_name
        )
        login(request, user)
        return redirect('dashboard')
    
    return render(request, "attendance/add_user.html")



def is_admin(user):
    return user.is_authenticated and user.is_superuser

@login_required
@user_passes_test(is_admin)
def deactivate_user(request, user_id):
    user = get_object_or_404(User, id=user_id)

    # prevent admin deleting himself
    if user == request.user:
        return redirect('dashboard')

    user.is_active = False
    user.save()

    return redirect('dashboard')


@login_required
@user_passes_test(is_admin)
def activate_user(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if user == request.user:
        return redirect('dashboard')

    user.is_active = True
    user.save()
    return redirect('dashboard')

@login_required
@user_passes_test(is_admin)
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)

    # prevent admin deleting himself
    if user == request.user:
        return redirect('dashboard')

    user.delete()
    return redirect('dashboard')

@login_required
def dashboard(request):
    today = timezone.now().date()
    attendance, created = Attendance.objects.get_or_create(
        user=request.user,
        date=today
    )

    if request.method == "POST":
        if 'clock_in' in request.POST:
            attendance.clock_in = localtime(timezone.now()).time()
            attendance.save()

        if 'clock_out' in request.POST:
            attendance.clock_out = localtime(timezone.now()).time()
            attendance.save()

    records = Attendance.objects.filter(user=request.user).order_by('-date')
    users = User.objects.filter(is_superuser=False)

    return render(request, 'attendance/dashboard.html', {
        'attendance': attendance,
        'records': records,
        'users': users
        })



@login_required
def request_leave(request):
    if request.method == "POST":
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        reason = request.POST.get("reason")

        if start_date > end_date:
            messages.error(request, "End date must be after start date.")
            return redirect("request_leave")

        Leave.objects.create(
            user=request.user,
            start_date=start_date,
            end_date=end_date,
            reason=reason
        )

        messages.success(request, "Leave request submitted successfully.")
        return redirect("dashboard")

    return render(request, "attendance/request_leave.html")







@login_required
@user_passes_test(is_admin)
def staff_attendance(request, user_id):
    user = get_object_or_404(User, id=user_id)
    records = Attendance.objects.filter(user=user).order_by('-date')
    return render(request, 'attendance/staff_attendance.html', {
        'records': records,
        'user': user
    })


@staff_member_required
def manage_leaves(request):
    leaves = Leave.objects.all().order_by("-created_at")
    return render(request, "attendance/manage_leaves.html", {"leaves": leaves})

@staff_member_required
def update_leave_status(request, leave_id, status):
    leave = Leave.objects.get(id=leave_id)

    if status in ["Approved", "Rejected"]:
        leave.status = status
        leave.approved_by = request.user
        leave.save()

    return redirect("manage_leaves")




def logout_view(request):
    logout(request)
    return redirect('login')




