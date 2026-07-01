from django.shortcuts import render, get_object_or_404
from django.db.models import Q, Avg
from .models import Service
from reviews.models import Review


def service_list_view(request):
    """Grid of service cards with category filter, search, and location-based sorting/filtering."""
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
            Q(provider__location__icontains=search) |
            Q(category__icontains=search)
        )

    # Location search
    q_loc = request.GET.get('q_loc', '').strip()
    if q_loc:
        import re
        has_letters = bool(re.search(r'[a-zA-Z]', q_loc))
        has_digits = bool(re.search(r'\d', q_loc))
        if has_letters and has_digits:
            pincode_match = re.search(r'\d+', q_loc)
            if pincode_match:
                pincode = pincode_match.group(0)
                services = services.filter(provider__pincode__icontains=pincode)
            else:
                services = services.filter(
                    Q(provider__city__icontains=q_loc) |
                    Q(provider__pincode__icontains=q_loc) |
                    Q(provider__location__icontains=q_loc)
                )
        else:
            services = services.filter(
                Q(provider__city__icontains=q_loc) |
                Q(provider__pincode__icontains=q_loc) |
                Q(provider__location__icontains=q_loc)
            )

    try:
        user_lat = float(request.GET.get('lat'))
        user_lon = float(request.GET.get('lon'))
    except (ValueError, TypeError, KeyError):
        user_lat, user_lon = None, None

    # Calculate distance and add ratings
    services_list = []
    from providers.views import get_distance
    for service in services:
        p = service.provider
        if p.latitude is not None and p.longitude is not None and user_lat is not None and user_lon is not None:
            service.distance = get_distance(user_lat, user_lon, p.latitude, p.longitude)
        else:
            service.distance = None

        # Add average rating to each service
        avg = service.reviews.aggregate(avg_rating=Avg('rating'))['avg_rating']
        service.avg_rating = round(avg, 1) if avg else 0
        service.review_count = service.reviews.count()
        services_list.append(service)

    # Sort by distance if user coordinates are available
    if user_lat is not None and user_lon is not None:
        services_list.sort(key=lambda x: (x.distance is None, x.distance or 0))

    categories = Service.CATEGORY_CHOICES

    is_ajax = request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1'
    if is_ajax:
        return render(request, 'services/service_list_grid.html', {
            'services': services_list,
            'user_lat': user_lat,
            'user_lon': user_lon,
        })

    context = {
        'services': services_list,
        'categories': categories,
        'selected_category': category,
        'search_query': search,
        'q_loc_query': q_loc,
        'user_lat': user_lat,
        'user_lon': user_lon,
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
