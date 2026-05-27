from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from django.http import HttpResponse
from datetime import datetime, timedelta
import json
from io import BytesIO
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

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


# ===================== REPORT VIEWS =====================

@admin_required
def reports_dashboard(request):
    """Reports dashboard with options to view different report types."""
    context = {}
    return render(request, 'admin_panel/reports_dashboard.html', context)


@admin_required
def customer_service_report(request):
    """Generate customer service usage reports - Daily, Weekly, Monthly."""
    time_period = request.GET.get('period', 'daily')  # daily, weekly, monthly
    search_query = request.GET.get('q', '').strip()
    
    # Get date range
    today = timezone.now().date()
    if time_period == 'daily':
        date_from = today
        date_to = today
        title = f"Daily Customer Service Report - {today.strftime('%d %B %Y')}"
    elif time_period == 'weekly':
        # Last 7 days
        date_from = today - timedelta(days=6)
        date_to = today
        title = f"Weekly Customer Service Report - {date_from.strftime('%d %b')} to {date_to.strftime('%d %b %Y')}"
    else:  # monthly
        # Current month
        date_from = today.replace(day=1)
        if today.month == 12:
            date_to = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            date_to = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        title = f"Monthly Customer Service Report - {today.strftime('%B %Y')}"

    # Get completed bookings for customers in the period
    bookings = Booking.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to,
        status='completed'
    ).select_related('user', 'service', 'provider__user')

    if search_query:
        bookings = bookings.filter(
            Q(user__first_name__icontains=search_query)
            | Q(user__last_name__icontains=search_query)
            | Q(user__username__icontains=search_query)
            | Q(user__email__icontains=search_query)
            | Q(user__phone__icontains=search_query)
        )

    # Aggregate data by customer
    customer_services = {}
    top_services = {}

    for booking in bookings:
        customer_id = booking.user.id
        service_name = booking.service.service_name
        
        if customer_id not in customer_services:
            customer_services[customer_id] = {
                'name': booking.user.get_full_name() or booking.user.username,
                'email': booking.user.email,
                'phone': booking.user.phone or 'N/A',
                'total_services': 0,
                'total_spent': 0,
                'services_breakdown': {}
            }
        
        customer_services[customer_id]['total_services'] += 1
        customer_services[customer_id]['total_spent'] += float(booking.total_price)
        
        if service_name not in customer_services[customer_id]['services_breakdown']:
            customer_services[customer_id]['services_breakdown'][service_name] = 0
        customer_services[customer_id]['services_breakdown'][service_name] += 1
        
        # Track top services globally
        if service_name not in top_services:
            top_services[service_name] = 0
        top_services[service_name] += 1

    # Sort top services
    top_services_sorted = sorted(top_services.items(), key=lambda x: x[1], reverse=True)[:5]
    
    # Sort customers by total services
    customers_list = sorted(
        customer_services.values(), 
        key=lambda x: x['total_services'], 
        reverse=True
    )

    context = {
        'time_period': time_period,
        'title': title,
        'customer_services': customers_list,
        'top_services': top_services_sorted,
        'total_bookings': bookings.count(),
        'total_revenue': sum([b.total_price for b in bookings]),
        'date_from': date_from,
        'date_to': date_to,
        'search_query': search_query,
    }
    
    return render(request, 'admin_panel/customer_service_report.html', context)


@admin_required
def provider_service_report(request):
    """Generate provider service reports - Daily, Weekly, Monthly."""
    time_period = request.GET.get('period', 'daily')  # daily, weekly, monthly
    search_query = request.GET.get('q', '').strip()
    
    # Get date range
    today = timezone.now().date()
    if time_period == 'daily':
        date_from = today
        date_to = today
        title = f"Daily Provider Service Report - {today.strftime('%d %B %Y')}"
    elif time_period == 'weekly':
        date_from = today - timedelta(days=6)
        date_to = today
        title = f"Weekly Provider Service Report - {date_from.strftime('%d %b')} to {date_to.strftime('%d %b %Y')}"
    else:  # monthly
        date_from = today.replace(day=1)
        if today.month == 12:
            date_to = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            date_to = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        title = f"Monthly Provider Service Report - {today.strftime('%B %Y')}"

    # Get completed bookings by providers
    bookings = Booking.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to,
        status='completed'
    ).select_related('provider__user', 'service')

    if search_query:
        bookings = bookings.filter(
            Q(provider__user__first_name__icontains=search_query)
            | Q(provider__user__last_name__icontains=search_query)
            | Q(provider__user__username__icontains=search_query)
            | Q(provider__user__email__icontains=search_query)
            | Q(provider__user__phone__icontains=search_query)
        )

    # Aggregate data by provider
    provider_services = {}
    top_services = {}

    for booking in bookings:
        provider_id = booking.provider.id
        service_name = booking.service.service_name
        
        if provider_id not in provider_services:
            provider_services[provider_id] = {
                'name': booking.provider.user.get_full_name() or booking.provider.user.username,
                'email': booking.provider.user.email,
                'phone': booking.provider.user.phone or 'N/A',
                'total_services_provided': 0,
                'total_earnings': 0,
                'services_breakdown': {}
            }
        
        provider_services[provider_id]['total_services_provided'] += 1
        provider_services[provider_id]['total_earnings'] += float(booking.total_price)
        
        if service_name not in provider_services[provider_id]['services_breakdown']:
            provider_services[provider_id]['services_breakdown'][service_name] = 0
        provider_services[provider_id]['services_breakdown'][service_name] += 1
        
        # Track most provided services
        if service_name not in top_services:
            top_services[service_name] = 0
        top_services[service_name] += 1

    top_services_sorted = sorted(top_services.items(), key=lambda x: x[1], reverse=True)[:5]
    
    providers_list = sorted(
        provider_services.values(), 
        key=lambda x: x['total_services_provided'], 
        reverse=True
    )

    context = {
        'time_period': time_period,
        'title': title,
        'provider_services': providers_list,
        'top_services': top_services_sorted,
        'total_bookings': bookings.count(),
        'total_platform_earnings': sum([b.total_price for b in bookings]),
        'date_from': date_from,
        'date_to': date_to,
        'search_query': search_query,
    }
    
    return render(request, 'admin_panel/provider_service_report.html', context)


@admin_required
def generate_customer_pdf_report(request):
    """Generate PDF report for customer services."""
    time_period = request.GET.get('period', 'daily')
    search_query = request.GET.get('q', '').strip()
    
    today = timezone.now().date()
    if time_period == 'daily':
        date_from = today
        date_to = today
        title = f"Daily Customer Service Report - {today.strftime('%d %B %Y')}"
    elif time_period == 'weekly':
        date_from = today - timedelta(days=6)
        date_to = today
        title = f"Weekly Customer Service Report - {date_from.strftime('%d %b')} to {date_to.strftime('%d %b %Y')}"
    else:
        date_from = today.replace(day=1)
        if today.month == 12:
            date_to = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            date_to = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        title = f"Monthly Customer Service Report - {today.strftime('%B %Y')}"

    bookings = Booking.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to,
        status='completed'
    ).select_related('user', 'service')

    if search_query:
        bookings = bookings.filter(
            Q(user__first_name__icontains=search_query)
            | Q(user__last_name__icontains=search_query)
            | Q(user__username__icontains=search_query)
            | Q(user__email__icontains=search_query)
            | Q(user__phone__icontains=search_query)
        )

    customer_services = {}
    top_services = {}

    for booking in bookings:
        customer_id = booking.user.id
        service_name = booking.service.service_name
        
        if customer_id not in customer_services:
            customer_services[customer_id] = {
                'name': booking.user.get_full_name() or booking.user.username,
                'email': booking.user.email,
                'total_services': 0,
                'total_spent': 0,
                'services': []
            }
        
        customer_services[customer_id]['total_services'] += 1
        customer_services[customer_id]['total_spent'] += float(booking.total_price)
        customer_services[customer_id]['services'].append(service_name)
        
        if service_name not in top_services:
            top_services[service_name] = 0
        top_services[service_name] += 1

    top_services_sorted = sorted(top_services.items(), key=lambda x: x[1], reverse=True)[:5]
    customers_list = sorted(customer_services.values(), key=lambda x: x['total_services'], reverse=True)
    total_revenue = sum([b['total_spent'] for b in customers_list])

    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1e3a8a'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 0.3*inch))

    # Summary section
    summary_data = [
        ['Metric', 'Value'],
        ['Total Completed Bookings', str(len(bookings))],
        ['Total Revenue', f"₹{total_revenue:,.2f}"],
        ['Period', f"{date_from.strftime('%d %b %Y')} to {date_to.strftime('%d %b %Y')}"],
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 0.3*inch))

    # Top Services
    elements.append(Paragraph("Top 5 Most Used Services", styles['Heading2']))
    elements.append(Spacer(1, 0.1*inch))
    
    top_services_data = [['Service Name', 'Count']]
    for service, count in top_services_sorted:
        top_services_data.append([service, str(count)])
    
    if len(top_services_data) == 1:
        top_services_data.append(['No services', '0'])
    
    top_table = Table(top_services_data, colWidths=[3.5*inch, 1.5*inch])
    top_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
    ]))
    
    elements.append(top_table)
    elements.append(Spacer(1, 0.3*inch))

    # Customer Details
    elements.append(Paragraph("Customer Service Usage Details", styles['Heading2']))
    elements.append(Spacer(1, 0.1*inch))

    customer_data = [['Customer', 'Email', 'Total Services', 'Total Spent']]
    for customer in customers_list[:20]:  # Limit to 20 per page
        customer_data.append([
            customer['name'][:30],
            customer['email'][:30],
            str(customer['total_services']),
            f"₹{customer['total_spent']:,.2f}"
        ])

    cust_table = Table(customer_data, colWidths=[1.8*inch, 1.8*inch, 1.2*inch, 1.2*inch])
    cust_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#f59e0b')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fafafa')]),
    ]))
    
    elements.append(cust_table)
    elements.append(Spacer(1, 0.2*inch))

    # Footer
    footer_text = f"Generated on {timezone.now().strftime('%d %B %Y at %H:%M:%S')}"
    elements.append(Paragraph(f"<i>{footer_text}</i>", styles['Normal']))

    doc.build(elements)
    buffer.seek(0)

    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="customer_service_report_{time_period}.pdf"'
    return response


@admin_required
def generate_provider_pdf_report(request):
    """Generate PDF report for provider services."""
    time_period = request.GET.get('period', 'daily')
    search_query = request.GET.get('q', '').strip()
    
    today = timezone.now().date()
    if time_period == 'daily':
        date_from = today
        date_to = today
        title = f"Daily Provider Service Report - {today.strftime('%d %B %Y')}"
    elif time_period == 'weekly':
        date_from = today - timedelta(days=6)
        date_to = today
        title = f"Weekly Provider Service Report - {date_from.strftime('%d %b')} to {date_to.strftime('%d %b %Y')}"
    else:
        date_from = today.replace(day=1)
        if today.month == 12:
            date_to = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
        else:
            date_to = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
        title = f"Monthly Provider Service Report - {today.strftime('%B %Y')}"

    bookings = Booking.objects.filter(
        created_at__date__gte=date_from,
        created_at__date__lte=date_to,
        status='completed'
    ).select_related('provider__user', 'service')

    if search_query:
        bookings = bookings.filter(
            Q(provider__user__first_name__icontains=search_query)
            | Q(provider__user__last_name__icontains=search_query)
            | Q(provider__user__username__icontains=search_query)
            | Q(provider__user__email__icontains=search_query)
            | Q(provider__user__phone__icontains=search_query)
        )

    provider_services = {}
    top_services = {}

    for booking in bookings:
        provider_id = booking.provider.id
        service_name = booking.service.service_name
        
        if provider_id not in provider_services:
            provider_services[provider_id] = {
                'name': booking.provider.user.get_full_name() or booking.provider.user.username,
                'email': booking.provider.user.email,
                'total_services': 0,
                'total_earnings': 0,
                'services': []
            }
        
        provider_services[provider_id]['total_services'] += 1
        provider_services[provider_id]['total_earnings'] += float(booking.total_price)
        provider_services[provider_id]['services'].append(service_name)
        
        if service_name not in top_services:
            top_services[service_name] = 0
        top_services[service_name] += 1

    top_services_sorted = sorted(top_services.items(), key=lambda x: x[1], reverse=True)[:5]
    providers_list = sorted(provider_services.values(), key=lambda x: x['total_services'], reverse=True)
    total_platform_earnings = sum([p['total_earnings'] for p in providers_list])

    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor('#1e3a8a'),
        spaceAfter=12,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    elements.append(Paragraph(title, title_style))
    elements.append(Spacer(1, 0.3*inch))

    # Summary section
    summary_data = [
        ['Metric', 'Value'],
        ['Total Completed Bookings', str(len(bookings))],
        ['Total Platform Earnings', f"₹{total_platform_earnings:,.2f}"],
        ['Period', f"{date_from.strftime('%d %b %Y')} to {date_to.strftime('%d %b %Y')}"],
    ]
    
    summary_table = Table(summary_data, colWidths=[3*inch, 2*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e3a8a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
    ]))
    
    elements.append(summary_table)
    elements.append(Spacer(1, 0.3*inch))

    # Top Services Provided
    elements.append(Paragraph("Top 5 Most Provided Services", styles['Heading2']))
    elements.append(Spacer(1, 0.1*inch))
    
    top_services_data = [['Service Name', 'Count']]
    for service, count in top_services_sorted:
        top_services_data.append([service, str(count)])
    
    if len(top_services_data) == 1:
        top_services_data.append(['No services', '0'])
    
    top_table = Table(top_services_data, colWidths=[3.5*inch, 1.5*inch])
    top_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#10b981')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f0f0f0')]),
    ]))
    
    elements.append(top_table)
    elements.append(Spacer(1, 0.3*inch))

    # Provider Details
    elements.append(Paragraph("Provider Service Delivery Details", styles['Heading2']))
    elements.append(Spacer(1, 0.1*inch))

    provider_data = [['Provider', 'Email', 'Total Services', 'Total Earnings']]
    for provider in providers_list[:20]:
        provider_data.append([
            provider['name'][:30],
            provider['email'][:30],
            str(provider['total_services']),
            f"₹{provider['total_earnings']:,.2f}"
        ])

    prov_table = Table(provider_data, colWidths=[1.8*inch, 1.8*inch, 1.2*inch, 1.2*inch])
    prov_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8b5cf6')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('ALIGN', (2, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#fafafa')]),
    ]))
    
    elements.append(prov_table)
    elements.append(Spacer(1, 0.2*inch))

    # Footer
    footer_text = f"Generated on {timezone.now().strftime('%d %B %Y at %H:%M:%S')}"
    elements.append(Paragraph(f"<i>{footer_text}</i>", styles['Normal']))

    doc.build(elements)
    buffer.seek(0)

    response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="provider_service_report_{time_period}.pdf"'
    return response
