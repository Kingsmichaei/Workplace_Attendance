from django.db import models
from django.contrib.auth.models import User
import json


class FaceData(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='face_data')
    facial_encodings = models.TextField()  # Store as JSON array
    face_registered = models.BooleanField(default=False)
    registered_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def set_encodings(self, encodings):
        """Store facial encodings as JSON"""
        self.facial_encodings = json.dumps(encodings)
    
    def get_encodings(self):
        """Retrieve facial encodings from JSON"""
        if self.facial_encodings:
            return json.loads(self.facial_encodings)
        return None

    def __str__(self):
        return f"Face Data - {self.user.username}"


class Attendance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField(auto_now_add=True)
    clock_in = models.TimeField(null=True, blank=True)
    clock_out = models.TimeField(null=True, blank=True)
    clock_in_method = models.CharField(
        max_length=20,
        choices=[('manual', 'Manual'), ('facial', 'Facial Recognition')],
        default='manual'
    )
    clock_out_method = models.CharField(
        max_length=20,
        choices=[('manual', 'Manual'), ('facial', 'Facial Recognition')],
        default='manual',
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.user.username} - {self.date}"


class Leave(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()

    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='Pending'
    )

    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_leaves'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.status}"
