from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime

from .models import Payment
from .forms import PaymentForm
from bookings.models import Booking
import qrcode
import base64
import urllib.parse
from io import BytesIO


@login_required
def checkout_view(request, booking_id):
    """Payment form after booking."""
    booking = get_object_or_404(
        Booking.objects.select_related('service', 'provider', 'provider__user'),
        id=booking_id,
        user=request.user
    )

    if hasattr(booking, 'payment'):
        payment = booking.payment
        if payment.payment_status == 'paid' or payment.status == 'success':
            messages.info(request, 'Payment already processed for this booking.')
            return redirect('payment_confirmation', booking_id=booking.id)

    if request.method == 'POST':
        form = PaymentForm(request.POST)
        if form.is_valid():
            Payment.objects.filter(booking=booking).delete()
            payment = form.save(commit=False)
            payment.booking = booking
            payment.amount = booking.total_price
            payment.payment_status = 'pending'
            if payment.payment_method == 'cash':
                payment.save()
                messages.success(request, 'Cash on Service selected. Payment is pending provider approval.')
                return redirect('payment_confirmation', booking_id=booking.id)
            payment.save()
            request.session['pending_txn_id'] = str(payment.transaction_id)
            request.session['pending_booking_id'] = booking.id
            messages.info(request, 'Please complete the online UPI payment.')
            return redirect('upi_payment', booking_id=booking.id)
    else:
        form = PaymentForm()

    context = {
        'form': form,
        'booking': booking,
    }
    return render(request, 'payments/checkout.html', context)


@login_required
def payment_confirmation_view(request, booking_id):
    """Payment success page."""
    booking = get_object_or_404(
        Booking.objects.select_related('service', 'provider', 'provider__user'),
        id=booking_id,
        user=request.user
    )
    payment = get_object_or_404(Payment, booking=booking)

    context = {
        'booking': booking,
        'payment': payment,
    }
    return render(request, 'payments/confirmation.html', context)


@login_required
def payment_failed_view(request, booking_id):
    """Payment failed page."""
    booking = get_object_or_404(
        Booking.objects.select_related('service', 'provider', 'provider__user'),
        id=booking_id,
        user=request.user
    )
    payment = get_object_or_404(Payment, booking=booking)

    context = {
        'booking': booking,
        'payment': payment,
    }
    return render(request, 'payments/failed.html', context)


@login_required
def upi_payment_view(request, booking_id):
    """Online UPI payment page with server-side QR code generation."""
    booking = get_object_or_404(
        Booking.objects.select_related('service', 'provider', 'provider__user'),
        id=booking_id,
        user=request.user
    )
    payment = get_object_or_404(Payment, booking=booking, payment_method='online')

    if payment.payment_status == 'paid' or payment.status == 'success':
        request.session.pop('pending_txn_id', None)
        request.session.pop('pending_booking_id', None)
        return redirect('payment_confirmation', booking_id=booking.id)

    request.session['pending_txn_id'] = str(payment.transaction_id)
    request.session['pending_booking_id'] = booking.id

    session_key = f'upi_loaded_{booking.id}'
    if session_key not in request.session:
        request.session[session_key] = timezone.now().isoformat()

    upi_id = request.GET.get('upi_id', request.POST.get('upi_id', 'akashairmen-1@okicici')).strip()
    amount_str = request.GET.get('amount', request.POST.get('amount', str(booking.total_price))).strip()

    try:
        amount_val = float(amount_str)
        if amount_val <= 0:
            amount_val = float(booking.total_price)
    except (ValueError, TypeError):
        amount_val = float(booking.total_price)

    try:
        load_time = datetime.fromisoformat(request.session.get(session_key, ''))
        if timezone.is_naive(load_time):
            load_time = timezone.make_aware(load_time)
        elapsed = (timezone.now() - load_time).total_seconds()
    except (TypeError, ValueError, AttributeError):
        elapsed = 0

    time_left = max(0, int(120 - elapsed))
    txn_id_str = str(payment.transaction_id) if payment.transaction_id else ''
    transaction_note = f'Booking_{booking.id}_Txn_{txn_id_str}'
    upi_uri = (
        f'upi://pay?pa={urllib.parse.quote(upi_id)}&am={amount_val:.2f}'
        f'&tn={urllib.parse.quote(transaction_note)}&cu=INR'
    )

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=1,
    )
    qr.add_data(upi_uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color='#0f172a', back_color='#ffffff')
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    qr_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    qr_data_url = f'data:image/png;base64,{qr_base64}'

    context = {
        'booking': booking,
        'payment': payment,
        'payment_success': payment.payment_status == 'paid',
        'qr_data_url': qr_data_url,
        'time_left': time_left,
        'upi_id': upi_id,
        'amount': f'{amount_val:.2f}',
        'upi_uri': upi_uri,
    }

    if request.method == 'POST':
        if request.POST.get('confirm_paid'):
            payment.amount = amount_val
            payment.payment_status = 'paid'
            payment.status = 'success'
            payment.save()
            try:
                from users.models import Notification
                Notification.objects.create(
                    user=booking.provider.user,
                    booking=booking,
                    title='Booking Paid Online',
                    message=f'Customer has completed online payment of ₹{amount_val:.2f} for Booking #{booking.id}.'
                )
            except Exception:
                pass
            messages.success(request, 'Payment marked as received. Your booking is confirmed.')
            return redirect('payment_confirmation', booking.id)

        simulation_status = request.POST.get('simulation_status')
        if simulation_status:
            payment.amount = amount_val
            if simulation_status == 'failed':
                payment.payment_status = 'failed'
                payment.status = 'failed'
                payment.save()
                return redirect('payment_failed', booking.id)

            payment.payment_status = 'paid'
            payment.status = 'success'
            payment.save()
            try:
                from users.models import Notification
                Notification.objects.create(
                    user=booking.provider.user,
                    booking=booking,
                    title='Booking Paid Online',
                    message=f'Customer has completed online payment of ₹{amount_val:.2f} for Booking #{booking.id}.'
                )
            except Exception:
                pass
            return redirect('payment_confirmation', booking.id)

        messages.info(
            request,
            'If you already paid, click the button again to confirm the payment. Otherwise you may cancel the booking.'
        )
        return redirect('upi_payment', booking.id)

    return render(request, 'payments/upi_payment.html', context)


@login_required
def check_payment_status_view(request, booking_id):
    """AJAX polling view to verify payment status."""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    payment = get_object_or_404(Payment, booking=booking, payment_method='online')
    payment.refresh_from_db()

    if payment.payment_status == 'paid' and payment.status != 'success':
        payment.status = 'success'
        payment.save(update_fields=['status'])
    elif payment.status == 'success' and payment.payment_status != 'paid':
        payment.payment_status = 'paid'
        payment.save(update_fields=['payment_status'])
    elif payment.payment_status == 'failed' and payment.status != 'failed':
        payment.status = 'failed'
        payment.save(update_fields=['status'])
    elif payment.status == 'failed' and payment.payment_status != 'failed':
        payment.payment_status = 'failed'
        payment.save(update_fields=['payment_status'])

    return JsonResponse({
        'status': 'paid' if payment.status == 'success' else payment.status,
        'transaction_id': str(payment.transaction_id) if payment.transaction_id else '',
        'success': payment.status == 'success' or payment.payment_status == 'paid',
        'failed': payment.status == 'failed' or payment.payment_status == 'failed',
    })


def check_payment(request, transaction_id):
    """Payment lookup endpoint used by external polling or UPI callbacks."""
    try:
        payment = Payment.objects.get(transaction_id=transaction_id)
    except Payment.DoesNotExist:
        return JsonResponse({'status': 'not_found'}, status=404)

    payment.refresh_from_db()
    changed = False
    if payment.payment_status == 'paid' and payment.status != 'success':
        payment.status = 'success'
        changed = True
    elif payment.status == 'success' and payment.payment_status != 'paid':
        payment.payment_status = 'paid'
        changed = True
    elif payment.payment_status == 'failed' and payment.status != 'failed':
        payment.status = 'failed'
        changed = True
    elif payment.status == 'failed' and payment.payment_status != 'failed':
        payment.payment_status = 'failed'
        changed = True

    if changed:
        payment.save(update_fields=['status', 'payment_status', 'updated_at'])

    return JsonResponse({'status': payment.status})


@login_required
def payment_success_redirect_view(request):
    booking_id = request.session.get('pending_booking_id')
    if not booking_id:
        messages.error(request, 'Session expired. Please contact support.')
        return redirect('dashboard')

    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    request.session.pop('pending_txn_id', None)
    request.session.pop('pending_booking_id', None)
    return redirect('payment_confirmation', booking_id=booking.id)


@login_required
def payment_failed_redirect_view(request):
    booking_id = request.session.get('pending_booking_id')
    if not booking_id:
        messages.error(request, 'Session expired. Please contact support.')
        return redirect('dashboard')

    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    request.session.pop('pending_txn_id', None)
    request.session.pop('pending_booking_id', None)
    return redirect('payment_failed', booking_id=booking.id)


@login_required
def cancel_and_rebook_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)
    if hasattr(booking, 'payment'):
        payment = booking.payment
        if payment.payment_status == 'pending':
            payment.payment_status = 'failed'
            payment.status = 'failed'
            payment.save()

    request.session.pop('pending_txn_id', None)
    request.session.pop('pending_booking_id', None)
    messages.warning(request, 'Payment cancelled. Your booking is preserved.')
    return redirect('booking_detail', booking_id=booking.id)


@login_required
def cancel_booking_from_payment_view(request, booking_id):
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    if request.method != 'POST':
        return redirect('booking_detail', booking_id=booking.id)

    if booking.status not in ('pending', 'confirmed'):
        messages.error(request, 'This booking cannot be cancelled at this time.')
        return redirect('booking_detail', booking_id=booking.id)

    if hasattr(booking, 'payment'):
        payment = booking.payment
        if payment.payment_status == 'pending':
            payment.payment_status = 'failed'
            payment.status = 'failed'
            payment.save()
        elif payment.payment_status == 'paid':
            payment.payment_status = 'refunded'
            payment.status = 'refunded'
            payment.save()

    booking.status = 'cancelled'
    booking.save(update_fields=['status'])
    request.session.pop('pending_txn_id', None)
    request.session.pop('pending_booking_id', None)
    messages.warning(request, 'Booking cancelled successfully.')
    return redirect('booking_detail', booking_id=booking.id)
