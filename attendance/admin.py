from django.contrib import admin
from .models import Attendance, Leave, FaceData


class FaceDataAdmin(admin.ModelAdmin):
    readonly_fields = ('registered_at', 'updated_at')
    list_display = ('user', 'face_registered', 'registered_at')
    list_filter = ('face_registered', 'registered_at')
    
    search_fields = ('user__username', 'user__email')


class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'clock_in', 'clock_out', 'clock_in_method')
    list_filter = ('date', 'clock_in_method')
    search_fields = ('user__username',)


admin.site.register(FaceData, FaceDataAdmin)
admin.site.register(Attendance, AttendanceAdmin)
admin.site.register(Leave)
 