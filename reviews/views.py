from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Review
from .forms import ReviewForm
from bookings.models import Booking


@login_required
def add_review_view(request, booking_id):
    """Add a review (only after booking is completed)."""
    booking = get_object_or_404(
        Booking.objects.select_related('service', 'provider', 'provider__user'),
        id=booking_id,
        user=request.user
    )

    if booking.status != 'completed':
        messages.warning(request, 'You can only review completed bookings.')
        return redirect('booking_detail', booking_id=booking.id)

    # Check if already reviewed
    if Review.objects.filter(user=request.user, booking=booking).exists():
        messages.info(request, 'You have already reviewed this booking.')
        return redirect('booking_detail', booking_id=booking.id)

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.user = request.user
            review.service = booking.service
            review.booking = booking
            review.save()
            messages.success(request, 'Thank you for your review!')
            return redirect('booking_detail', booking_id=booking.id)
    else:
        form = ReviewForm()

    context = {
        'form': form,
        'booking': booking,
    }
    return render(request, 'reviews/add_review.html', context)
