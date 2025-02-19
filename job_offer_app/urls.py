from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_job_offer, name='create_job_offer'),
    path('all/', views.get_all_job_offers, name='get_all_job_offers'),
    path('<int:job_id>/', views.get_job_offer_by_id, name='get_job_offer_by_id'),
    path('update/<int:job_id>/', views.update_job_offer, name='update_job_offer'),
    path('delete/<int:job_id>/', views.delete_job_offer, name='delete_job_offer'),
    path('my-offers/', views.get_my_job_offers, name='get_my_job_offers'),
    path('by-phone/', views.get_job_offers_by_phone, name='get_job_offers_by_phone'),
    path('by-email/', views.get_job_offers_by_email, name='get_job_offers_by_email'),
]