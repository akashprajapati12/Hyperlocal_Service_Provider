from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Booking
from .forms import BookingForm
from services.models import Service


@login_required
def create_booking_view(request, service_id):
    """Create a booking for a service."""
    if request.user.role != 'customer':
        messages.warning(request, 'Only customers can book services.')
        return redirect('service_list')

    service = get_object_or_404(Service.objects.select_related('provider', 'provider__user'), id=service_id)

    if request.method == 'POST':
        form = BookingForm(request.POST, service=service)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.service = service
            booking.provider = service.provider
            booking.save()
            from users.models import Notification
            Notification.objects.create(
                user=booking.provider.user,
                booking=booking,
                title="New Booking Request",
                message=f"A new service is on the way, accept it (Booking #{booking.id})"
            )
            messages.success(request, 'Booking created! Proceed to payment.')
            return redirect('checkout', booking_id=booking.id)
    else:
        form = BookingForm(service=service)

    context = {
        'form': form,
        'service': service,
    }
    return render(request, 'bookings/create_booking.html', context)


@login_required
def booking_detail_view(request, booking_id):
    """View booking details with status tracker."""
    booking = get_object_or_404(
        Booking.objects.select_related('user', 'service', 'provider', 'provider__user'),
        id=booking_id
    )

    # Ensure only the booking owner, provider, or admin can view
    if request.user != booking.user and request.user != booking.provider.user and request.user.role != 'admin' and not request.user.is_superuser:
        messages.warning(request, 'Access denied.')
        return redirect('dashboard')

    has_payment = hasattr(booking, 'payment')
    has_review = booking.reviews.filter(user=request.user).exists() if request.user == booking.user else False

    can_dispute = False
    if booking.status == 'completed' and booking.completed_at and not booking.is_disputed and request.user == booking.user:
        from django.utils import timezone
        from datetime import timedelta
        if timezone.now() <= booking.completed_at + timedelta(days=2):
            can_dispute = True

    context = {
        'booking': booking,
        'has_payment': has_payment,
        'has_review': has_review,
        'can_dispute': can_dispute,
    }
    return render(request, 'bookings/booking_detail.html', context)


@login_required
def raise_dispute_view(request, booking_id):
    """Raise a dispute for a completed booking."""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    from django.utils import timezone
    from datetime import timedelta

    if booking.status != 'completed' or not booking.completed_at:
        messages.error(request, 'You can only dispute completed bookings.')
        return redirect('booking_detail', booking_id=booking.id)

    if timezone.now() > booking.completed_at + timedelta(days=2):
        messages.error(request, 'Dispute window has closed. You can only raise a dispute within 2 days of completion.')
        return redirect('booking_detail', booking_id=booking.id)

    if booking.is_disputed:
        messages.error(request, 'A dispute has already been raised for this booking.')
        return redirect('booking_detail', booking_id=booking.id)

    if request.method == 'POST':
        booking.is_disputed = True
        booking.save()

        from .models import ChatMessage
        from users.models import Notification, UserProfile
        
        # Add a system message to the chat
        ChatMessage.objects.create(
            booking=booking,
            sender=request.user,
            message="SYSTEM: A dispute has been raised regarding this booking. An administrator has been notified and will join the chat shortly to help resolve the issue."
        )
        
        # Notify admins
        admins = UserProfile.objects.filter(role='admin')
        for admin in admins:
            Notification.objects.create(
                user=admin,
                booking=booking,
                title="Dispute Raised",
                message=f"Dispute raised for Booking #{booking.id}. Please join the chat."
            )
            
        # Notify provider
        Notification.objects.create(
            user=booking.provider.user,
            booking=booking,
            title="Dispute Raised",
            message=f"A dispute was raised for Booking #{booking.id}. Check the chat."
        )

        messages.success(request, 'Dispute has been raised. You have been redirected to the dispute chat.')
        return redirect('booking_chat', booking_id=booking.id)

    return render(request, 'bookings/raise_dispute.html', {'booking': booking})


@login_required
def cancel_booking_view(request, booking_id):
    """Cancel a booking with a beautiful HTML confirmation page."""
    booking = get_object_or_404(Booking, id=booking_id, user=request.user)

    # Check if booking is in cancellable state
    if booking.status not in ('pending', 'confirmed'):
        messages.error(request, 'This booking cannot be cancelled.')
        return redirect('booking_detail', booking_id=booking.id)

    if request.method == 'POST':
        booking.status = 'cancelled'
        booking.save()
        # Refund if payment exists
        if hasattr(booking, 'payment') and booking.payment.payment_status == 'paid':
            booking.payment.payment_status = 'refunded'
            booking.payment.save()
        messages.success(request, 'Booking cancelled successfully.')
        return redirect('booking_detail', booking_id=booking.id)

    context = {
        'booking': booking,
    }
    return render(request, 'bookings/cancel_confirm.html', context)


@login_required
def booking_history_view(request):
    """All bookings for the current user."""
    if request.user.role == 'customer':
        bookings = Booking.objects.filter(user=request.user).exclude(additional_info__in=["Admin Direct Support Line", "Admin Customer Support Line"])
    elif request.user.role == 'provider':
        bookings = Booking.objects.filter(provider=request.user.provider_profile).exclude(additional_info__in=["Admin Direct Support Line", "Admin Customer Support Line"])
    else:
        bookings = Booking.objects.all()

    bookings = bookings.select_related('service', 'provider', 'provider__user', 'user').order_by('-created_at')

    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter:
        bookings = bookings.filter(status=status_filter)

    context = {
        'bookings': bookings,
        'status_filter': status_filter,
    }
    return render(request, 'bookings/booking_history.html', context)


@login_required
def add_extra_time_view(request, booking_id):
    """Allow provider to record overtime hours and auto-calculate charges."""
    booking = get_object_or_404(Booking, id=booking_id)

    # Ensure only the assigned provider can add extra time
    if request.user != booking.provider.user:
        messages.error(request, 'Access denied. Only the assigned provider can log extra time.')
        return redirect('booking_detail', booking_id=booking.id)

    if request.method == 'POST':
        try:
            extra_hours = int(request.POST.get('extra_hours', 0))
            extra_minutes = int(request.POST.get('extra_minutes', 0))
            
            if extra_hours < 0 or extra_minutes < 0 or extra_minutes >= 60:
                messages.error(request, 'Hours and minutes must be positive, and minutes must be less than 60.')
            else:
                total_extra_hours = extra_hours + (extra_minutes / 60.0)
                booking.extra_hours = total_extra_hours
                # Calculate charge using service price as direct hourly rate
                hourly_rate = float(booking.service.price)
                booking.extra_charges = total_extra_hours * hourly_rate
                booking.save()
                messages.success(request, f'Overtime logged successfully! Recorded {extra_hours}h {extra_minutes}m extra time (+₹{booking.extra_charges:.2f}).')
        except ValueError:
            messages.error(request, 'Invalid entry for hours or minutes.')

    return redirect('booking_detail', booking_id=booking.id)


@login_required
def booking_chat_view(request, booking_id):
    """Chat service between customer and provider for a confirmed booking."""
    booking = get_object_or_404(
        Booking.objects.select_related('user', 'provider', 'provider__user', 'service'),
        id=booking_id
    )

    # Ensure booking is accepted (confirmed or completed) (Admin is bypassed and can view/chat for any booking status)
    if booking.status not in ('confirmed', 'completed') and request.user.role != 'admin':
        messages.error(request, 'Chat is only available after the service provider accepts the service.')
        return redirect('booking_detail', booking_id=booking.id)

    # Access control: only the customer, provider, or administrator
    if request.user != booking.user and request.user != booking.provider.user and request.user.role != 'admin' and not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')

    # Mark unread chat notifications for this booking & user as read immediately upon opening
    from users.models import Notification
    from django.db.models import Q
    Notification.objects.filter(
        Q(title__icontains="Chat") | Q(title__icontains="Message"),
        user=request.user,
        booking=booking,
        is_read=False
    ).update(is_read=True)

    from .models import ChatMessage
    
    if request.method == 'POST':
        if booking.status in ('completed', 'cancelled') and not booking.is_disputed and request.user.role != 'admin':
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'status': 'error', 'error': 'Chat is closed.'}, status=400)
            messages.error(request, 'This conversation has been closed.')
            return redirect('booking_chat', booking_id=booking.id)
            
        message_text = request.POST.get('message', '').strip()
        if message_text:
            ChatMessage.objects.create(
                booking=booking,
                sender=request.user,
                message=message_text
            )
            # Create a silent/quick notification for the recipient(s)
            from users.models import Notification
            if request.user.role == 'admin':
                for r in (booking.user, booking.provider.user):
                    if r != request.user:
                        Notification.objects.create(
                            user=r,
                            booking=booking,
                            title="Admin Message",
                            message=f"Administrator: {message_text[:40]}"
                        )
            else:
                recipient = booking.user if request.user.id == booking.provider.user.id else booking.provider.user
                Notification.objects.create(
                    user=recipient,
                    booking=booking,
                    title=f"New Chat Message",
                    message=f"{request.user.first_name or request.user.username} sent you a message: {message_text[:40]}"
                )
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                from django.http import JsonResponse
                return JsonResponse({'status': 'success'})
            return redirect('booking_chat', booking_id=booking.id)

    chat_messages = ChatMessage.objects.filter(booking=booking).select_related('sender')
    
    context = {
        'booking': booking,
        'chat_messages': chat_messages,
    }
    return render(request, 'bookings/chat.html', context)


@login_required
def booking_messages_json(request, booking_id):
    """Retrieve chat messages as JSON for seamless modern async updates."""
    from django.http import JsonResponse
    booking = get_object_or_404(Booking, id=booking_id)

    # Access control
    if request.user != booking.user and request.user != booking.provider.user and request.user.role != 'admin' and not request.user.is_superuser:
        return JsonResponse({'error': 'Access denied'}, status=403)

    if booking.status not in ('confirmed', 'completed') and request.user.role != 'admin':
        return JsonResponse({'error': 'Chat not active'}, status=400)

    # Mark unread chat notifications for this booking & user as read immediately on polling
    from users.models import Notification
    from django.db.models import Q
    Notification.objects.filter(
        Q(title__icontains="Chat") | Q(title__icontains="Message"),
        user=request.user,
        booking=booking,
        is_read=False
    ).update(is_read=True)

    from .models import ChatMessage
    messages_qs = ChatMessage.objects.filter(booking=booking).select_related('sender').order_by('created_at')
    
    data = []
    for msg in messages_qs:
        data.append({
            'sender_id': msg.sender.id,
            'sender_name': msg.sender.get_full_name() or msg.sender.username,
            'sender_role': msg.sender.role,
            'message': msg.message,
            'created_at': msg.created_at.strftime('%I:%M %p'),
            'is_me': msg.sender.id == request.user.id
        })
    return JsonResponse({'messages': data})


from django.http import JsonResponse

def check_availability_view(request):
    """AJAX view to check booked slots for a service provider on a given date."""
    service_id = request.GET.get('service_id')
    booking_date = request.GET.get('date')
    
    if not service_id or not booking_date:
        return JsonResponse({'booked_slots': []})
        
    service = get_object_or_404(Service, id=service_id)
    provider = service.provider
    
    # Query all active bookings for this provider on this date
    # (Exclude 'cancelled' bookings so they are released)
    active_bookings = Booking.objects.filter(
        provider=provider,
        booking_date=booking_date
    ).exclude(status='cancelled')
    
    booked_slots = list(active_bookings.values_list('time_slot', flat=True))
    
    return JsonResponse({'booked_slots': booked_slots})


@login_required
def booking_chat_delete_view(request, booking_id):
    """Delete all chat messages for a given booking.
    Only the booking owner, provider, or admin can perform the deletion.
    """
    booking = get_object_or_404(Booking, id=booking_id)
    # Permission check – same logic as booking_chat_view
    if request.user != booking.user and request.user != booking.provider.user and request.user.role != 'admin' and not request.user.is_superuser:
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
    # Delete all related chat messages
    ChatMessage.objects.filter(booking=booking).delete()
    messages.success(request, 'Chat conversation has been deleted.')
    return redirect('chat_inbox')


@login_required
def chat_inbox_view(request):
    """Global Chat Inbox displaying all active/past chat conversations with unread badge."""
    from django.db.models import Q
    from .models import ChatMessage
    
    q = request.GET.get('q', '').strip()
    
    if request.user.role == 'admin':
        bookings_qs = Booking.objects.filter(chat_deleted=False).select_related('user', 'provider', 'provider__user', 'service')
    else:
        bookings_qs = Booking.objects.filter(
            Q(user=request.user) | Q(provider__user=request.user),
            chat_deleted=False
        ).select_related('user', 'provider', 'provider__user', 'service')
        
    # Standard security filtering for chat accessibility: confirmed or completed (Bypassed for administrators)
    if request.user.role != 'admin':
        bookings_qs = bookings_qs.filter(status__in=('confirmed', 'completed'))
    
    # Enable robust keyword searches
    if q:
        bookings_qs = bookings_qs.filter(
            Q(user__username__icontains=q) |
            Q(user__first_name__icontains=q) |
            Q(user__last_name__icontains=q) |
            Q(provider__user__username__icontains=q) |
            Q(provider__user__first_name__icontains=q) |
            Q(provider__user__last_name__icontains=q) |
            Q(service__service_name__icontains=q) |
            Q(id__icontains=q)
        )
        
    bookings_qs = bookings_qs.order_by('-created_at')
    
    inbox_items = []
    from .models import ChatMessage
    for b in bookings_qs:
        if request.user.role == 'admin':
            other_user = b.user
            title_display = f"{b.user.get_full_name() or b.user.username} & {b.provider.user.get_full_name() or b.provider.user.username}"
            avatar_text = "AD"
        else:
            other_user = b.provider.user if request.user == b.user else b.user
            title_display = other_user.get_full_name() or other_user.username
            
            initials = ""
            if other_user.first_name:
                initials += other_user.first_name[:1]
            if other_user.last_name:
                initials += other_user.last_name[:1]
            if not initials:
                initials = other_user.username[:1]
            avatar_text = initials.upper()
            
        # Fetch the last message
        last_msg = ChatMessage.objects.filter(booking=b).order_by('-created_at').first()
        
        inbox_items.append({
            'booking': b,
            'other_user': other_user,
            'title_display': title_display,
            'avatar_text': avatar_text,
            'last_message': last_msg,
        })
        
    discovered_users = []
    if request.user.role == 'admin' and q:
        from users.models import UserProfile
        discovered_users = UserProfile.objects.exclude(role='admin').filter(
            Q(username__icontains=q) |
            Q(first_name__icontains=q) |
            Q(last_name__icontains=q)
        ).order_by('username')[:10]
        
    context = {
        'inbox_items': inbox_items,
        'query_q': q,
        'discovered_users': discovered_users,
    }
    return render(request, 'bookings/inbox.html', context)


@login_required
def admin_start_chat_view(request, user_id):
    """Allows administrators to initiate a direct chat with any user or provider logically and isolated."""
    if request.user.role != 'admin':
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
        
    from users.models import UserProfile
    from providers.models import ServiceProvider
    from services.models import Service
    from django.utils import timezone
    from django.db.models import Q
    
    target_user = get_object_or_404(UserProfile, id=user_id)
    admin_user = request.user
    
    # 1. Create or fetch a unique ServiceProvider profile for the Admin representing Support
    admin_provider, _ = ServiceProvider.objects.get_or_create(
        user=admin_user,
        defaults={
            "skill": "System Administration & Support",
            "location": "System HQ",
            "availability_status": True,
            "bio": "Official support and mediation channel.",
            "is_verified": True
        }
    )
    
    # 2. Check if an active direct booking already exists between this admin (as provider/customer) and the target user
    if target_user.role == 'provider':
        # Admin is Customer, target is Provider
        target_provider, _ = ServiceProvider.objects.get_or_create(
            user=target_user,
            defaults={
                "skill": "General Services",
                "location": target_user.address or "Not specified",
                "availability_status": True,
                "is_verified": False
            }
        )
        existing_booking = Booking.objects.filter(user=admin_user, provider=target_provider, status__in=('confirmed', 'completed')).first()
    else:
        # Admin is Provider, target is Customer
        existing_booking = Booking.objects.filter(user=target_user, provider=admin_provider, status__in=('confirmed', 'completed')).first()
        
    if existing_booking:
        return redirect('booking_chat', booking_id=existing_booking.id)
        
    # 3. No existing direct booking exists, create a direct support line
    if target_user.role == 'provider':
        # Find or create a service listed under the target provider
        service = Service.objects.filter(provider=target_provider).first()
        if not service:
            service = Service.objects.create(
                provider=target_provider,
                service_name=f"Direct Communication with {target_user.username}",
                description="Direct admin-moderated service support line.",
                price=0.00,
                category="other"
            )
            
        booking = Booking.objects.create(
            user=admin_user,
            provider=target_provider,
            service=service,
            booking_date=timezone.now().date(),
            status='confirmed',
            additional_info="Admin Direct Support Line"
        )
    else:
        # Target user is a Customer. Admin is the Provider.
        # Find or create a service listed under the Admin's support provider profile
        service = Service.objects.filter(provider=admin_provider).first()
        if not service:
            service = Service.objects.create(
                provider=admin_provider,
                service_name="Admin Customer Support",
                description="Direct support and dispute resolution line with administrators.",
                price=0.00,
                category="other"
            )
            
        booking = Booking.objects.create(
            user=target_user,
            provider=admin_provider,
            service=service,
            booking_date=timezone.now().date(),
            status='confirmed',
            additional_info="Admin Customer Support Line"
        )
        
    return redirect('booking_chat', booking_id=booking.id)


@login_required
def delete_chat_view(request, booking_id):
    """Delete chat messages for a booking (admin or owner only)."""
    from django.http import JsonResponse
    
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'Only POST requests are allowed.'}, status=405)
    
    booking = get_object_or_404(Booking, id=booking_id)
    
    # Access control: only admin, booking owner, or provider can delete
    if request.user.role != 'admin' and request.user != booking.user and request.user != booking.provider.user:
        return JsonResponse({'status': 'error', 'message': 'Access denied.'}, status=403)
    
    try:
        from .models import ChatMessage
        # Delete all chat messages for this booking
        ChatMessage.objects.filter(booking=booking).delete()
        # Mark the chat as deleted so it doesn't reappear on refresh
        booking.chat_deleted = True
        booking.save()
        
        return JsonResponse({
            'status': 'success',
            'message': 'Chat deleted successfully.'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'An error occurred: {str(e)}'
        }, status=500)

