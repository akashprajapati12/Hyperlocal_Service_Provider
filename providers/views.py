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
        form = ProviderRegistrationForm(request.POST, request.FILES)
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
        return redirect('dashboard')

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
        return redirect('dashboard')

    if request.method == 'POST':
        form = ServiceForm(request.POST)
        if form.is_valid():
            # Update provider details
            provider.skill = form.cleaned_data['skill']
            provider.location = form.cleaned_data['location']
            provider.bio = form.cleaned_data['bio']
            provider.save()

            # Save service
            service = form.save(commit=False)
            service.provider = provider
            service.save()
            messages.success(request, 'Service added successfully!')
            return redirect('provider_dashboard')
    else:
        form = ServiceForm(initial={
            'skill': provider.skill,
            'location': provider.location,
            'bio': provider.bio,
        })

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
        return redirect('dashboard')

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
                message=f"Your service has been accepted (Booking #{booking.formatted_id})"
            )
            messages.success(request, f'Booking #{booking.formatted_id} confirmed!')
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
                message=f"Your booking #{booking.formatted_id} request has been declined by the provider."
            )
            messages.info(request, f'Booking #{booking.formatted_id} cancelled.')
        elif action == 'complete':
            booking.status = 'completed'
            from django.utils import timezone
            booking.completed_at = timezone.now()
            booking.save()
            messages.success(request, f'Booking #{booking.formatted_id} marked as completed!')
        elif action == 'approve_payment':
            if hasattr(booking, 'payment'):
                payment = booking.payment
                payment.payment_status = 'paid'
                payment.save()
                
                from users.models import Notification
                Notification.objects.create(
                    user=booking.user,
                    booking=booking,
                    title="Payment Confirmed",
                    message=f"The provider has approved and confirmed receipt of your payment for Booking #{booking.formatted_id}."
                )
                messages.success(request, f'Payment for Booking #{booking.formatted_id} approved successfully!')
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
        return redirect('dashboard')

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
        return redirect('dashboard')

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


from math import radians, cos, sin, asin, sqrt
from django.db.models import Q

def get_distance(lat1, lon1, lat2, lon2):
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return None
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * asin(sqrt(a))
    r = 6371 # Radius of Earth in km
    return round(c * r, 2)


def provider_search_view(request):
    """Search providers by city/pincode and sort by distance if location coordinates are available."""
    providers = ServiceProvider.objects.select_related('user').all()

    # Filter to show available providers
    providers = providers.filter(availability_status=True)

    q = request.GET.get('q', '').strip()
    if q:
        import re
        has_letters = bool(re.search(r'[a-zA-Z]', q))
        has_digits = bool(re.search(r'\d', q))
        if has_letters and has_digits:
            pincode_match = re.search(r'\d+', q)
            if pincode_match:
                pincode = pincode_match.group(0)
                providers = providers.filter(pincode__icontains=pincode)
            else:
                providers = providers.filter(
                    Q(city__icontains=q) |
                    Q(pincode__icontains=q) |
                    Q(location__icontains=q)
                )
        else:
            providers = providers.filter(
                Q(city__icontains=q) |
                Q(pincode__icontains=q) |
                Q(location__icontains=q)
            )

    try:
        user_lat = float(request.GET.get('lat'))
        user_lon = float(request.GET.get('lon'))
    except (ValueError, TypeError, KeyError):
        user_lat, user_lon = None, None

    providers_list = []
    for p in providers:
        if p.latitude is not None and p.longitude is not None and user_lat is not None and user_lon is not None:
            p.distance = get_distance(user_lat, user_lon, p.latitude, p.longitude)
        else:
            p.distance = None
        providers_list.append(p)

    # Sort providers by distance (nearest first). Providers without distance go to the end.
    providers_list.sort(key=lambda x: (x.distance is None, x.distance or 0))

    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1'
    if is_ajax:
        return render(request, 'providers/provider_list_cards.html', {
            'providers': providers_list,
            'user_lat': user_lat,
            'user_lon': user_lon,
        })

    context = {
        'providers': providers_list,
        'q_query': q,
        'user_lat': user_lat,
        'user_lon': user_lon,
    }
    return render(request, 'providers/provider_search.html', context)


def provider_public_profile_view(request, provider_id):
    """View provider profile with list of services, prices, and reviews."""
    provider = get_object_or_404(ServiceProvider.objects.select_related('user'), id=provider_id)
    services = provider.services.all()

    from reviews.models import Review
    reviews = Review.objects.filter(service__provider=provider).select_related('user', 'service').order_by('-review_date')

    context = {
        'provider': provider,
        'services': services,
        'reviews': reviews,
        'avg_rating': provider.average_rating,
        'review_count': provider.review_count,
        'rating_range': range(1, 6),
    }
    return render(request, 'providers/provider_public_profile.html', context)
