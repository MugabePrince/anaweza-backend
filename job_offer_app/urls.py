from django.urls import path
from . import views
from .views import get_job_offers_by_category, get_job_offers_by_job_type, get_job_offers_by_category_and_job_type

urlpatterns = [
    path('create/', views.create_job_offer, name='create_job_offer'),
    path('offers/', views.get_all_job_offers, name='get_all_job_offers'),
    path('<int:job_id>/', views.get_job_offer_by_id, name='get_job_offer_by_id'),
    path('update/<int:job_id>/', views.update_job_offer, name='update_job_offer'),
    path('delete/<int:job_id>/', views.delete_job_offer, name='delete_job_offer'),
    path('my-offers/', views.get_my_job_offers, name='get_my_job_offers'),
    path('by-phone/', views.get_job_offers_by_phone, name='get_job_offers_by_phone'),
    path('by-email/', views.get_job_offers_by_email, name='get_job_offers_by_email'),
     path('category/', get_job_offers_by_category, name='job_offers_by_category'),
    path('job-type/', get_job_offers_by_job_type, name='job_offers_by_job_type'),
    path('typeandcategory/', get_job_offers_by_category_and_job_type, name='job_offers_by_category_and_job_type'),
]