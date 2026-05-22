from django.urls import path
from . import views

urlpatterns = [
    path('add/<int:booking_id>/', views.add_review_view, name='add_review'),
]
