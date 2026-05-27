# Admin Reports System - User Guide

## 🎯 Overview
The Admin Reports System provides analytics dashboards showing:
- **Customer Service Usage**: How many services customers took
- **Provider Service Delivery**: How many services providers delivered
- **Time-based Analysis**: Daily, Weekly, Monthly breakdowns
- **PDF Export**: Download reports for record keeping

---

## 📊 Report Types

### 1️⃣ Customer Service Report
**What it shows:**
- How many services each customer booked
- What are the most popular services among customers
- Customer spending patterns
- Top customers by service count

**Available for:** Daily | Weekly | Monthly

**Metrics:**
- Total Bookings
- Total Revenue
- Active Customers
- Average Revenue per Booking

---

### 2️⃣ Provider Service Report
**What it shows:**
- How many services each provider delivered
- What services are most commonly provided
- Provider earning patterns
- Top providers by services delivered

**Available for:** Daily | Weekly | Monthly

**Metrics:**
- Total Bookings
- Platform Earnings
- Active Providers
- Average Earnings per Booking

---

## 🚀 How to Access Reports

### Step 1: Login as Admin
- Go to your HyperLocal platform
- Login with admin credentials

### Step 2: Navigate to Reports
- Look for **"Reports"** in the main navigation bar
- Or go directly to `/admin/reports/`

### Step 3: Choose Report Type
- Click on **"Customer Service Report"** OR
- Click on **"Provider Service Report"**

### Step 4: Select Time Period
- Click **Daily**, **Weekly**, or **Monthly**
- Reports update instantly

### Step 5: Download PDF (Optional)
- Click **"Download PDF"** button
- File saves to your Downloads folder

---

## 📈 What Each Report Contains

### Customer Service Report Breakdown:

```
Report Title & Date Range
├── Summary Statistics
│   ├── Total Bookings
│   ├── Total Revenue  
│   ├── Active Customers
│   └── Average Revenue/Booking
├── Top 5 Services Used
│   ├── Service Name
│   ├── Usage Count
│   └── Percentage
└── Customer Details Table
    ├── Customer Name
    ├── Email
    ├── Phone
    ├── Total Services Taken
    ├── Total Spent
    ├── Average per Service
    └── Services Breakdown
```

### Provider Service Report Breakdown:

```
Report Title & Date Range
├── Summary Statistics
│   ├── Total Bookings
│   ├── Platform Earnings
│   ├── Active Providers
│   └── Average Earnings/Booking
├── Top 5 Services Provided
│   ├── Service Name
│   ├── Times Provided
│   └── Percentage
└── Provider Details Table
    ├── Provider Name
    ├── Email
    ├── Phone
    ├── Services Provided
    ├── Total Earnings
    ├── Average per Service
    └── Services Breakdown
```

---

## 📅 Time Periods Explained

| Period | Coverage | Use Case |
|--------|----------|----------|
| **Daily** | Today only | Tracking daily activity |
| **Weekly** | Last 7 days | Trend analysis |
| **Monthly** | Entire month | Planning and reviews |

---

## 💾 PDF Download Features

### What's Included:
✓ Report title with date range
✓ Professional formatting
✓ Summary statistics table
✓ Top services section
✓ Detailed customer/provider data
✓ Generation timestamp
✓ Color-coded sections

### Filename Format:
- Customer Report: `customer_service_report_[period].pdf`
  - Example: `customer_service_report_daily.pdf`
- Provider Report: `provider_service_report_[period].pdf`
  - Example: `provider_service_report_monthly.pdf`

---

## 🔍 Reading the Tables

### Customer Service Report Table:

| Column | Meaning |
|--------|---------|
| Customer Name | Full name of customer |
| Email | Contact email |
| Phone | Contact phone number |
| Total Services | How many services customer booked |
| Total Spent | Total amount spent by customer |
| Avg Per Service | Average cost per service |
| Services Breakdown | List of services with counts |

### Provider Service Report Table:

| Column | Meaning |
|--------|---------|
| Provider Name | Full name of provider |
| Email | Contact email |
| Phone | Contact phone number |
| Services Provided | How many services provider delivered |
| Total Earnings | Total amount earned from services |
| Avg Per Service | Average earnings per service |
| Services Breakdown | List of services with counts |

---

## 💡 Tips & Tricks

### Tip 1: Compare Periods
- Generate daily report on Monday
- Generate weekly report
- Compare trends

### Tip 2: Track Top Performers
- Check who are top customers (by services)
- Check who are top providers (by services)
- Use for recognition or incentives

### Tip 3: Monitor Popular Services
- See what services customers want most
- See what services providers deliver most
- Plan service expansion based on demand

### Tip 4: Revenue Analysis
- Use average revenue per booking to track profitability
- Compare revenue between periods
- Identify growth trends

### Tip 5: Keep Records
- Download monthly reports for bookkeeping
- Archive reports for audit trail
- Track historical trends

---

## ❌ Common Issues & Solutions

### Issue: No Data Showing
**Solution:** 
- Ensure there are completed bookings in that period
- Check booking status is "completed"
- Verify dates are correct

### Issue: PDF Won't Download
**Solution:**
- Try a different browser
- Clear browser cache
- Disable download blocking extensions

### Issue: Can't See Reports Link
**Solution:**
- Make sure you're logged in as admin
- Check your user role is "admin"
- Try refreshing the page

### Issue: Numbers Look Wrong
**Solution:**
- Verify only "completed" bookings are counted
- Check booking total_price field
- Confirm date range in report title

---

## 🔐 Security & Permissions

✓ Reports are **admin-only**
✓ Non-admin users cannot access reports
✓ All data is real-time from database
✓ No data is cached or exported without admin action
✓ Download creates audit trail (file name includes date)

---

## 📱 Browser Compatibility

Works on:
- ✓ Chrome/Chromium
- ✓ Firefox
- ✓ Safari
- ✓ Edge
- ✓ Mobile browsers

---

## 🎨 Report Appearance

### Color Scheme:
- **Blue gradient**: Customer reports
- **Red/Pink gradient**: Provider reports
- **Green**: Success badges and top services
- **Light gray**: Table alternating rows

### Typography:
- **Poppins font**: Headers and labels
- **Helvetica**: Body text
- **Monospace**: Data values

---

## 📞 Support & Help

If you encounter issues:

1. **Check Documentation**: See REPORTS_DOCUMENTATION.md
2. **Verify Setup**: Run `python manage.py check`
3. **Check Logs**: Look for error messages in Django logs
4. **Contact Dev Team**: Report issues with report name and period

---

## ✨ Features At A Glance

| Feature | Customer Report | Provider Report |
|---------|-----------------|-----------------|
| Daily View | ✓ | ✓ |
| Weekly View | ✓ | ✓ |
| Monthly View | ✓ | ✓ |
| Top Services | ✓ | ✓ |
| PDF Export | ✓ | ✓ |
| Statistics | ✓ | ✓ |
| Detailed Data | ✓ | ✓ |
| Admin Only | ✓ | ✓ |

---

## 🎯 Use Cases

### Use Case 1: Daily Operations
```
Morning Review
├── Check daily customer report
├── Identify top customers
└── Monitor service demand
```

### Use Case 2: Weekly Planning
```
Weekly Strategy Meeting
├── Review weekly customer trends
├── Review weekly provider trends
├── Plan marketing activities
└── Download reports for meeting
```

### Use Case 3: Monthly Review
```
Month-end Report
├── Generate monthly customer report
├── Generate monthly provider report
├── Download both as PDF
├── Archive in records system
└── Share with stakeholders
```

### Use Case 4: Service Analysis
```
Service Optimization
├── Check top services in customer report
├── Check top services in provider report
├── Compare demand vs supply
└── Plan service improvements
```

---

## 🚀 Getting Started Now

1. **Login** as admin user
2. **Navigate** to Reports
3. **Choose** Customer or Provider report
4. **Select** Daily/Weekly/Monthly
5. **View** the analytics
6. **Download** PDF if needed

That's it! You're ready to use the Reports System.

---

**Last Updated:** May 25, 2026
**Version:** 1.0
