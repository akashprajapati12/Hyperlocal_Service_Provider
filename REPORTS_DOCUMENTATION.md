# Admin Reports System Documentation

## Overview
The Admin Reports System provides comprehensive analytics and insights about customer and provider service usage on a daily, weekly, and monthly basis. This system is exclusively available to admin users and includes features for viewing detailed reports and downloading them as PDF files.

## Features

### 1. **Customer Service Report**
Provides insights into customer service consumption patterns.

**Metrics Included:**
- Total completed bookings
- Total revenue generated
- Number of active customers
- Average revenue per booking
- Top 5 most used services by customers
- Detailed customer-wise breakdown including:
  - Customer name and email
  - Phone number
  - Total services taken
  - Total amount spent
  - Average cost per service
  - Breakdown of services used

**Time Periods:**
- **Daily:** Report for the current date
- **Weekly:** Report for the last 7 days
- **Monthly:** Report for the entire current month

### 2. **Provider Service Report**
Provides insights into provider service delivery patterns.

**Metrics Included:**
- Total completed bookings
- Total platform earnings
- Number of active providers
- Average earnings per booking
- Top 5 most provided services
- Detailed provider-wise breakdown including:
  - Provider name and email
  - Phone number
  - Total services provided
  - Total earnings from services
  - Average earnings per service
  - Breakdown of services provided

**Time Periods:**
- **Daily:** Report for the current date
- **Weekly:** Report for the last 7 days
- **Monthly:** Report for the entire current month

### 3. **PDF Download Functionality**
Each report can be downloaded as a professionally formatted PDF document containing:
- Report title with date range
- Summary statistics
- Top services section
- Detailed customer/provider information tables
- Generation timestamp
- Professional formatting with color-coded sections

## Access and Navigation

### Navigation Path
1. Login as admin user
2. In the navigation bar, click on **"Reports"**
3. You'll be taken to the Reports Dashboard

### Reports Dashboard
The Reports Dashboard provides quick access to:
- **Customer Service Report** with Daily, Weekly, and Monthly options
- **Provider Service Report** with Daily, Weekly, and Monthly options
- Information about what each report contains

### Direct Report Access
From any report page:
- Use the **Period Selector** buttons to switch between Daily, Weekly, and Monthly views
- Use the **Download PDF** button to export the current report

## URL Structure

### Report URLs
- `/admin/reports/` - Reports Dashboard
- `/admin/reports/customer-services/?period=daily|weekly|monthly` - Customer Service Report
- `/admin/reports/provider-services/?period=daily|weekly|monthly` - Provider Service Report
- `/admin/reports/customer-pdf/?period=daily|weekly|monthly` - Download Customer PDF
- `/admin/reports/provider-pdf/?period=daily|weekly|monthly` - Download Provider PDF

## Security
- All reports are protected by the `@admin_required` decorator
- Only users with `role='admin'` can access reports
- Non-admin users attempting to access reports are redirected to login
- The Reports link only appears in the navbar for admin users

## Report Data Source
Reports use completed bookings as the source of truth:
- Only bookings with `status='completed'` are included
- Data is calculated in real-time based on the selected period
- All earnings and revenue calculations are based on `booking.total_price`

## Customization Options

### Modifying Report Periods
Edit the time period logic in `admin_panel/views.py`:
- `customer_service_report()` function (around line 242)
- `provider_service_report()` function (around line 295)

### Adding New Metrics
1. Modify the aggregation logic in the report view
2. Update the context dictionary with new data
3. Display in the template using template tags

### Changing PDF Styling
Edit the PDF generation functions:
- `generate_customer_pdf_report()` - Line 350
- `generate_provider_pdf_report()` - Line 460
- Modify colors, fonts, and table styling as needed

## Template Filters
Custom template filters are available in `admin_panel/templatetags/custom_filters.py`:
- `divide` - Divide one value by another
- `multiply` - Multiply values
- Usage: `{{ value|divide:divisor }}` or `{{ value|multiply:factor }}`

## File Structure
```
admin_panel/
├── views.py                          (Report views)
├── urls.py                           (Report URL routes)
├── templatetags/
│   ├── __init__.py
│   └── custom_filters.py            (Template filters)
└── templates/admin_panel/
    ├── reports_dashboard.html        (Reports main page)
    ├── customer_service_report.html  (Customer report page)
    └── provider_service_report.html  (Provider report page)
```

## Technical Details

### View Functions
1. `reports_dashboard()` - Shows report selection page
2. `customer_service_report()` - Displays customer service analytics
3. `provider_service_report()` - Displays provider service analytics
4. `generate_customer_pdf_report()` - Generates PDF for customer report
5. `generate_provider_pdf_report()` - Generates PDF for provider report

### Dependencies
- `reportlab` - PDF generation library
- `django.db.models` - Database aggregation
- `django.utils.timezone` - Date/time utilities

### Database Queries
Reports use efficient database queries with:
- `.select_related()` for foreign key optimization
- `.annotate()` and `.aggregate()` for calculations
- `.values()` for grouping data

## Performance Considerations
- Reports aggregate data at query time (not cached)
- Large datasets may take time to render
- Consider adding pagination for very large customer/provider bases
- PDF generation is performed synchronously

## Future Enhancements
Possible improvements:
1. Add caching for frequently accessed reports
2. Implement scheduled report generation via Celery
3. Add email delivery of reports
4. Create custom date range selectors
5. Add comparison between periods
6. Implement data export to Excel/CSV
7. Add graphical charts to HTML reports
8. Create performance optimization for large datasets

## Troubleshooting

### Reports show no data
- Verify completed bookings exist for the selected period
- Check booking `status` field is set to 'completed'
- Ensure `created_at` dates are correct

### PDF download fails
- Verify reportlab is installed: `pip install reportlab`
- Check file permissions
- Verify temporary storage location has write access

### Navigation link not showing
- Verify user is logged in as admin (role='admin')
- Clear browser cache
- Verify `reports_dashboard` URL is properly registered in `urls.py`

## Support
For issues or questions about the reports system, contact the development team.
