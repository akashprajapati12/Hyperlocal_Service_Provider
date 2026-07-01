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
            city='Mumbai', pincode='400001',
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

    def test_service_list_location_city_and_pincode(self):
        # Searching Mumbai 400001 should extract the pincode and find the service
        response = self.client.get(reverse('service_list'), {'q_loc': 'Mumbai 400001'})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'AC Repair')

    def test_service_list_location_city_and_wrong_pincode(self):
        # Searching Mumbai 999999 (wrong pincode) should search only by pincode and return no results
        response = self.client.get(reverse('service_list'), {'q_loc': 'Mumbai 999999'})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'AC Repair')