from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from users.models import UserProfile, Notification
from providers.models import ServiceProvider
from services.models import Service
from bookings.models import Booking, ChatMessage
import datetime


class BookingModelTest(TestCase):
    def setUp(self):
        self.customer = UserProfile.objects.create_user(
            username='bk_customer', password='pass1234', role='customer'
        )
        self.provider_user = UserProfile.objects.create_user(
            username='bk_provider', password='pass1234', role='provider'
        )
        self.provider = ServiceProvider.objects.create(
            user=self.provider_user, skill='Tutoring', location='Jaipur',
            availability_status=True, is_verified=True
        )
        self.service = Service.objects.create(
            provider=self.provider, service_name='Math Tutor',
            description='1:1 math tuition', price=600.00, category='tutoring'
        )
        self.booking = Booking.objects.create(
            user=self.customer, service=self.service,
            provider=self.provider,
            booking_date=datetime.date.today(),
            time_slot='11_12', status='pending'
        )

    def test_booking_str(self):
        self.assertIn('Math Tutor', str(self.booking))
        self.assertIn('pending', str(self.booking))

    def test_booking_default_status(self):
        b = Booking.objects.create(
            user=self.customer, service=self.service,
            provider=self.provider,
            booking_date=datetime.date.today(), time_slot='09_10'
        )
        self.assertEqual(b.status, 'pending')

    def test_total_price_no_extra(self):
        self.assertEqual(float(self.booking.total_price), 600.00)

    def test_total_price_with_extra_charges(self):
        self.booking.extra_charges = 100.00
        self.booking.save()
        self.assertEqual(float(self.booking.total_price), 700.00)

    def test_extra_hours_part(self):
        self.booking.extra_hours = 1.5
        self.assertEqual(self.booking.extra_hours_part, 1)

    def test_extra_minutes_part(self):
        self.booking.extra_hours = 1.5
        self.assertEqual(self.booking.extra_minutes_part, 30)

    def test_booking_ordering_newest_first(self):
        b2 = Booking.objects.create(
            user=self.customer, service=self.service,
            provider=self.provider,
            booking_date=datetime.date.today(), time_slot='12_13'
        )
        bookings = list(Booking.objects.all())
        self.assertEqual(bookings[0].id, b2.id)

    def test_is_disputed_default_false(self):
        self.assertFalse(self.booking.is_disputed)

    def test_chat_deleted_default_false(self):
        self.assertFalse(self.booking.chat_deleted)

    def test_status_choices(self):
        statuses = [s[0] for s in Booking.STATUS_CHOICES]
        self.assertIn('pending', statuses)
        self.assertIn('confirmed', statuses)
        self.assertIn('completed', statuses)
        self.assertIn('cancelled', statuses)


class ChatMessageModelTest(TestCase):
    def setUp(self):
        self.customer = UserProfile.objects.create_user(
            username='chat_cust', password='pass1234', role='customer'
        )
        self.provider_user = UserProfile.objects.create_user(
            username='chat_prov', password='pass1234', role='provider'
        )
        self.provider = ServiceProvider.objects.create(
            user=self.provider_user, skill='Beauty', location='City',
            availability_status=True, is_verified=True
        )
        self.service = Service.objects.create(
            provider=self.provider, service_name='Haircut',
            description='Salon at home', price=250.00, category='beauty'
        )
        self.booking = Booking.objects.create(
            user=self.customer, service=self.service,
            provider=self.provider,
            booking_date=datetime.date.today(), time_slot='09_10', status='confirmed'
        )
        self.msg = ChatMessage.objects.create(
            booking=self.booking, sender=self.customer,
            message='Hello, please be on time'
        )

    def test_chatmessage_str(self):
        self.assertIn('chat_cust', str(self.msg))

    def test_chatmessage_ordering(self):
        msg2 = ChatMessage.objects.create(
            booking=self.booking, sender=self.provider_user, message='Sure!'
        )
        msgs = list(ChatMessage.objects.filter(booking=self.booking))
        self.assertEqual(msgs[0].id, self.msg.id)


class BookingViewsTest(TestCase):
    def setUp(self):
        self.client = Client()
        self.customer = UserProfile.objects.create_user(
            username='bkview_cust', password='pass1234', role='customer'
        )
        self.provider_user = UserProfile.objects.create_user(
            username='bkview_prov', password='pass1234', role='provider'
        )
        self.provider = ServiceProvider.objects.create(
            user=self.provider_user, skill='Electrical', location='City',
            availability_status=True, is_verified=True
        )
        self.service = Service.objects.create(
            provider=self.provider, service_name='Wiring Fix',
            description='Fix wiring', price=700.00, category='electrical'
        )
        self.booking = Booking.objects.create(
            user=self.customer, service=self.service,
            provider=self.provider,
            booking_date=datetime.date.today(), time_slot='14_15', status='pending'
        )

    def test_create_booking_requires_login(self):
        response = self.client.get(reverse('create_booking', args=[self.service.id]))
        self.assertNotEqual(response.status_code, 200)

    def test_create_booking_get(self):
        self.client.login(username='bkview_cust', password='pass1234')
        response = self.client.get(reverse('create_booking', args=[self.service.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'bookings/create_booking.html')

    def test_provider_cannot_create_booking(self):
        self.client.login(username='bkview_prov', password='pass1234')
        response = self.client.get(reverse('create_booking', args=[self.service.id]))
        self.assertEqual(response.status_code, 302)

    def test_booking_detail_view(self):
        self.client.login(username='bkview_cust', password='pass1234')
        response = self.client.get(reverse('booking_detail', args=[self.booking.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'bookings/booking_detail.html')

    def test_booking_detail_shows_service_name(self):
        self.client.login(username='bkview_cust', password='pass1234')
        response = self.client.get(reverse('booking_detail', args=[self.booking.id]))
        self.assertContains(response, 'Wiring Fix')

    def test_booking_detail_access_denied_for_other_user(self):
        other = UserProfile.objects.create_user(
            username='other_user', password='pass1234', role='customer'
        )
        self.client.login(username='other_user', password='pass1234')
        response = self.client.get(reverse('booking_detail', args=[self.booking.id]))
        self.assertEqual(response.status_code, 302)

    def test_cancel_booking(self):
        self.client.login(username='bkview_cust', password='pass1234')
        response = self.client.post(reverse('cancel_booking', args=[self.booking.id]))
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'cancelled')

    def test_booking_history_view(self):
        self.client.login(username='bkview_cust', password='pass1234')
        response = self.client.get(reverse('booking_history'))
        self.assertEqual(response.status_code, 200)

    def test_create_booking_post_creates_booking(self):
        self.client.login(username='bkview_cust', password='pass1234')
        count_before = Booking.objects.count()
        response = self.client.post(reverse('create_booking', args=[self.service.id]), {
            'booking_date': (datetime.date.today() + datetime.timedelta(days=1)).strftime('%Y-%m-%d'),
            'time_slot': '09_10',
            'additional_info': 'Please bring tools'
        })
        self.assertGreater(Booking.objects.count(), count_before)

    def test_create_booking_creates_notification(self):
        self.client.login(username='bkview_cust', password='pass1234')
        response = self.client.post(reverse('create_booking', args=[self.service.id]), {
            'booking_date': (datetime.date.today() + datetime.timedelta(days=2)).strftime('%Y-%m-%d'),
            'time_slot': '10_11',
        })
        self.assertTrue(Notification.objects.filter(user=self.provider_user).exists())