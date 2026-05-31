from django.test import TestCase, Client
from django.urls import reverse
from users.models import UserProfile, Notification
from providers.models import ServiceProvider
from services.models import Service
from bookings.models import Booking
from payments.models import Payment
import datetime


class AdminPanelViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.admin_user = UserProfile.objects.create_user(
            username='admin_test', password='pass1234', role='admin'
        )
        self.customer = UserProfile.objects.create_user(
            username='adm_cust', password='pass1234', role='customer'
        )
        self.provider_user = UserProfile.objects.create_user(
            username='adm_prov', password='pass1234', role='provider'
        )
        self.provider = ServiceProvider.objects.create(
            user=self.provider_user, skill='Plumbing', location='Ranchi',
            availability_status=True, is_verified=True
        )
        self.service = Service.objects.create(
            provider=self.provider, service_name='Admin Test Service',
            description='Test', price=500.00, category='plumbing'
        )
        self.booking = Booking.objects.create(
            user=self.customer, service=self.service,
            provider=self.provider,
            booking_date=datetime.date.today(), time_slot='09_10', status='pending'
        )
        self.payment = Payment.objects.create(
            booking=self.booking, amount=500.00,
            payment_method='cash', payment_status='paid'
        )

    def test_admin_dashboard_requires_login(self):
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_customer_cannot_access_admin_dashboard(self):
        self.client.login(username='adm_cust', password='pass1234')
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_admin_dashboard_accessible_by_admin(self):
        self.client.login(username='admin_test', password='pass1234')
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'admin_panel/dashboard.html')

    def test_manage_users_view(self):
        self.client.login(username='admin_test', password='pass1234')
        response = self.client.get(reverse('manage_users'))
        self.assertEqual(response.status_code, 200)

    def test_manage_providers_view(self):
        self.client.login(username='admin_test', password='pass1234')
        response = self.client.get(reverse('manage_providers'))
        self.assertEqual(response.status_code, 200)

    def test_manage_bookings_view(self):
        self.client.login(username='admin_test', password='pass1234')
        response = self.client.get(reverse('manage_bookings'))
        self.assertEqual(response.status_code, 200)

    def test_admin_booking_detail_view(self):
        self.client.login(username='admin_test', password='pass1234')
        response = self.client.get(reverse('admin_booking_detail', args=[self.booking.id]))
        self.assertEqual(response.status_code, 200)

    def test_admin_user_detail_view(self):
        self.client.login(username='admin_test', password='pass1234')
        response = self.client.get(reverse('admin_user_detail', args=[self.customer.id]))
        self.assertEqual(response.status_code, 200)

    def test_reports_dashboard_view(self):
        self.client.login(username='admin_test', password='pass1234')
        response = self.client.get(reverse('reports_dashboard'))
        self.assertEqual(response.status_code, 200)

    def test_customer_service_report_view(self):
        self.client.login(username='admin_test', password='pass1234')
        response = self.client.get(reverse('customer_service_report'))
        self.assertEqual(response.status_code, 200)

    def test_provider_service_report_view(self):
        self.client.login(username='admin_test', password='pass1234')
        response = self.client.get(reverse('provider_service_report'))
        self.assertEqual(response.status_code, 200)

    def test_provider_cannot_access_admin_dashboard(self):
        self.client.login(username='adm_prov', password='pass1234')
        response = self.client.get(reverse('admin_dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_admin_dashboard_shows_stats(self):
        self.client.login(username='admin_test', password='pass1234')
        response = self.client.get(reverse('admin_dashboard'))
        self.assertIn('total_users', response.context)
        self.assertIn('total_providers', response.context)
        self.assertIn('total_bookings', response.context)
        self.assertIn('total_revenue', response.context)

    def test_admin_dashboard_revenue_includes_paid_payments(self):
        self.client.login(username='admin_test', password='pass1234')
        response = self.client.get(reverse('admin_dashboard'))
        self.assertGreater(float(response.context['total_revenue']), 0)