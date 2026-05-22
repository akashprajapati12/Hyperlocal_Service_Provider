from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Avg
from .models import Service
from reviews.models import Review


def service_list_view(request):
    """Grid of service cards with category filter and search."""
    services = Service.objects.select_related('provider', 'provider__user').all()

    # Category filter
    category = request.GET.get('category', '')
    if category:
        services = services.filter(category=category)

    # Search
    search = request.GET.get('search', '')
    if search:
        services = services.filter(
            Q(service_name__icontains=search) |
            Q(description__icontains=search) |
            Q(provider__user__first_name__icontains=search) |
            Q(provider__user__last_name__icontains=search) |
            Q(provider__location__icontains=search)
        )

    # Add average rating to each service
    for service in services:
        avg = service.reviews.aggregate(avg_rating=Avg('rating'))['avg_rating']
        service.avg_rating = round(avg, 1) if avg else 0
        service.review_count = service.reviews.count()

    categories = Service.CATEGORY_CHOICES

    context = {
        'services': services,
        'categories': categories,
        'selected_category': category,
        'search_query': search,
    }
    return render(request, 'services/service_list.html', context)


def service_detail_view(request, service_id):
    """Service detail page with reviews and Book Now button."""
    service = get_object_or_404(
        Service.objects.select_related('provider', 'provider__user'),
        id=service_id
    )
    reviews = Review.objects.filter(service=service).select_related('user').order_by('-review_date')
    avg_rating = reviews.aggregate(avg=Avg('rating'))['avg'] or 0

    context = {
        'service': service,
        'reviews': reviews,
        'avg_rating': round(avg_rating, 1),
        'review_count': reviews.count(),
        'rating_range': range(1, 6),
    }
    return render(request, 'services/service_detail.html', context)
