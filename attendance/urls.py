from django import views
from django.urls import path
from .views import login_view, dashboard, logout_view
from . import views

urlpatterns = [
    path('', login_view, name='login'),
    path('dashboard/', dashboard, name='dashboard'),
    path('logout/', logout_view, name='logout'),
]

