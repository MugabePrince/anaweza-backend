from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

urlpatterns = [
    path('advertisements/', views.get_all_advertisements, name='get_all_advertisements'),
    path('create/', views.create_advertisement, name='create_advertisement'),
    path('<int:pk>/', views.get_advertisement_by_id, name='get_advertisement_by_id'),
    path('contact/<str:contact_info>/', views.get_advertisements_by_contact, name='get_advertisement_by_contact'),
    path('update/<int:pk>/', views.update_advertisement, name='update_advertisement'),
    path('delete/<int:pk>/', views.delete_advertisement, name='delete_advertisement'),
]
