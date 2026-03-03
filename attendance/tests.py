from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Leave
from datetime import date, timedelta


class LeaveViewsTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='alice', password='password')
        self.client.login(username='alice', password='password')

    def test_request_leave_page_contains_leaves(self):
        # create a pending and an approved leave
        Leave.objects.create(
            user=self.user,
            start_date=date.today(),
            end_date=date.today() + timedelta(days=2),
            reason='Test',
            status='Pending'
        )
        Leave.objects.create(
            user=self.user,
            start_date=date.today() - timedelta(days=5),
            end_date=date.today() - timedelta(days=3),
            reason='Another',
            status='Approved'
        )
        response = self.client.get(reverse('request_leave'))
        self.assertEqual(response.status_code, 200)
        # page should include both statuses
        self.assertContains(response, 'Pending')
        self.assertContains(response, 'Approved')

    def test_cancel_pending_leave(self):
        leave = Leave.objects.create(
            user=self.user,
            start_date=date.today(),
            end_date=date.today(),
            reason='Cancel me',
            status='Pending'
        )
        url = reverse('cancel_leave', args=[leave.id])
        response = self.client.get(url)
        # should redirect back
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Leave.objects.filter(id=leave.id).exists())

    def test_cannot_cancel_non_pending(self):
        leave = Leave.objects.create(
            user=self.user,
            start_date=date.today(),
            end_date=date.today(),
            reason='Do not cancel',
            status='Approved'
        )
        url = reverse('cancel_leave', args=[leave.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Leave.objects.filter(id=leave.id).exists())
