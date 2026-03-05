from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from django.utils.timezone import localtime
from .models import Attendance
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from .models import Leave
from datetime import date, time as dt_time
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login
from django.utils.timezone import now
from django.db.models import Count
import csv
from django.http import HttpResponse
from .models import Attendance
from django.http import JsonResponse
from .models import FaceData
from .facial_recognition import FacialRecognitionEngine
import json
import numpy as np    
from openpyxl import Workbook



    
    


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
    return user.is_authenticated and user.is_superuser



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
        return JsonResponse({
            "success": True,
            "message": f"User {user.username} created successfully!"
        })


    
    return render(request, "attendance/add_user.html")




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
@login_required
def request_leave(request):
    # allow users to submit a leave and also view their past requests
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
        return redirect("request_leave")

    # for GET (or after redirect) show the user's own leave requests
    leaves = Leave.objects.filter(user=request.user).order_by("-created_at")
    leave_durations = {leave.id: (leave.end_date - leave.start_date).days + 1 for leave in leaves}

    return render(request, "attendance/request_leave.html", {
        "leaves": leaves,
        "leave_durations": leave_durations,
    })







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
    # Handle adding new leave for an employee
    if request.method == "POST" and "add_leave" in request.POST:
        user_id = request.POST.get("user_id")
        start_date = request.POST.get("start_date")
        end_date = request.POST.get("end_date")
        reason = request.POST.get("reason")
        
        if user_id and start_date and end_date and reason:
            if start_date <= end_date:
                user = User.objects.get(id=user_id)
                Leave.objects.create(
                    user=user,
                    start_date=start_date,
                    end_date=end_date,
                    reason=reason,
                    status='Approved',
                    approved_by=request.user
                )
                messages.success(request, f"Leave request created successfully for {user.get_full_name() or user.username}.")
                return redirect('manage_leaves')
            else:
                messages.error(request, "End date must be after start date.")
        else:
            messages.error(request, "All fields are required.")
    
    leaves = Leave.objects.all().order_by("-created_at")
    all_users = User.objects.filter(is_superuser=False).order_by('first_name', 'last_name')
    
    # Calculate duration for each leave
    leave_durations = {}
    for leave in leaves:
        duration = (leave.end_date - leave.start_date).days + 1
        leave_durations[leave.id] = duration
    
    return render(request, "attendance/manage_leaves.html", {
        "leaves": leaves,
        "leave_durations": leave_durations,
        "all_users": all_users
    })

@staff_member_required
def update_leave_status(request, leave_id, status):
    leave = Leave.objects.get(id=leave_id)

    if status in ["Approved", "Rejected"]:
        leave.status = status
        leave.approved_by = request.user
        leave.save()

    return redirect("manage_leaves")


@login_required
def cancel_leave(request, leave_id):
    """Allow a user to cancel their own pending leave request."""
    leave = get_object_or_404(Leave, id=leave_id, user=request.user)
    if leave.status == "Pending":
        leave.delete()
        messages.success(request, "Your leave request has been cancelled.")
    else:
        messages.error(request, "Only pending leave requests may be cancelled.")
    return redirect("request_leave")




def logout_view(request):
    logout(request)
    return redirect('login')


# ==================== FACIAL RECOGNITION VIEWS ====================

@login_required
def register_face(request):
    """Register or update facial data for the current user"""
    from .models import FaceData
    
    try:
        face_data = FaceData.objects.get(user=request.user)
    except FaceData.DoesNotExist:
        face_data = FaceData.objects.create(user=request.user)

    if request.method == "POST":
        return render(request, 'attendance/register_face.html', {
            'face_registered': face_data.face_registered
        })

    return render(request, 'attendance/register_face.html', {
        'face_registered': face_data.face_registered
    })


@csrf_exempt
@login_required
def capture_face_for_registration(request):
    """API endpoint to capture and store facial encoding during registration"""
    from django.http import JsonResponse
    from .models import FaceData
    from .facial_recognition import FacialRecognitionEngine
    import json
    
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            base64_image = data.get('image')

            if not base64_image:
                return JsonResponse({
                    'success': False,
                    'message': 'No image provided'
                })

            # Convert base64 to image
            image = FacialRecognitionEngine.base64_to_image(base64_image)
            if image is None:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid image format'
                })

            # Extract facial encodings
            encodings = FacialRecognitionEngine.get_face_encodings_from_image(image)

            if not encodings:
                return JsonResponse({
                    'success': False,
                    'message': 'No face detected. Please ensure your face is clearly visible.'
                })

            if len(encodings) > 1:
                return JsonResponse({
                    'success': False,
                    'message': 'Multiple faces detected. Ensure only your face is in the frame.'
                })

            # Store the encoding
            face_data, created = FaceData.objects.get_or_create(user=request.user)
            face_data.set_encodings([encodings[0].tolist()])
            face_data.face_registered = True
            face_data.save()

            return JsonResponse({
                'success': True,
                'message': 'Face registered successfully!'
            })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })

    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@csrf_exempt
@login_required
def facial_recognition_clock_in_out(request):
    """
    Handle facial recognition for clock in/out.
    This view captures facial data and verifies it against stored facial data.
    """
   
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            action = data.get('action')  # 'clock_in' or 'clock_out'
            base64_image = data.get('image')

            if action not in ['clock_in', 'clock_out']:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid action'
                })

            if not base64_image:
                return JsonResponse({
                    'success': False,
                    'message': 'No image provided'
                })

            # Convert base64 to image
            image = FacialRecognitionEngine.base64_to_image(base64_image)
            if image is None:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid image format'
                })

            # Get facial encodings from the captured image
            captured_encodings = FacialRecognitionEngine.get_face_encodings_from_image(image)

            if not captured_encodings:
                return JsonResponse({
                    'success': False,
                    'message': 'No face detected in the image'
                })

            if len(captured_encodings) > 1:
                return JsonResponse({
                    'success': False,
                    'message': 'Multiple faces detected'
                })

            # Get stored facial data for the user
            try:
                face_data = request.user.face_data
            except FaceData.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'Facial data not registered. Please register your face first.'
                })

            # Get stored encodings
            stored_encodings = face_data.get_encodings()
            if not stored_encodings:
                return JsonResponse({
                    'success': False,
                    'message': 'No facial data found for this user'
                })

            # Convert stored encodings back to numpy arrays
            known_encodings = [np.array(enc) for enc in stored_encodings]

            # Verify the captured face
            is_match, distance = FacialRecognitionEngine.verify_face(
                known_encodings,
                captured_encodings[0]
            )

            if not is_match:
                return JsonResponse({
                    'success': False,
                    'message': f'Facial recognition failed. Not recognized. (Distance: {distance:.2f})',
                    'distance': float(distance)
                })

            # Update attendance with facial recognition
            today = timezone.now().date()
            attendance, created = Attendance.objects.get_or_create(
                user=request.user,
                date=today
            )

            if action == 'clock_in':
                attendance.clock_in = localtime(timezone.now()).time()
                attendance.clock_in_method = 'facial'
                attendance.save()

                return JsonResponse({
                    'success': True,
                    'message': f'Clocked in successfully at {attendance.clock_in}',
                    'distance': float(distance)
                })

            elif action == 'clock_out':
                if not attendance.clock_in:
                    return JsonResponse({
                        'success': False,
                        'message': 'Please clock in first'
                    })

                attendance.clock_out = localtime(timezone.now()).time()
                attendance.clock_out_method = 'facial'
                attendance.save()

                return JsonResponse({
                    'success': True,
                    'message': f'Clocked out successfully at {attendance.clock_out}',
                    'distance': float(distance)
                })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })

    return JsonResponse({'success': False, 'message': 'Invalid request method'})


@csrf_exempt
def facial_login(request):
    """Alternative login method using facial recognition"""
    
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            base64_image = data.get('image')
            username = data.get('username')

            if not base64_image or not username:
                return JsonResponse({
                    'success': False,
                    'message': 'Image and username required'
                })

            # Get the user
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'User not found'
                })

            # Convert base64 to image
            image = FacialRecognitionEngine.base64_to_image(base64_image)
            if image is None:
                return JsonResponse({
                    'success': False,
                    'message': 'Invalid image format'
                })

            # Get facial encodings from captured image
            captured_encodings = FacialRecognitionEngine.get_face_encodings_from_image(image)

            if not captured_encodings:
                return JsonResponse({
                    'success': False,
                    'message': 'No face detected'
                })

            # Get stored facial data
            try:
                face_data = user.face_data
            except FaceData.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'message': 'User has not registered facial data'
                })

            stored_encodings = face_data.get_encodings()
            if not stored_encodings:
                return JsonResponse({
                    'success': False,
                    'message': 'No facial data found'
                })

            # Convert to numpy arrays
            known_encodings = [np.array(enc) for enc in stored_encodings]

            # Verify
            is_match, distance = FacialRecognitionEngine.verify_face(
                known_encodings,
                captured_encodings[0]
            )

            if is_match:
                login(request, user)
                return JsonResponse({
                    'success': True,
                    'message': 'Login successful',
                    'redirect': '/dashboard/'
                })
            else:
                return JsonResponse({
                    'success': False,
                    'message': f'Face not recognized'
                })

        except Exception as e:
            return JsonResponse({
                'success': False,
                'message': f'Error: {str(e)}'
            })

    return JsonResponse({'success': False, 'message': 'Invalid request method'})




# ==================== END OF FACIAL RECOGNITION VIEWS ====================

# ==================== MONTHLY SUMMARY VIEWS ====================

@login_required
@user_passes_test(is_admin)
def attendance_summary(request):
    today = now().date()
    # Total staff (exclude superusers)
    staff_users = User.objects.filter(is_superuser=False, is_active=True)
    total_staff = staff_users.count()

    # Present / absent counts for today (based on clock_in) - only count non-superusers
    total_present = Attendance.objects.filter(date=today, clock_in__isnull=False, user__is_superuser=False).count()
    total_clocked_out = Attendance.objects.filter(date=today, clock_out__isnull=False, user__is_superuser=False).count()
    total_absent = max(0, total_staff - total_present)

    # Personal summary for each staff (today)
    staff_summaries = []
    for u in staff_users:
        rec = Attendance.objects.filter(user=u, date=today).first()
        if rec and rec.clock_in:
            status = 'Present'
        else:
            status = 'Absent'

        # Determine late clock-in and early clock-out based on default work times
        # Default shift: 09:00 start, 17:00 end
        late = False
        early = False
        if rec and rec.clock_in:
            try:
                if rec.clock_in > dt_time(9, 0):
                    late = True
            except Exception:
                late = False

        if rec and rec.clock_out:
            try:
                if rec.clock_out < dt_time(17, 0):
                    early = True
            except Exception:
                early = False

        staff_summaries.append({
            'employee_id': u.id,
            'username': u.username,
            'full_name': f"{u.first_name} {u.last_name}".strip(),
            'status': status,
            'clock_in': getattr(rec, 'clock_in', None) if rec else None,
            'clock_out': getattr(rec, 'clock_out', None) if rec else None,
            'late': late,
            'early': early,
        })

    context = {
        'total_staff': total_staff,
        'total_staff_clocked_in': total_present,
        'total_staff_absent': total_absent,
        'total_staff_clocked_out': total_clocked_out,
        'staff_summaries': staff_summaries,
    }

    return render(request, 'attendance/attendance_summary.html', context)




@login_required
@user_passes_test(is_admin)
def export_attendance_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="attendance.csv"'

    writer = csv.writer(response)
    writer.writerow(['User', 'Date', 'Clock In', 'Clock Out', 'Clock In Method', 'Clock Out Method'])

    records = Attendance.objects.all()
    for record in records:
        writer.writerow([
            record.user.username, 
            record.date,
            record.clock_in or '',
            record.clock_out or '',
            record.clock_in_method,
            record.clock_out_method or ''
        ])

    return response      



@login_required
@user_passes_test(is_admin)
def export_attendance_excel(request):
    wb = Workbook()
    ws = wb.active
    ws.title = "Attendance"

    ws.append(["User", "Date", "Clock In", "Clock Out", "Clock In Method", "Clock Out Method"])
    for record in Attendance.objects.all():
        ws.append([
            record.user.username,
            str(record.date),
            str(record.clock_in) if record.clock_in else '',
            str(record.clock_out) if record.clock_out else '',
            record.clock_in_method,
            record.clock_out_method or ''
        ])
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    response["Content-Disposition"] = "attachment; filename=attendance.xlsx"
    
    wb.save(response)
    return response
    
