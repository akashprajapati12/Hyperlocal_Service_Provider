from django.test import TestCase, Client
from django.urls import reverse
from users.models import UserProfile
from providers.models import ServiceProvider
from services.models import Service
from bookings.models import Booking
from reviews.models import Review
import datetime


class ReviewModelTest(TestCase):
    def setUp(self):
        self.customer = UserProfile.objects.create_user(
            username='rev_cust', password='pass1234', role='customer'
        )
        self.provider_user = UserProfile.objects.create_user(
            username='rev_prov', password='pass1234', role='provider'
        )
        self.provider = ServiceProvider.objects.create(
            user=self.provider_user, skill='Cleaning', location='City',
            availability_status=True, is_verified=True
        )
        self.service = Service.objects.create(
            provider=self.provider, service_name='Office Clean',
            description='Office cleaning', price=1200.00, category='cleaning'
        )
        self.booking = Booking.objects.create(
            user=self.customer, service=self.service,
            provider=self.provider,
            booking_date=datetime.date.today(), time_slot='09_10',
            status='completed'
        )
        self.review = Review.objects.create(
            user=self.customer, service=self.service,
            booking=self.booking, rating=4, comment='Good service'
        )

    def test_review_str(self):
        self.assertIn('rev_cust', str(self.review))
        self.assertIn('4', str(self.review))

    def test_review_rating_stored(self):
        self.assertEqual(self.review.rating, 4)

    def test_review_comment_stored(self):
        self.assertEqual(self.review.comment, 'Good service')

    def test_review_unique_per_booking(self):
        from django.db import IntegrityError
        with self.assertRaises(Exception):
            Review.objects.create(
                user=self.customer, service=self.service,
                booking=self.booking, rating=5
            )

    def test_review_ordering_newest_first(self):
        booking2 = Booking.objects.create(
            user=self.customer, service=self.service,
            provider=self.provider,
            booking_date=datetime.date.today(), time_slot='10_11',
            status='completed'
        )
        r2 = Review.objects.create(
            user=self.customer, service=self.service,
            booking=booking2, rating=3
        )
        reviews = list(Review.objects.all())
        self.assertEqual(reviews[0].id, r2.id)

    def test_review_rating_range(self):
        from django.core.exceptions import ValidationError
        r = Review(
            user=self.customer, service=self.service,
            booking=self.booking, rating=6
        )
        with self.assertRaises(ValidationError):
            r.full_clean()


class ReviewViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.customer = UserProfile.objects.create_user(
            username='rv_viewcust', password='pass1234', role='customer'
        )
        self.provider_user = UserProfile.objects.create_user(
            username='rv_viewprov', password='pass1234', role='provider'
        )
        self.provider = ServiceProvider.objects.create(
            user=self.provider_user, skill='Plumbing', location='Pune',
            availability_status=True, is_verified=True
        )
        self.service = Service.objects.create(
            provider=self.provider, service_name='Tank Fix',
            description='Fix water tank', price=900.00, category='plumbing'
        )
        self.completed_booking = Booking.objects.create(
            user=self.customer, service=self.service,
            provider=self.provider,
            booking_date=datetime.date.today(), time_slot='13_14',
            status='completed'
        )
        self.pending_booking = Booking.objects.create(
            user=self.customer, service=self.service,
            provider=self.provider,
            booking_date=datetime.date.today(), time_slot='15_16',
            status='pending'
        )

    def test_add_review_requires_login(self):
        response = self.client.get(reverse('add_review', args=[self.completed_booking.id]))
        self.assertNotEqual(response.status_code, 200)

    def test_add_review_get_for_completed_booking(self):
        self.client.login(username='rv_viewcust', password='pass1234')
        response = self.client.get(reverse('add_review', args=[self.completed_booking.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'reviews/add_review.html')

    def test_add_review_redirects_for_pending_booking(self):
        self.client.login(username='rv_viewcust', password='pass1234')
        response = self.client.get(reverse('add_review', args=[self.pending_booking.id]))
        self.assertEqual(response.status_code, 302)

    def test_add_review_post_creates_review(self):
        self.client.login(username='rv_viewcust', password='pass1234')
        response = self.client.post(reverse('add_review', args=[self.completed_booking.id]), {
            'rating': 5,
            'comment': 'Excellent work!'
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Review.objects.filter(
            user=self.customer, booking=self.completed_booking
        ).exists())

    def test_add_review_duplicate_redirects(self):
        Review.objects.create(
            user=self.customer, service=self.service,
            booking=self.completed_booking, rating=3
        )
        self.client.login(username='rv_viewcust', password='pass1234')
        response = self.client.get(reverse('add_review', args=[self.completed_booking.id]))
        self.assertEqual(response.status_code, 302)