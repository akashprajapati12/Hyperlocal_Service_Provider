from users.models import Notification

def notification_context(request):
    if request.user.is_authenticated:
        from django.db.models import Q
        unread_count = Notification.objects.filter(
            user=request.user, 
            is_read=False
        ).exclude(Q(title__icontains="Chat") | Q(title__icontains="Message")).count()
        
        unread_chat_count = Notification.objects.filter(
            Q(title__icontains="Chat") | Q(title__icontains="Message"),
            user=request.user, 
            is_read=False
        ).count()
        return {
            'unread_notifications_count': unread_count,
            'unread_chat_notifications_count': unread_chat_count
        }
    return {
        'unread_notifications_count': 0,
        'unread_chat_notifications_count': 0
    }
