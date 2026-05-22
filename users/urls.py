from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('', views.customer_dashboard, name='customer_dashboard'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile_view, name='edit_profile'),
    path('notifications/', views.notifications_view, name='notifications'),
    path('notifications/<int:notif_id>/click/', views.notification_click_view, name='notification_click'),
]
