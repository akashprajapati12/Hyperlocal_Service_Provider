from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from users.models import UserProfile, Notification
from providers.models import ServiceProvider
from services.models import Service
from bookings.models import Booking
from payments.models import Payment
from payments.forms import PaymentForm
import datetime


class PaymentsTestCase(TestCase):
    def setUp(self):
        # Create users
        self.customer = UserProfile.objects.create_user(
            username='customer_test',
            email='customer@test.com',
            password='password123',
            role='customer'
        )
        self.provider_user = UserProfile.objects.create_user(
            username='provider_test',
            email='provider@test.com',
            password='password123',
            role='provider'
        )
        
        # Create service provider
        self.provider = ServiceProvider.objects.create(
            user=self.provider_user,
            skill='Plumbing',
            location='TestCity',
            availability_status=True,
            is_verified=True
        )
        
        # Create service
        self.service = Service.objects.create(
            provider=self.provider,
            service_name='Test Pipe Repair',
            description='Test description',
            price=500.00,
            category='plumbing'
        )
        
        # Create booking
        self.booking = Booking.objects.create(
            user=self.customer,
            service=self.service,
            provider=self.provider,
            booking_date=timezone.now().date(),
            time_slot='09_10',
            status='pending'
        )
        
        # Initialize client
        self.client = Client()
        self.client.login(username='customer_test', password='password123')

    def test_checkout_view_get(self):
        response = self.client.get(reverse('checkout', args=[self.booking.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'payments/checkout.html')
        self.assertIsInstance(response.context['form'], PaymentForm)

    def test_checkout_view_post_cash(self):
        response = self.client.post(reverse('checkout', args=[self.booking.id]), {'payment_method': 'cash'})
        self.assertEqual(response.status_code, 302)
        payment = Payment.objects.get(booking=self.booking)
        self.assertEqual(payment.payment_method, 'cash')
        self.assertEqual(payment.payment_status, 'pending')
        self.assertRedirects(response, reverse('payment_confirmation', args=[self.booking.id]))

    def test_checkout_view_post_online(self):
        response = self.client.post(reverse('checkout', args=[self.booking.id]), {'payment_method': 'online'})
        self.assertEqual(response.status_code, 302)
        payment = Payment.objects.get(booking=self.booking)
        self.assertEqual(payment.payment_method, 'online')
        self.assertEqual(payment.payment_status, 'pending')
        self.assertRedirects(response, reverse('upi_payment', args=[self.booking.id]))

    def test_upi_payment_view(self):
        # Create online payment first
        payment = Payment.objects.create(
            booking=self.booking,
            amount=500.00,
            payment_method='online',
            payment_status='pending'
        )
        response = self.client.get(reverse('upi_payment', args=[self.booking.id]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'payments/upi_payment.html')
        self.assertIn('qr_data_url', response.context)

    def test_check_payment_status_view(self):
        # Create online payment first in pending state
        payment = Payment.objects.create(
            booking=self.booking,
            amount=500.00,
            payment_method='online',
            payment_status='pending'
        )
        # Poll status for pending payment
        response = self.client.get(reverse('check_payment_status', args=[self.booking.id]))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['success'])
        self.assertFalse(data['failed'])
        self.assertEqual(data['status'], 'pending')

        # Update payment status to paid
        payment.payment_status = 'paid'
        payment.save()

        # Poll status for paid payment
        response = self.client.get(reverse('check_payment_status', args=[self.booking.id]))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['status'], 'paid')


    def test_cancel_and_rebook_view_preserves_booking(self):
        # Create pending online payment first
        payment = Payment.objects.create(
            booking=self.booking,
            amount=500.00,
            payment_method='online',
            payment_status='pending'
        )
        response = self.client.get(reverse('cancel_and_rebook', args=[self.booking.id]))
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('booking_detail', args=[self.booking.id]))
        
        # Assert the booking was NOT deleted and payment status was marked failed
        self.assertTrue(Booking.objects.filter(id=self.booking.id).exists())
        payment.refresh_from_db()
        self.assertEqual(payment.payment_status, 'failed')


    def test_checkout_view_allows_changing_pending_payment(self):
        # Create a pending online payment
        Payment.objects.create(
            booking=self.booking,
            amount=500.00,
            payment_method='online',
            payment_status='pending'
        )
        # Verify get checkout is still accessible
        response = self.client.get(reverse('checkout', args=[self.booking.id]))
        self.assertEqual(response.status_code, 200)
        
        # Verify we can post and change method to cash
        response = self.client.post(reverse('checkout', args=[self.booking.id]), {'payment_method': 'cash'})
        self.assertEqual(response.status_code, 302)
        payment = Payment.objects.get(booking=self.booking)
        self.assertEqual(payment.payment_method, 'cash')

    def test_upi_payment_view_dynamic_inputs(self):
        Payment.objects.create(
            booking=self.booking,
            amount=500.00,
            payment_method='online',
            payment_status='pending'
        )
        # GET with dynamic upi_id and amount
        response = self.client.get(reverse('upi_payment', args=[self.booking.id]), {'upi_id': 'dynamic@upi', 'amount': '250.00'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['upi_id'], 'dynamic@upi')
        self.assertEqual(response.context['amount'], '250.00')
        self.assertIn('upi://pay?pa=dynamic%40upi', response.context['upi_uri'])
        self.assertIn('am=250.00', response.context['upi_uri'])

    def test_upi_payment_view_post_success_simulation(self):
        Payment.objects.create(
            booking=self.booking,
            amount=500.00,
            payment_method='online',
            payment_status='pending'
        )
        response = self.client.post(
            reverse('upi_payment', args=[self.booking.id]),
            {'simulation_status': 'success', 'upi_id': 'merchant@upi', 'amount': '500.00'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('payment_confirmation', args=[self.booking.id]))
        payment = Payment.objects.get(booking=self.booking)
        self.assertEqual(payment.payment_status, 'paid')
        self.assertEqual(float(payment.amount), 500.00)
        self.booking.refresh_from_db()
        self.assertEqual(self.booking.status, 'confirmed')

    def test_provider_approve_payment_confirms_booking(self):
        payment = Payment.objects.create(
            booking=self.booking,
            amount=500.00,
            payment_method='online',
            payment_status='pending'
        )
        self.client.login(username='provider_test', password='password123')
        response = self.client.post(
            reverse('manage_requests'),
            {'booking_id': self.booking.id, 'action': 'approve_payment'}
        )
        self.assertEqual(response.status_code, 200)
        self.booking.refresh_from_db()
        payment.refresh_from_db()
        self.assertEqual(payment.payment_status, 'paid')
        self.assertEqual(self.booking.status, 'confirmed')

    def test_upi_payment_view_post_failed_simulation(self):
        Payment.objects.create(
            booking=self.booking,
            amount=500.00,
            payment_method='online',
            payment_status='pending'
        )
        response = self.client.post(
            reverse('upi_payment', args=[self.booking.id]),
            {'simulation_status': 'failed', 'upi_id': 'merchant@upi', 'amount': '500.00'}
        )
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('payment_failed', args=[self.booking.id]))
        payment = Payment.objects.get(booking=self.booking)
        self.assertEqual(payment.payment_status, 'failed')
        self.assertEqual(float(payment.amount), 500.00)

    def test_check_payment_status_view_failed(self):
        payment = Payment.objects.create(
            booking=self.booking,
            amount=500.00,
            payment_method='online',
            payment_status='failed'
        )
        response = self.client.get(reverse('check_payment_status', args=[self.booking.id]))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['failed'])
        self.assertFalse(data['success'])
        self.assertEqual(data['status'], 'failed')

