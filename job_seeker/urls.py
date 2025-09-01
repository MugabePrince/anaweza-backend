# job_seeker/urls.py

from django.urls import path
from . import views

urlpatterns = [
    # Existing URLs
    path('create/', views.create_job_seeker, name='create_job_seeker'),
    path('all/', views.get_all_job_seekers, name='get_all_job_seekers'),
    path('id/<int:id>/', views.get_job_seeker_by_id, name='get_job_seeker_by_id'),
    path('phone/<str:phone_number>/', views.get_job_seeker_by_phone, name='get_job_seeker_by_phone'),
    path('email/<str:email>/', views.get_job_seeker_by_email, name='get_job_seeker_by_email'),
    path('status/<str:status_value>/', views.get_job_seekers_by_status, name='get_job_seekers_by_status'),
    path('update/<int:id>/', views.update_job_seeker, name='update_job_seeker'),
    path('delete/<int:id>/', views.delete_job_seeker, name='delete_job_seeker'),
    path('created-by-user/', views.get_job_seekers_created_by_user, name='get_job_seekers_created_by_user'),
    path('by-user/<int:user_id>/', views.get_job_seeker_by_user, name='get_job_seeker_by_user'),
    
    # User details URLs
    path('user/details/', views.get_user_details, name='get_user_details'),
    path('user/update/', views.update_user_details, name='update_user_details'),
    
    # Enhanced skills management URLs
    path('skills/', views.get_job_seeker_skills, name='get_job_seeker_skills'),
    path('skills/<int:job_seeker_id>/', views.get_job_seeker_skills, name='get_job_seeker_skills_by_id'),
    path('skills/update/', views.update_job_seeker_skills, name='update_job_seeker_skills'),
    path('search/skills/', views.search_job_seekers_by_skill, name='search_job_seekers_by_skill'),
]