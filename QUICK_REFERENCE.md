# Admin Reports System - Quick Reference

## 📋 Installation Checklist

```bash
# 1. Install reportlab library
pip install reportlab==4.0.9

# 2. Verify installation
pip list | grep reportlab
# Output: reportlab 4.0.9

# 3. Django system check
python manage.py check
# Output: System check identified no issues (0 silenced).

# 4. Start development server
python manage.py runserver
# Navigate to: http://localhost:8000/admin/reports/
```

## 🔗 Quick URL Reference

| Feature | URL | Method |
|---------|-----|--------|
| Reports Hub | `/admin/reports/` | GET |
| Customer Daily | `/admin/reports/customer-services/?period=daily` | GET |
| Customer Weekly | `/admin/reports/customer-services/?period=weekly` | GET |
| Customer Monthly | `/admin/reports/customer-services/?period=monthly` | GET |
| Provider Daily | `/admin/reports/provider-services/?period=daily` | GET |
| Provider Weekly | `/admin/reports/provider-services/?period=weekly` | GET |
| Provider Monthly | `/admin/reports/provider-services/?period=monthly` | GET |
| Download Customer PDF | `/admin/reports/customer-pdf/?period=[period]` | GET |
| Download Provider PDF | `/admin/reports/provider-pdf/?period=[period]` | GET |

## 🎯 View Functions Quick Reference

```python
# Location: admin_panel/views.py

# 1. Reports Dashboard
@admin_required
def reports_dashboard(request):
    # Shows report selection interface
    # URL: /admin/reports/

# 2. Customer Service Report
@admin_required
def customer_service_report(request):
    # Shows customer analytics HTML
    # Parameters: ?period=daily|weekly|monthly
    # URL: /admin/reports/customer-services/

# 3. Provider Service Report
@admin_required
def provider_service_report(request):
    # Shows provider analytics HTML
    # Parameters: ?period=daily|weekly|monthly
    # URL: /admin/reports/provider-services/

# 4. Generate Customer PDF
@admin_required
def generate_customer_pdf_report(request):
    # Returns PDF file
    # Parameters: ?period=daily|weekly|monthly
    # URL: /admin/reports/customer-pdf/

# 5. Generate Provider PDF
@admin_required
def generate_provider_pdf_report(request):
    # Returns PDF file
    # Parameters: ?period=daily|weekly|monthly
    # URL: /admin/reports/provider-pdf/
```

## 🗂️ File Structure

```
Hyperlocal_Service_Provider/
├── admin_panel/
│   ├── views.py                    (Modified - Added 5 functions)
│   ├── urls.py                     (Modified - Added 5 routes)
│   ├── templatetags/               (New)
│   │   ├── __init__.py             (New)
│   │   └── custom_filters.py       (New)
│   └── migrations/
│
├── templates/
│   ├── base.html                   (Modified - Added Reports link)
│   └── admin_panel/
│       ├── reports_dashboard.html        (New)
│       ├── customer_service_report.html  (New)
│       └── provider_service_report.html  (New)
│
├── requirements.txt                (Modified - Added reportlab)
│
├── manage.py
├── REPORTS_DOCUMENTATION.md        (New - Technical docs)
├── SETUP_SUMMARY.md                (New - Setup guide)
├── USER_GUIDE_REPORTS.md           (New - User guide)
└── SYSTEM_ARCHITECTURE.md          (New - Architecture diagrams)
```

## 🔍 Database Queries Used

```python
# Get completed bookings in date range
Booking.objects.filter(
    created_at__date__gte=date_from,
    created_at__date__lte=date_to,
    status='completed'
).select_related('user', 'service', 'provider__user')

# Group by customer
customer_services = {}
for booking in bookings:
    customer_id = booking.user.id
    # Aggregate totals and services
    
# Group by provider  
provider_services = {}
for booking in bookings:
    provider_id = booking.provider.id
    # Aggregate totals and services

# Find top services
top_services = {}
for booking in bookings:
    service_name = booking.service.service_name
    # Count occurrences
    
# Sort results
sorted_customers = sorted(customer_services.values(), 
                         key=lambda x: x['total_services'], 
                         reverse=True)
```

## 🎨 Template Tags Usage

```django
{# In HTML templates #}

{# Divide filter for averages #}
{{ total_spent|divide:total_services }}
{# Example: 1000|divide:5 = 200 #}

{# Multiply filter for percentages #}
{{ count|multiply:100|divide:total_bookings }}
{# Example: 5|multiply:100|divide:10 = 50 #}

{# Load in template #}
{% load custom_filters %}
```

## 📊 Report Data Calculation Examples

### Customer Report Example
```
Customer: John Doe
Bookings: [
    { service: 'Plumbing', price: 500 },
    { service: 'Cleaning', price: 300 },
    { service: 'Plumbing', price: 500 },
]

Total Services: 3
Total Spent: 1300
Avg per Service: 1300 ÷ 3 = 433.33

Services Breakdown:
- Plumbing: 2
- Cleaning: 1
```

### Provider Report Example
```
Provider: ABC Services
Bookings: [
    { service: 'Plumbing', price: 500 },
    { service: 'Plumbing', price: 500 },
    { service: 'Electrical', price: 400 },
]

Total Services: 3
Total Earnings: 1400
Avg per Service: 1400 ÷ 3 = 466.67

Services Breakdown:
- Plumbing: 2
- Electrical: 1
```

## 🔐 Access Control

```python
# Admin-only decorator in views.py
def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'admin':
            messages.warning(request, 'Admin access required.')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper

# Applied to all report views
@admin_required
def reports_dashboard(request):
    ...
```

## 🐛 Debugging Commands

```bash
# Check Django configuration
python manage.py check

# Verify reportlab installation
python -c "import reportlab; print(reportlab.__version__)"
# Output: Should show version number (e.g., 4.0.9)

# Test database connectivity
python manage.py shell
>>> from bookings.models import Booking
>>> Booking.objects.filter(status='completed').count()
# Should return number of completed bookings

# Check admin users
python manage.py shell
>>> from users.models import UserProfile
>>> UserProfile.objects.filter(role='admin').count()
# Should return number of admin users

# Run specific tests (if you have them)
python manage.py test admin_panel
```

## 📝 Common Code Snippets

### Getting Date Range
```python
from datetime import timedelta
from django.utils import timezone

today = timezone.now().date()

# Daily
date_from = today
date_to = today

# Weekly (last 7 days)
date_from = today - timedelta(days=6)
date_to = today

# Monthly
date_from = today.replace(day=1)
if today.month == 12:
    date_to = today.replace(year=today.year + 1, month=1, day=1) - timedelta(days=1)
else:
    date_to = today.replace(month=today.month + 1, day=1) - timedelta(days=1)
```

### Creating PDF Response
```python
from django.http import HttpResponse
from io import BytesIO

buffer = BytesIO()
# ... generate PDF ...
buffer.seek(0)

response = HttpResponse(buffer.getvalue(), content_type='application/pdf')
response['Content-Disposition'] = f'attachment; filename="report.pdf"'
return response
```

### Querying Completed Bookings
```python
from bookings.models import Booking
from django.utils import timezone

bookings = Booking.objects.filter(
    status='completed',
    created_at__date__gte=date_from,
    created_at__date__lte=date_to
).select_related('user', 'service', 'provider__user')

# Count
total = bookings.count()

# Sum revenue
revenue = sum([b.total_price for b in bookings])

# Group by customer
from itertools import groupby
by_customer = groupby(bookings, key=lambda b: b.user.id)
```

## 🔗 Navigation Paths

### Admin Dashboard → Reports
1. Login as admin
2. Top navbar has link: "Reports"
3. Click to go to `/admin/reports/`

### Main Dashboard → Reports
- URL: `http://localhost:8000/admin/reports/`

### Reports Hub → Report Pages
- Customer → `/admin/reports/customer-services/?period=daily`
- Provider → `/admin/reports/provider-services/?period=daily`

## ⚙️ Configuration Options

### Change Time Zones
In `settings.py`:
```python
TIME_ZONE = 'Asia/Kolkata'  # Or your timezone
USE_TZ = True
```

### Change PDF Page Size
In `views.py` PDF functions:
```python
from reportlab.lib.pagesizes import letter, A4
doc = SimpleDocTemplate(buffer, pagesize=A4)  # Change to letter if needed
```

### Change PDF Colors
In `views.py` PDF functions:
```python
from reportlab.lib import colors
colors.HexColor('#1e3a8a')  # Blue
colors.HexColor('#f5576c')  # Red/Pink
colors.HexColor('#10b981')  # Green
```

## 📞 Support Contacts

| Issue | Solution |
|-------|----------|
| Reports not showing | Check if completed bookings exist |
| PDF won't download | Try different browser, clear cache |
| Can't access reports | Login as admin user |
| Import errors | Run `python manage.py check` |
| reportlab errors | Reinstall: `pip install --force-reinstall reportlab` |

## ✅ Testing Checklist

- [ ] reportlab installed successfully
- [ ] Django check passes
- [ ] Navigation link visible for admin
- [ ] Can access `/admin/reports/`
- [ ] Customer report loads for daily period
- [ ] Provider report loads for weekly period
- [ ] PDF downloads for monthly reports
- [ ] Non-admin users cannot access reports
- [ ] Numbers calculate correctly
- [ ] Tables display properly on mobile

## 🚀 Quick Start Commands

```bash
# Complete setup
cd "C:\Users\admin\OneDrive\Desktop\finalGitProject\Hyperlocal_Service_Provider"
pip install reportlab==4.0.9
python manage.py check
python manage.py runserver

# Access in browser
# http://localhost:8000/admin/reports/
```

## 📚 Documentation Files

1. **REPORTS_DOCUMENTATION.md** - Technical documentation
2. **SETUP_SUMMARY.md** - Implementation guide
3. **USER_GUIDE_REPORTS.md** - End-user guide
4. **SYSTEM_ARCHITECTURE.md** - Architecture diagrams
5. **QUICK_REFERENCE.md** - This file

---

**Quick Reference Complete!**
Use this file for fast lookup of commands, URLs, and code snippets.
