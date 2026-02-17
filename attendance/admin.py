from django.contrib import admin
from .models import Attendance
from .models import Leave

admin.site.register(Attendance)
admin.site.register(Leave)
