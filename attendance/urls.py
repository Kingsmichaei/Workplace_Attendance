from django.urls import path
from . views import (
    activate_user, deactivate_user, delete_user, login_view, dashboard, 
    logout_view, add_user, manage_leaves, request_leave, staff_attendance, 
    update_leave_status, register_face, capture_face_for_registration,
    facial_recognition_clock_in_out, facial_login
)
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', login_view, name='login'),
    path('dashboard/', dashboard, name='dashboard'),
    path('logout/', logout_view, name='logout'),
    path('add_user/', add_user, name='add_user'),
    path('deactivate-user/<int:user_id>/', deactivate_user, name='deactivate_user'),
    path('activate-user/<int:user_id>/', activate_user, name='activate_user'),
    path('delete-user/<int:user_id>/', delete_user, name='delete_user'),
    path('staff-attendance/<int:user_id>/', staff_attendance, name='staff_attendance'),
    path('request-leave/', request_leave, name='request_leave'),
    path('manage-leaves/',manage_leaves, name='manage_leaves'),
    path('update-leave-status/<int:leave_id>/<str:status>/',update_leave_status, name='update_leave_status'),
    
    # Facial Recognition URLs
    path('register-face/', register_face, name='register_face'),
    path('api/capture-face-registration/', capture_face_for_registration, name='capture_face_registration'),
    path('api/facial-clock/', facial_recognition_clock_in_out, name='facial_clock'),
    path('api/facial-login/', facial_login, name='facial_login'),
    
    # Password Reset URLs
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='attendance/password_reset.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='attendance/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='attendance/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='attendance/password_reset_complete.html'), name='password_reset_complete'),
]





