"""
URL configuration for Hyperlocal_Service_Provider project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from users import views as user_views
from payments import views as payment_views
from django.core.management import call_command

# Automatically apply database migrations on application start
try:
    call_command('migrate', interactive=False)
except Exception as e:
    import sys
    print("Startup migrations execution warning:", e, file=sys.stderr)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', user_views.home_view, name='home'),
    path('dashboard/', user_views.dashboard_redirect, name='dashboard'),
    path('about/', user_views.about_view, name='about'),
    path('contact/', user_views.contact_view, name='contact'),
    path('feedback/', user_views.feedback_view, name='feedback'),
    path('users/', include('users.urls')),
    path('providers/', include('providers.urls')),
    path('services/', include('services.urls')),
    path('bookings/', include('bookings.urls')),
    path('payments/', include('payments.urls')),
    path('reviews/', include('reviews.urls')),
    path('admin-panel/', include('admin_panel.urls')),
    path('check-payment/<str:transaction_id>/', payment_views.check_payment, name='check_payment'),
    path('payment-success/', payment_views.payment_success_redirect_view, name='payment_success'),
    path('payment-failed/', payment_views.payment_failed_redirect_view, name='payment_failed_page'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

