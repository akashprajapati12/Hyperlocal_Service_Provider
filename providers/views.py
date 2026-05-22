from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count
from .forms import ProviderRegistrationForm, ProviderProfileForm
from .models import ServiceProvider
from services.models import Service
from services.forms import ServiceForm
from bookings.models import Booking
from payments.models import Payment
from users.forms import UserProfileUpdateForm


def provider_register_view(request):
    """Provider registration."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = ProviderRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Provider account created! Complete your profile to start receiving bookings.')
            return redirect('provider_dashboard')
    else:
        form = ProviderRegistrationForm()

    return render(request, 'providers/register.html', {'form': form})


@login_required
def provider_dashboard(request):
    """Provider dashboard with stats."""
    if request.user.role != 'provider':
        messages.warning(request, 'Access denied.')
        return redirect('dashboard')

    try:
        provider = request.user.provider_profile
    except ServiceProvider.DoesNotExist:
        messages.error(request, 'Provider profile not found.')
        return redirect('home')

    bookings = Booking.objects.filter(provider=provider).select_related('user', 'service').exclude(additional_info__in=["Admin Direct Support Line", "Admin Customer Support Line"])
    total_earnings = Payment.objects.filter(
        booking__provider=provider,
        payment_status='paid'
    ).aggregate(total=Sum('amount'))['total'] or 0

    context = {
        'provider': provider,
        'total_bookings': bookings.count(),
        'pending_requests': bookings.filter(status='pending').count(),
        'completed_bookings': bookings.filter(status='completed').count(),
        'cancelled_bookings': bookings.filter(status='cancelled').count(),
        'total_earnings': total_earnings,
        'recent_bookings': bookings[:5],
    }
    return render(request, 'providers/dashboard.html', context)


@login_required
def add_service_view(request):
    """Add a new service listing."""
    if request.user.role != 'provider':
        messages.warning(request, 'Access denied.')
        return redirect('dashboard')

    try:
        provider = request.user.provider_profile
    except ServiceProvider.DoesNotExist:
        messages.error(request, 'Provider profile not found.')
        return redirect('home')

    if request.method == 'POST':
        form = ServiceForm(request.POST)
        if form.is_valid():
            service = form.save(commit=False)
            service.provider = provider
            service.save()
            messages.success(request, 'Service added successfully!')
            return redirect('provider_dashboard')
    else:
        form = ServiceForm()

    return render(request, 'providers/add_service.html', {'form': form})


@login_required
def manage_requests_view(request):
    """Manage booking requests (accept/reject)."""
    if request.user.role != 'provider':
        messages.warning(request, 'Access denied.')
        return redirect('dashboard')

    try:
        provider = request.user.provider_profile
    except ServiceProvider.DoesNotExist:
        messages.error(request, 'Provider profile not found.')
        return redirect('home')

    if request.method == 'POST':
        booking_id = request.POST.get('booking_id')
        action = request.POST.get('action')
        booking = get_object_or_404(Booking, id=booking_id, provider=provider)

        if action == 'accept':
            booking.status = 'confirmed'
            booking.save()
            from users.models import Notification
            Notification.objects.create(
                user=booking.user,
                booking=booking,
                title="Booking Accepted",
                message=f"Your service has been accepted (Booking #{booking.id})"
            )
            Notification.objects.create(
                user=booking.provider.user,
                booking=booking,
                title="Booking Confirmed",
                message=f"You have accepted the booking. Contact information and chat are now active. (Booking #{booking.id})"
            )
            messages.success(request, f'Booking #{booking.id} confirmed!')
        elif action == 'reject':
            booking.status = 'cancelled'
            booking.save()
            # Refund if payment exists and was paid
            if hasattr(booking, 'payment') and booking.payment.payment_status == 'paid':
                booking.payment.payment_status = 'refunded'
                booking.payment.save()
            from users.models import Notification
            Notification.objects.create(
                user=booking.user,
                booking=booking,
                title="Booking Request Declined",
                message=f"Your booking #{booking.id} request has been declined by the provider."
            )
            messages.info(request, f'Booking #{booking.id} cancelled.')
        elif action == 'complete':
            booking.status = 'completed'
            from django.utils import timezone
            booking.completed_at = timezone.now()
            booking.save()
            messages.success(request, f'Booking #{booking.id} marked as completed!')
        elif action == 'approve_payment':
            if hasattr(booking, 'payment'):
                payment = booking.payment
                payment.payment_status = 'paid'
                payment.save()
                
                # Automatically confirm booking when payment is approved by provider
                booking.status = 'confirmed'
                booking.save()
                
                from users.models import Notification
                Notification.objects.create(
                    user=booking.user,
                    booking=booking,
                    title="Payment Confirmed",
                    message=f"The provider has approved and confirmed receipt of your payment for Booking #{booking.id}."
                )
                messages.success(request, f'Payment for Booking #{booking.id} approved successfully!')
            else:
                messages.error(request, 'No payment record found for this booking.')

    bookings = Booking.objects.filter(provider=provider).select_related('user', 'service').exclude(additional_info__in=["Admin Direct Support Line", "Admin Customer Support Line"]).order_by('-created_at')

    context = {
        'bookings': bookings,
    }
    return render(request, 'providers/manage_requests.html', context)


@login_required
def update_profile_view(request):
    """Update provider profile."""
    if request.user.role != 'provider':
        messages.warning(request, 'Access denied.')
        return redirect('dashboard')

    try:
        provider = request.user.provider_profile
    except ServiceProvider.DoesNotExist:
        messages.error(request, 'Provider profile not found.')
        return redirect('home')

    if request.method == 'POST':
        user_form = UserProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        provider_form = ProviderProfileForm(request.POST, instance=provider)
        if user_form.is_valid() and provider_form.is_valid():
            user_form.save()
            provider_form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('provider_update_profile')
    else:
        user_form = UserProfileUpdateForm(instance=request.user)
        provider_form = ProviderProfileForm(instance=provider)

    context = {
        'user_form': user_form,
        'provider_form': provider_form,
    }
    return render(request, 'providers/update_profile.html', context)


@login_required
def my_services_view(request):
    """View and manage provider's services."""
    if request.user.role != 'provider':
        messages.warning(request, 'Access denied.')
        return redirect('dashboard')

    try:
        provider = request.user.provider_profile
    except ServiceProvider.DoesNotExist:
        messages.error(request, 'Provider profile not found.')
        return redirect('home')

    services = Service.objects.filter(provider=provider)
    context = {
        'services': services,
    }
    return render(request, 'providers/my_services.html', context)


@login_required
def delete_service_view(request, service_id):
    """Delete a service."""
    if request.user.role != 'provider':
        messages.warning(request, 'Access denied.')
        return redirect('dashboard')

    service = get_object_or_404(Service, id=service_id, provider=request.user.provider_profile)
    if request.method == 'POST':
        service.delete()
        messages.success(request, 'Service deleted successfully!')
    return redirect('my_services')
