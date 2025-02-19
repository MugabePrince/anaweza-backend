from django.urls import path
from . import views

urlpatterns = [
    # JobCategory URLs
    path('job-categories/', views.JobCategoryListCreateView.as_view(), name='job-category-list-create'),
    path('job-categories/<int:id>/', views.JobCategoryDetailView.as_view(), name='job-category-detail'),
    path('job-categories/by-name/', views.get_job_category_by_name, name='job-category-by-name'),
    path('job-categories/by-user/', views.get_job_categories_by_user, name='job-categories-by-user'),
    
    # JobType URLs
    path('job-types/', views.JobTypeListCreateView.as_view(), name='job-type-list-create'),
    path('job-types/<int:id>/', views.JobTypeDetailView.as_view(), name='job-type-detail'),
    path('job-types/by-name/', views.get_job_type_by_name, name='job-type-by-name'),
    path('job-types/by-user/', views.get_job_types_by_user, name='job-types-by-user'),
]