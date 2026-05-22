from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import UnifiedRegistrationForm, UserProfileUpdateForm, LoginForm
from bookings.models import Booking


def home_view(request):
    """Landing page — providers/admins skip to dashboard."""
    context = {}
    if request.user.is_authenticated:
        if request.user.role == 'provider':
            return redirect('provider_dashboard')
        elif request.user.role == 'admin':
            return redirect('admin_dashboard')
        else:
            # Customer role
            from reviews.models import Review
            from django.db.models import Avg
            
            bookings = Booking.objects.filter(user=request.user).select_related('service', 'provider', 'provider__user').exclude(additional_info__in=["Admin Direct Support Line", "Admin Customer Support Line"])
            total_bookings = bookings.count()
            last_booking = bookings.order_by('-created_at').first()
            
            context['bookings'] = bookings
            context['total_bookings'] = total_bookings
            context['last_booking'] = last_booking
            context['pending_bookings'] = bookings.filter(status='pending').count()
            context['completed_bookings'] = bookings.filter(status='completed').count()
            context['cancelled_bookings'] = bookings.filter(status='cancelled').count()
            
            if last_booking:
                provider = last_booking.provider
                context['hired_provider'] = provider
                
                # Calculate provider's average rating across all reviews of their services
                avg = Review.objects.filter(service__provider=provider).aggregate(avg_rating=Avg('rating'))['avg_rating']
                context['provider_rating'] = round(avg, 1) if avg else 0.0
                context['provider_review_count'] = Review.objects.filter(service__provider=provider).count()
                
    return render(request, 'home.html', context)


def register_view(request):
    """Unified registration with role selection."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = UnifiedRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Account created successfully! Welcome aboard.')
            if user.role == 'provider':
                return redirect('provider_dashboard')
            return redirect('customer_dashboard')
    else:
        form = UnifiedRegistrationForm()

    return render(request, 'users/register.html', {'form': form})


def login_view(request):
    """Login with role-based redirect."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {user.first_name or user.username}!')
                # Role-based redirect
                if user.role == 'admin':
                    return redirect('admin_dashboard')
                elif user.role == 'provider':
                    return redirect('provider_dashboard')
                else:
                    return redirect('customer_dashboard')
            else:
                messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()

    return render(request, 'users/login.html', {'form': form})


def logout_view(request):
    """Logout."""
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('home')


@login_required
def dashboard_redirect(request):
    """Redirect to the appropriate dashboard based on role."""
    if request.user.role == 'admin':
        return redirect('admin_dashboard')
    elif request.user.role == 'provider':
        return redirect('provider_dashboard')
    else:
        return redirect('customer_dashboard')


@login_required
def customer_dashboard(request):
    """Customer dashboard showing booking history."""
    if request.user.role != 'customer':
        messages.warning(request, 'Access denied.')
        return redirect('dashboard')

    bookings = Booking.objects.filter(user=request.user).select_related('service', 'provider', 'provider__user').exclude(additional_info__in=["Admin Direct Support Line", "Admin Customer Support Line"])
    context = {
        'bookings': bookings,
        'total_bookings': bookings.count(),
        'pending_bookings': bookings.filter(status='pending').count(),
        'completed_bookings': bookings.filter(status='completed').count(),
        'cancelled_bookings': bookings.filter(status='cancelled').count(),
    }
    return render(request, 'users/customer_dashboard.html', context)


@login_required
def profile_view(request):
    """View profile (read-only)."""
    return render(request, 'users/profile.html')


@login_required
def edit_profile_view(request):
    """Edit profile form."""
    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = UserProfileUpdateForm(instance=request.user)

    return render(request, 'users/edit_profile.html', {'form': form})


def about_view(request):
    """About Us page."""
    return render(request, 'about.html')


def contact_view(request):
    """Contact Us page."""
    if request.method == 'POST':
        messages.success(request, 'Thank you! Your message has been received. We will get back to you shortly.')
        return redirect('contact')
    return render(request, 'contact.html')


def feedback_view(request):
    """Feedback page."""
    if request.method == 'POST':
        messages.success(request, 'Thank you for your valuable feedback!')
        return redirect('feedback')
    return render(request, 'feedback.html')


@login_required
def notifications_view(request):
    """View to list all notifications and system alerts."""
    from .models import Notification
    
    # Mark all notifications as read if requested
    from django.db.models import Q
    if request.method == 'POST' and request.POST.get('action') == 'mark_all_read':
        Notification.objects.filter(user=request.user, is_read=False).exclude(Q(title__icontains="Chat") | Q(title__icontains="Message")).update(is_read=True)
        messages.success(request, 'All notifications marked as read.')
        return redirect('notifications')
        
    notifications = Notification.objects.filter(user=request.user).exclude(Q(title__icontains="Chat") | Q(title__icontains="Message"))
    
    # Let's support marking an individual notification as read
    notif_id = request.GET.get('read')
    if notif_id:
        Notification.objects.filter(user=request.user, id=notif_id).update(is_read=True)
        return redirect('notifications')
        
    return render(request, 'users/notifications.html', {
        'notifications': notifications,
    })


from django.urls import reverse

@login_required
def notification_click_view(request, notif_id):
    """Mark a notification as read and redirect to the corresponding page (booking or chat)."""
    from .models import Notification
    notification = get_object_or_404(Notification, id=notif_id, user=request.user)
    
    # Mark as read
    notification.is_read = True
    notification.save()
    
    # Determine the target redirect URL
    if not notification.booking:
        import re
        match = re.search(r'#(\d+)', notification.message) or re.search(r'#(\d+)', notification.title)
        if match:
            booking_id = int(match.group(1))
            from bookings.models import Booking
            try:
                booking = Booking.objects.get(id=booking_id)
                notification.booking = booking
                notification.save()
            except Booking.DoesNotExist:
                pass

    if notification.booking:
        title_lower = notification.title.lower()
        if "chat" in title_lower or "message" in title_lower:
            return redirect('booking_chat', booking_id=notification.booking.id)
        else:
            return redirect('booking_detail', booking_id=notification.booking.id)
            
    return redirect('notifications')

