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
        
        return JsonResponse({
            'status': 'success',
            'message': 'Chat deleted successfully.'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'error',
            'message': f'An error occurred: {str(e)}'
        }, status=500)
