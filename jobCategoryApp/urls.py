from django.urls import path
from . import views

urlpatterns = [
    # Job Category URLs
    path('categories/', views.list_job_categories, name='list-job-categories'),
    path('create/', views.create_job_category, name='create-job-category'),
    path('<int:id>/', views.get_job_category, name='get-job-category'),
    path('update/<int:id>/', views.update_job_category, name='update-job-category'),
    path('delete/<int:id>/', views.delete_job_category, name='delete-job-category'),
    path('name/', views.get_job_category_by_name, name='get-job-category-by-name'),
    path('user/', views.get_job_categories_by_user, name='get-job-categories-by-user'),
    
    # Job Type URLs
    path('types/', views.list_job_types, name='list-job-types'),
    path('type/create/', views.create_job_type, name='create-job-type'),
    path('type/<int:id>/', views.get_job_type, name='get-job-type'),
    path('type/update/<int:id>/', views.update_job_type, name='update-job-type'),
    path('type/delete/<int:id>/', views.delete_job_type, name='delete-job-type'),
    path('type/name/', views.get_job_type_by_name, name='get-job-type-by-name'),
    path('type/user/', views.get_job_types_by_user, name='get-job-types-by-user'),
]