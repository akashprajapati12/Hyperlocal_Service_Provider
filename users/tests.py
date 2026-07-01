from django.test import TestCase, Client
from django.urls import reverse
from users.models import UserProfile
from providers.models import ServiceProvider
from services.models import Service
from reviews.models import Review
from bookings.models import Booking
import datetime


class ServiceModelTest(TestCase):
    def setUp(self):
        self.provider_user = UserProfile.objects.create_user(
            username='svc_provider', password='pass1234', role='provider'
        )
        self.provider = ServiceProvider.objects.create(
            user=self.provider_user, skill='Plumbing', location='Delhi',
            availability_status=True, is_verified=True
        )
        self.service = Service.objects.create(
            provider=self.provider,
            service_name='Pipe Fix',
            description='Fix leaking pipes',
            price=400.00,
            category='plumbing'
        )

    def test_service_str(self):
        self.assertIn('Pipe Fix', str(self.service))
        self.assertIn('400', str(self.service))

    def test_service_default_category(self):
        s = Service.objects.create(
            provider=self.provider,
            service_name='Misc Work',
            description='desc',
            price=100.00
        )
        self.assertEqual(s.category, 'other')

    def test_service_category_choices(self):
        categories = [c[0] for c in Service.CATEGORY_CHOICES]
        self.assertIn('plumbing', categories)
        self.assertIn('electrical', categories)
        self.assertIn('cleaning', categories)

    def test_service_ordering_newest_first(self):
        s2 = Service.objects.create(
            provider=self.provider, service_name='New Service',
            description='new', price=200.00, category='electrical'
        )
        services = list(Service.objects.all())
        self.assertEqual(services[0].id, s2.id)

    def test_service_price_stored_correctly(self):
        self.service.refresh_from_db()
        self.assertEqual(float(self.service.price), 400.00)


class ServiceViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.provider_user = UserProfile.objects.create_user(
            username='svc_prov2', password='pass1234', role='provider'
        )
        self.provider = ServiceProvider.objects.create(
            user=self.provider_user, skill='Electrical', location='Mumbai',
            availability_status=True, is_verified=True
        )
        self.service = Service.objects.create(
            provider=self.provider, service_name='AC Repair',
            description='Full AC service', price=800.00, category='electrical'
        )

    def test_service_list_view(self):
        response = self.client.get(reverse('service_list'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'services/service_list.html')

    def test_service_list_shows_services(self):
        response = self.client.get(reverse('service_list'))
        self.assertContains(response, 'AC Repair')

    def test_service_detail_view(self):
        response = self.client.get(reverse('service_detail', args=[self.service.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'services/service_detail.html')

    def test_service_detail_shows_price(self):
        response = self.client.get(reverse('service_detail', args=[self.service.id]))
        self.assertContains(response, '800')

    def test_service_list_category_filter(self):
        response = self.client.get(reverse('service_list'), {'category': 'electrical'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'AC Repair')

    def test_service_list_search(self):
        response = self.client.get(reverse('service_list'), {'search': 'AC'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'AC Repair')

    def test_service_list_search_no_results(self):
        response = self.client.get(reverse('service_list'), {'search': 'xyznonexistent'})
        self.assertEqual(response.status_code, 200)

    def test_service_detail_404_for_invalid_id(self):
        response = self.client.get(reverse('service_detail', args=[99999]))
        self.assertEqual(response.status_code, 404)

    def test_service_detail_context_has_reviews(self):
        response = self.client.get(reverse('service_detail', args=[self.service.id]))
        self.assertIn('reviews', response.context)

    def test_service_detail_context_has_avg_rating(self):
        response = self.client.get(reverse('service_detail', args=[self.service.id]))
        self.assertIn('avg_rating', response.context)
        self.assertEqual(response.context['avg_rating'], 0)

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

class PasswordValidationTest(TestCase):
    def test_short_password_rejected(self):
        # Password with less than 8 characters should be rejected
        with self.assertRaises(ValidationError):
            validate_password("1234567")

    def test_numeric_only_password_accepted_if_long_enough(self):
        # A purely numeric password of length 8 should be accepted (no NumericPasswordValidator)
        try:
            validate_password("12345678")
        except ValidationError:
            self.fail("validate_password raised ValidationError unexpectedly for numeric-only password")

    def test_common_password_accepted_if_long_enough(self):
        # A very common password like "password" of length 8 should be accepted (no CommonPasswordValidator)
        try:
            validate_password("password")
        except ValidationError:
            self.fail("validate_password raised ValidationError unexpectedly for common password")

    def test_matching_username_rejected(self):
        # A password too similar to user attributes should be rejected
        user = UserProfile(username="johndoe")
        with self.assertRaises(ValidationError):
            validate_password("johndoe123", user=user)

class UnifiedRegistrationTest(TestCase):
    def setUp(self):
        self.client = Client()

    def test_unified_register_customer_no_pincode_allowed(self):
        post_data = {
            'username': 'new_cust',
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'jane@example.com',
            'phone': '1234567890',
            'role': 'customer',
            'password1': 'pass12345',
            'password2': 'pass12345',
        }
        response = self.client.post(reverse('register'), post_data)
        self.assertEqual(response.status_code, 302)
        user = UserProfile.objects.get(username='new_cust')
        self.assertEqual(user.role, 'customer')
        self.assertFalse(hasattr(user, 'provider_profile'))

    def test_unified_register_provider_requires_pincode(self):
        post_data = {
            'username': 'new_prov_fail',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'phone': '1234567890',
            'role': 'provider',
            'password1': 'pass12345',
            'password2': 'pass12345',
        }
        response = self.client.post(reverse('register'), post_data)
        self.assertEqual(response.status_code, 200)
        self.assertFormError(response.context['form'], 'pincode', 'Pincode is required for providers.')

    def test_unified_register_provider_with_pincode_saves(self):
        post_data = {
            'username': 'new_prov_success',
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john2@example.com',
            'phone': '1234567890',
            'role': 'provider',
            'pincode': '700001',
            'password1': 'pass12345',
            'password2': 'pass12345',
        }
        response = self.client.post(reverse('register'), post_data)
        self.assertEqual(response.status_code, 302)
        user = UserProfile.objects.get(username='new_prov_success')
        self.assertEqual(user.role, 'provider')
        self.assertEqual(user.provider_profile.pincode, '700001')