from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count
from users.models import UserProfile
from providers.models import ServiceProvider
from bookings.models import Booking
from payments.models import Payment
from services.models import Service


def admin_required(view_func):
    """Decorator to restrict access to admin users."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'admin':
            messages.warning(request, 'Admin access required.')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


@admin_required
def admin_dashboard(request):
    """Admin dashboard with stats and charts."""
    total_users = UserProfile.objects.filter(role='customer').count()
    total_providers = ServiceProvider.objects.count()
    total_bookings = Booking.objects.count()
    total_revenue = Payment.objects.filter(payment_status='paid').aggregate(
        total=Sum('amount')
    )['total'] or 0

    # Monthly revenue data (last 6 months)
    from django.db.models.functions import TruncMonth
    from django.utils import timezone
    import json

    monthly_revenue = (
        Payment.objects.filter(payment_status='paid')
        .annotate(month=TruncMonth('payment_date'))
        .values('month')
        .annotate(revenue=Sum('amount'))
        .order_by('month')
    )
    chart_labels = [item['month'].strftime('%b %Y') for item in monthly_revenue] if monthly_revenue else []
    chart_data = [float(item['revenue']) for item in monthly_revenue] if monthly_revenue else []

    # Booking status distribution
    booking_status = (
        Booking.objects.values('status')
        .annotate(count=Count('id'))
    )
    status_labels = [item['status'].title() for item in booking_status]
    status_data = [item['count'] for item in booking_status]

    # Category distribution
    category_dist = (
        Service.objects.values('category')
        .annotate(count=Count('id'))
    )
    cat_labels = [item['category'].title() for item in category_dist]
    cat_data = [item['count'] for item in category_dist]

    recent_bookings = Booking.objects.select_related(
        'user', 'service', 'provider', 'provider__user'
    ).order_by('-created_at')[:10]

    context = {
        'total_users': total_users,
        'total_providers': total_providers,
        'total_bookings': total_bookings,
        'total_revenue': total_revenue,
        'chart_labels': json.dumps(chart_labels),
        'chart_data': json.dumps(chart_data),
        'status_labels': json.dumps(status_labels),
        'status_data': json.dumps(status_data),
        'cat_labels': json.dumps(cat_labels),
        'cat_data': json.dumps(cat_data),
        'recent_bookings': recent_bookings,
    }
    return render(request, 'admin_panel/dashboard.html', context)


@admin_required
def manage_users_view(request):
    """Manage all users with activate/deactivate."""
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        action = request.POST.get('action')
        user = get_object_or_404(UserProfile, id=user_id)

        if action == 'activate':
            user.is_active = True
            user.save()
            messages.success(request, f'User {user.username} activated.')
        elif action == 'deactivate':
            user.is_active = False
            user.save()
            messages.success(request, f'User {user.username} deactivated.')

    users = UserProfile.objects.filter(role='customer').order_by('-date_joined')
    context = {'users': users}
    return render(request, 'admin_panel/manage_users.html', context)


@admin_required
def manage_providers_view(request):
    """Manage providers with verify option."""
    if request.method == 'POST':
        provider_id = request.POST.get('provider_id')
        action = request.POST.get('action')
        provider = get_object_or_404(ServiceProvider, id=provider_id)

        if action == 'verify':
            provider.is_verified = True
            provider.save()
            messages.success(request, f'Provider {provider.user.username} verified.')
        elif action == 'unverify':
            provider.is_verified = False
            provider.save()
            messages.success(request, f'Provider {provider.user.username} verification removed.')

    providers = ServiceProvider.objects.select_related('user').all()
    context = {'providers': providers}
    return render(request, 'admin_panel/manage_providers.html', context)


@admin_required
def manage_bookings_view(request):
    """All bookings with status filter."""
    bookings = Booking.objects.select_related(
        'user', 'service', 'provider', 'provider__user'
    ).exclude(additional_info__in=["Admin Direct Support Line", "Admin Customer Support Line"]).order_by('-created_at')

    status_filter = request.GET.get('status', '')
    if status_filter:
        bookings = bookings.filter(status=status_filter)

    context = {
        'bookings': bookings,
        'status_filter': status_filter,
    }
    return render(request, 'admin_panel/manage_bookings.html', context)


@admin_required
def admin_booking_detail_view(request, booking_id):
    """View full booking details inside the admin panel."""
    booking = get_object_or_404(
        Booking.objects.select_related('user', 'service', 'provider', 'provider__user'),
        id=booking_id
    )
    
    # Retrieve payment if it exists
    has_payment = hasattr(booking, 'payment')
    payment = booking.payment if has_payment else None
    
    # Retrieve reviews if any
    reviews = booking.reviews.all().select_related('user')
    
    # Retrieve chat messages for quick preview or audit
    from bookings.models import ChatMessage
    chat_messages = ChatMessage.objects.filter(booking=booking).select_related('sender').order_by('created_at')

    context = {
        'booking': booking,
        'payment': payment,
        'has_payment': has_payment,
        'reviews': reviews,
        'chat_messages': chat_messages,
    }
    return render(request, 'admin_panel/booking_detail.html', context)



@admin_required
def admin_user_detail_view(request, user_id):
    """View full profile information for any user or provider inside the admin panel."""
    user = get_object_or_404(UserProfile, id=user_id)
    
    # Check if they have a provider profile
    provider_profile = getattr(user, 'provider_profile', None)
    
    bookings = []
    services = []
    if user.role == 'customer':
        bookings = Booking.objects.filter(user=user).select_related('service', 'provider', 'provider__user').exclude(additional_info__in=["Admin Direct Support Line", "Admin Customer Support Line"]).order_by('-created_at')
    elif user.role == 'provider' and provider_profile:
        bookings = Booking.objects.filter(provider=provider_profile).select_related('user', 'service').exclude(additional_info__in=["Admin Direct Support Line", "Admin Customer Support Line"]).order_by('-created_at')
        services = Service.objects.filter(provider=provider_profile).order_by('-id')
        
    context = {
        'target_user': user,
        'provider_profile': provider_profile,
        'bookings': bookings,
        'services': services,
    }
    return render(request, 'admin_panel/user_detail.html', context)
