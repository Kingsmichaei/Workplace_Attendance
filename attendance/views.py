from django.contrib.auth.models import User
from urllib import request
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
from datetime import date
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import login



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
    from django.http import JsonResponse
    from .models import FaceData
    from .facial_recognition import FacialRecognitionEngine
    import json
    import numpy as np      
    
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
    from django.http import JsonResponse
    from .models import FaceData
    from .facial_recognition import FacialRecognitionEngine
    import json
    import numpy as np
    
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




