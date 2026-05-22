from django.urls import path
from . import views

urlpatterns = [
    path('checkout/<int:booking_id>/', views.checkout_view, name='checkout'),
    path('confirmation/<int:booking_id>/', views.payment_confirmation_view, name='payment_confirmation'),
    path('failed/<int:booking_id>/', views.payment_failed_view, name='payment_failed'),
    path('upi/<int:booking_id>/', views.upi_payment_view, name='upi_payment'),
    path('upi/<int:booking_id>/status/', views.check_payment_status_view, name='check_payment_status'),
    path('upi/<int:booking_id>/cancel/', views.cancel_and_rebook_view, name='cancel_and_rebook'),
    path('upi/<int:booking_id>/cancel-booking/', views.cancel_booking_from_payment_view, name='cancel_booking_from_payment'),
]

