from django.urls import path
from . import views

urlpatterns = [
    path('', views.admin_dashboard, name='admin_dashboard'),
    path('users/', views.manage_users_view, name='manage_users'),
    path('providers/', views.manage_providers_view, name='manage_providers'),
    path('bookings/', views.manage_bookings_view, name='manage_bookings'),
    path('bookings/<int:booking_id>/', views.admin_booking_detail_view, name='admin_booking_detail'),
    path('users/<int:user_id>/', views.admin_user_detail_view, name='admin_user_detail'),
]
