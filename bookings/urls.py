from django.urls import path
from . import views

urlpatterns = [
    path('create/<int:service_id>/', views.create_booking_view, name='create_booking'),
    path('<int:booking_id>/', views.booking_detail_view, name='booking_detail'),
    path('<int:booking_id>/cancel/', views.cancel_booking_view, name='cancel_booking'),
    path('<int:booking_id>/extra-time/', views.add_extra_time_view, name='add_extra_time'),
    path('<int:booking_id>/chat/', views.booking_chat_view, name='booking_chat'),
    path('<int:booking_id>/chat/messages/', views.booking_messages_json, name='booking_chat_messages'),
    path('<int:booking_id>/chat/delete/', views.booking_chat_delete_view, name='booking_chat_delete'),
    path('history/', views.booking_history_view, name='booking_history'),
    path('check-availability/', views.check_availability_view, name='check_availability'),
    path('inbox/', views.chat_inbox_view, name='chat_inbox'),
    path('admin-start-chat/<int:user_id>/', views.admin_start_chat_view, name='admin_start_chat'),
    path('<int:booking_id>/raise-dispute/', views.raise_dispute_view, name='raise_dispute'),
]
