# urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Create and list applications
    path('applications/', views.get_all_applications, name='get-all-applications'),
    path('create/', views.create_application, name='create-application'),
    
    # Get specific application
    path('<int:pk>/', views.get_application, name='get-application'),
    
    # Update and delete application
    path('update/<int:pk>/', views.update_application, name='update-application'),
    path('delete/<int:pk>/', views.delete_application, name='delete-application'),
    
    # Status management
    path('status/<int:pk>/', views.update_application_status, name='update-application-status'),
    path('accept/<int:pk>/', views.accept_application, name='accept-application'),
    path('reject/<int:pk>/', views.reject_application, name='reject-application'),
    path('shortlist/<int:pk>/', views.shortlist_application, name='shortlist-application'),
    path('withdraw/<int:pk>/', views.withdraw_application, name='withdraw-application'),
    
    # User-specific endpoints
    path('my-applications/', views.get_my_applications, name='get-my-applications'),
    path('my-job-offer-applications/', views.get_my_job_offer_applications, name='get-my-job-offer-applications'),
    path('job-offer/<int:job_offer_id>/', views.get_job_offer_applications, name='get-job-offer-applications'),
]