from django.urls import path
from job_seeker import views

urlpatterns = [
    path('create/', views.create_job_seeker, name='create-job-seeker'),
    path('all/', views.get_all_job_seekers, name='all-job-seekers'),
    path('<int:id>/', views.get_job_seeker_by_id, name='job-seeker-by-id'),
    path('phone/<str:phone_number>/', views.get_job_seeker_by_phone, name='job-seeker-by-phone'),
    path('email/<str:email>/', views.get_job_seeker_by_email, name='job-seeker-by-email'),
    path('status/<str:status_value>/', views.get_job_seekers_by_status, name='job-seekers-by-status'),
    path('update/<int:id>/', views.update_job_seeker, name='update-job-seeker'),
    path('delete/<int:id>/', views.delete_job_seeker, name='delete-job-seeker'),
    path('created-by-user/', views.get_job_seekers_created_by_user, name='job-seekers-created-by-user'),
    path('by-user/<int:user_id>/', views.get_job_seeker_by_user, name='job-seeker-by-user'),
]
##############