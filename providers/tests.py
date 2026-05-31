from django.test import TestCase, Client
from django.urls import reverse
from users.models import UserProfile
from providers.models import ServiceProvider
from services.models import Service
from bookings.models import Booking
from payments.models import Payment
import datetime


class ServiceProviderModelTest(TestCase):
    def setUp(self):
        self.provider_user = UserProfile.objects.create_user(
            username='provmodel', password='pass1234', role='provider',
            first_name='Raju', last_name='Kumar'
        )
        self.provider = ServiceProvider.objects.create(
            user=self.provider_user,
            skill='Plumbing',
            location='Ranchi',
            availability_status=True,
            is_verified=False,
            bio='Expert plumber'
        )

    def test_provider_str_with_full_name(self):
        result = str(self.provider)
        self.assertIn('Raju Kumar', result)
        self.assertIn('Plumbing', result)

    def test_provider_str_no_skill(self):
        self.provider.skill = None
        self.provider.save()
        self.assertIn('No Skill Set', str(self.provider))

    def test_provider_default_availability(self):
        p = ServiceProvider.objects.create(
            user=UserProfile.objects.create_user(username='p2', password='p'),
        )
        self.assertTrue(p.availability_status)

    def test_provider_not_verified_by_default_on_new(self):
        u = UserProfile.objects.create_user(username='unverif', password='p', role='provider')
        p = ServiceProvider.objects.create(user=u)
        self.assertFalse(p.is_verified)

    def test_provider_one_to_one_with_user(self):
        self.assertEqual(self.provider_user.provider_profile, self.provider)


class ProviderViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.provider_user = UserProfile.objects.create_user(
            username='prov_view', password='pass1234', role='provider'
        )
        self.provider = ServiceProvider.objects.create(
            user=self.provider_user, skill='Cleaning', location='Patna',
            availability_status=True, is_verified=True
        )
        self.customer = UserProfile.objects.create_user(
            username='cust_prov', password='pass1234', role='customer'
        )
        self.service = Service.objects.create(
            provider=self.provider, service_name='Deep Clean',
            description='Full house clean', price=1500.00, category='cleaning'
        )
        self.booking = Booking.objects.create(
            user=self.customer, service=self.service,
            provider=self.provider,
            booking_date=datetime.date.today(), time_slot='10_11', status='pending'
        )

    def test_provider_dashboard_requires_login(self):
        response = self.client.get(reverse('provider_dashboard'))
        self.assertNotEqual(response.status_code, 200)

    def test_provider_dashboard_accessible(self):
        self.client.login(username='prov_view', password='pass1234')
        response = self.client.get(reverse('provider_dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'providers/dashboard.html')

    def test_customer_cannot_access_provider_dashboard(self):
        self.client.login(username='cust_prov', password='pass1234')
        response = self.client.get(reverse('provider_dashboard'))
        self.assertEqual(response.status_code, 302)

    def test_my_services_view(self):
        self.client.login(username='prov_view', password='pass1234')
        response = self.client.get(reverse('my_services'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Deep Clean')

    def test_add_service_get(self):
        self.client.login(username='prov_view', password='pass1234')
        response = self.client.get(reverse('add_service'))
        self.assertEqual(response.status_code, 200)

    def test_manage_requests_view(self):
        self.client.login(username='prov_view', password='pass1234')
        response = self.client.get(reverse('manage_requests'))
        self.assertEqual(response.status_code, 200)

    def test_manage_requests_confirm_booking(self):
        self.client.login(username='prov_view', password='pass1234')
        self.client.post(reverse('manage_requests'), {
            'booking_id': self.booking.id,
            'action': 'accept'
        })
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'confirmed')

    def test_manage_requests_cancel_booking(self):
        self.client.login(username='prov_view', password='pass1234')
        self.client.post(reverse('manage_requests'), {
            'booking_id': self.booking.id,
            'action': 'reject'
        })
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'cancelled')

    def test_manage_requests_complete_booking(self):
        self.booking.status = 'confirmed'
        self.booking.save()
        self.client.login(username='prov_view', password='pass1234')
        response = self.client.post(reverse('manage_requests'), {
            'booking_id': self.booking.id,
            'action': 'complete'
        })
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'completed')

    def test_update_profile_get(self):
        self.client.login(username='prov_view', password='pass1234')
        response = self.client.get(reverse('provider_update_profile'))
        self.assertEqual(response.status_code, 200)

    def test_delete_service(self):
        self.client.login(username='prov_view', password='pass1234')
        response = self.client.post(reverse('delete_service', args=[self.service.id]))
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Service.objects.filter(id=self.service.id).exists())