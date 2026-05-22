from django.urls import path
from . import views

urlpatterns = [
    path('', views.service_list_view, name='service_list'),
    path('<int:service_id>/', views.service_detail_view, name='service_detail'),
]
