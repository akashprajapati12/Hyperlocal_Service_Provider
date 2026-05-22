from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.provider_register_view, name='provider_register'),
    path('dashboard/', views.provider_dashboard, name='provider_dashboard'),
    path('add-service/', views.add_service_view, name='add_service'),
    path('manage-requests/', views.manage_requests_view, name='manage_requests'),
    path('update-profile/', views.update_profile_view, name='provider_update_profile'),
    path('my-services/', views.my_services_view, name='my_services'),
    path('delete-service/<int:service_id>/', views.delete_service_view, name='delete_service'),
]
