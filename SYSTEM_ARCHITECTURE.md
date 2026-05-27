# Admin Reports System Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         ADMIN USER                               │
│                  (role = 'admin' required)                       │
└────────────────────────────┬────────────────────────────────────┘
                             │
                    LOGIN CHECK & AUTH
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    ADMIN INTERFACE                               │
│                    (/admin/reports/)                             │
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │           Reports Dashboard                              │   │
│  │  ┌─────────────────────────────────────────────────────┐ │   │
│  │  │ Customer Service Report    │ Provider Service Report │ │   │
│  │  │ ├─ Daily    ├─ Weekly    │ ├─ Daily    ├─ Weekly │ │   │
│  │  │ └─ Monthly  │            │ └─ Monthly  │        │ │   │
│  │  └─────────────────────────────────────────────────────┘ │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────┬──────────────────────────────┬──────────────────────────┘
         │                              │
         ▼                              ▼
    CUSTOMER REPORT              PROVIDER REPORT
    /customer-services/          /provider-services/
         │                              │
         ├─ Period Selection ────────────┤
         │  (Daily/Weekly/Monthly)       │
         │                              │
         ▼                              ▼
    Customer Analytics              Provider Analytics
    View (HTML Page)                View (HTML Page)
         │                              │
         ├─ View Online ────────────────┤
         │                              │
         └─ Download PDF ──────────┬────┘
                                   │
         ┌─────────────────────────┴──────────────────┐
         │                                             │
         ▼                                             ▼
    generate_customer_          generate_provider_
    pdf_report()                pdf_report()
         │                              │
         ├─ Fetch Data ─────────────────┤
         │ (from Django ORM)            │
         │                              │
         ├─ Aggregate ──────────────────┤
         │ (Sum, Count, Group By)       │
         │                              │
         ├─ Format PDF ─────────────────┤
         │ (using reportlab)            │
         │                              │
         └─ Download ───────────────────┘
                │
                ▼
         PDF File (↓)
    customer_service_report_daily.pdf
    provider_service_report_monthly.pdf
```

## Data Flow Diagram

```
┌──────────────────────┐
│   Booking Model      │
│  ┌────────────────┐  │
│  │ id             │  │
│  │ user (FK)      │  │
│  │ provider (FK)  │  │
│  │ service (FK)   │  │
│  │ status ────────┼──┼─── Only "completed" bookings
│  │ created_at     │  │
│  │ total_price    │  │
│  └────────────────┘  │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────────────────────────────────────┐
│          Report View (views.py)                      │
│  ┌──────────────────────────────────────────────┐   │
│  │ 1. Filter by Status & Date Range             │   │
│  │    bookings = Booking.objects.filter(        │   │
│  │        status='completed',                   │   │
│  │        created_at__date__gte=date_from,      │   │
│  │        created_at__date__lte=date_to         │   │
│  │    )                                         │   │
│  └────────┬─────────────────────────────────────┘   │
│           │                                         │
│  ┌────────▼─────────────────────────────────────┐   │
│  │ 2. Aggregate & Count Data                    │   │
│  │    - Group by customer/provider              │   │
│  │    - Sum total_price for revenue/earnings    │   │
│  │    - Count bookings per customer/provider    │   │
│  │    - Find top services                       │   │
│  └────────┬─────────────────────────────────────┘   │
│           │                                         │
│  ┌────────▼─────────────────────────────────────┐   │
│  │ 3. Create Context Dictionary                 │   │
│  │    - customer_services or provider_services  │   │
│  │    - top_services                            │   │
│  │    - total_bookings, total_revenue           │   │
│  │    - date_from, date_to                      │   │
│  └────────┬─────────────────────────────────────┘   │
└─────────┬┘                                          
          │
          ▼
┌──────────────────────────────────────────────────────┐
│        Template Layer (HTML Templates)               │
│  ┌──────────────────────────────────────────────┐   │
│  │ Display Tables & Stats                       │   │
│  │ - Summary Statistics Cards                   │   │
│  │ - Top Services Table                         │   │
│  │ - Customer/Provider Details Table            │   │
│  │ - Service Breakdown per Customer/Provider    │   │
│  └──────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┘
```

## PDF Generation Pipeline

```
┌─────────────────────────────┐
│  PDF Generation Request     │
│  /reports/customer-pdf/     │
│  ?period=daily              │
└────────────────┬────────────┘
                 │
                 ▼
        ┌────────────────────┐
        │ Extract Parameters │
        │ - time_period      │
        │ - date_from        │
        │ - date_to          │
        └────────┬───────────┘
                 │
                 ▼
        ┌────────────────────────────────┐
        │ Query Bookings from Database   │
        │ - Filter by status='completed' │
        │ - Filter by date range         │
        │ - Select related objects       │
        └────────┬───────────────────────┘
                 │
                 ▼
        ┌────────────────────────────────┐
        │ Aggregate Data                 │
        │ - Calculate totals             │
        │ - Group by customer/provider   │
        │ - Find top services            │
        └────────┬───────────────────────┘
                 │
                 ▼
        ┌────────────────────────────────┐
        │ Create ReportLab Document      │
        │ - SimpleDocTemplate (A4)       │
        │ - BytesIO Buffer               │
        └────────┬───────────────────────┘
                 │
                 ▼
        ┌────────────────────────────────┐
        │ Build PDF Sections             │
        │ - Title & Styling              │
        │ - Summary Table                │
        │ - Top Services Table           │
        │ - Customer/Provider Table      │
        │ - Footer with timestamp        │
        └────────┬───────────────────────┘
                 │
                 ▼
        ┌────────────────────────────────┐
        │ Return HTTP Response           │
        │ - Content-Type: application/pdf│
        │ - Content-Disposition: attach  │
        │ - Filename: report_[period].pdf│
        └────────┬───────────────────────┘
                 │
                 ▼
        ┌────────────────────────────┐
        │ File Downloaded to User    │
        │ "customer_service_report_  │
        │  daily.pdf"                │
        └────────────────────────────┘
```

## URL Routing Architecture

```
admin_panel/urls.py
│
├─ path('', views.admin_dashboard)
│  └─ Route: /admin/
│
├─ path('users/', views.manage_users_view)
│  └─ Route: /admin/users/
│
├─ path('providers/', views.manage_providers_view)
│  └─ Route: /admin/providers/
│
├─ path('bookings/', views.manage_bookings_view)
│  └─ Route: /admin/bookings/
│
├─ path('reports/', views.reports_dashboard)
│  └─ Route: /admin/reports/  ◄─── NEW
│
├─ path('reports/customer-services/', views.customer_service_report)
│  └─ Route: /admin/reports/customer-services/?period=[daily|weekly|monthly]  ◄─── NEW
│
├─ path('reports/provider-services/', views.provider_service_report)
│  └─ Route: /admin/reports/provider-services/?period=[daily|weekly|monthly]  ◄─── NEW
│
├─ path('reports/customer-pdf/', views.generate_customer_pdf_report)
│  └─ Route: /admin/reports/customer-pdf/?period=[daily|weekly|monthly]  ◄─── NEW
│
└─ path('reports/provider-pdf/', views.generate_provider_pdf_report)
   └─ Route: /admin/reports/provider-pdf/?period=[daily|weekly|monthly]  ◄─── NEW
```

## Authentication Flow

```
User Access Request
       │
       ▼
   Is User Logged In?
   ├─ NO  ──► Redirect to /login/
   │
   └─ YES ─► Check User Role
             │
             ├─ role != 'admin'  ──► Warning Message
             │                       Redirect to /login/
             │
             └─ role == 'admin'  ──► Grant Access
                                     Render Report View
```

## Database Query Optimization

```
Report Generation Query Pattern:

┌─ Initial Query ─┐
│ Booking.objects │
│ .filter(        │ ◄─── Filter Conditions
│   status='comp',│      • status='completed'
│   created_at__  │      • Date range filtering
│   date__gte=... │
│ )               │
└────────┬────────┘
         │
         ▼
┌─ Select Related ─┐
│ .select_related(│ ◄─── Reduce Queries
│   'user',       │      • Fetch foreign key objects
│   'service',    │      • Prevent N+1 queries
│   'provider'    │
│ )               │
└────────┬────────┘
         │
         ▼
┌─ Python Processing ─┐
│ Loop through        │ ◄─── Aggregate in Memory
│ bookings and        │      • Group by customer/provider
│ aggregate data      │      • Calculate totals
│ into dictionaries   │      • Build top services list
└────────┬────────────┘
         │
         ▼
   Final Report Data
   (Ready for Template/PDF)
```

## Template Filter Architecture

```
custom_filters.py
│
├─ @register.filter
│  def divide(value, arg)
│  │  return float(value) / float(arg)
│  │  Usage in template: {{ amount|divide:count }}
│  │  Example: {{ 1000|divide:5 }} → 200
│  │
│  └─ Used for: Average calculations
│
└─ @register.filter
   def multiply(value, arg)
      return float(value) * float(arg)
      Usage in template: {{ percentage|multiply:100 }}
      Example: {{ 0.5|multiply:100 }} → 50
      
      └─ Used for: Percentage calculations
```

## Security Architecture

```
Access Control Layer
│
├─ Authentication Check
│  └─ request.user.is_authenticated
│
├─ Authorization Check  
│  └─ request.user.role == 'admin'
│
└─ @admin_required Decorator
   (Applied to all report views)
   
   If Auth Fails:
   ├─ messages.warning("Admin access required.")
   └─ redirect('login')
```

## Report Data Model

```
Customer Service Report Data:
{
    customer_id: {
        'name': str,
        'email': str,
        'phone': str,
        'total_services': int,
        'total_spent': float,
        'services_breakdown': {
            service_name: int,
            ...
        }
    },
    ...
}

Provider Service Report Data:
{
    provider_id: {
        'name': str,
        'email': str,
        'phone': str,
        'total_services_provided': int,
        'total_earnings': float,
        'services_breakdown': {
            service_name: int,
            ...
        }
    },
    ...
}

Top Services:
[
    (service_name, count),
    ...
]
```

## Time Period Calculation

```
If time_period == 'daily':
    date_from = today
    date_to = today
    Example: 25 May 2026

If time_period == 'weekly':
    date_from = today - 6 days
    date_to = today
    Example: 19 May 2026 - 25 May 2026

If time_period == 'monthly':
    date_from = 1st of current month
    date_to = last day of current month
    Example: 01 May 2026 - 31 May 2026
```

---

**System Diagram Complete!**
