from django.urls import path
from job_seeker.views import *

urlpatterns = [
    path('create/', CreateJobSeeker.as_view(), name='create-job-seeker'),
    path('all/', GetAllJobSeekers.as_view(), name='all-job-seekers'),
    path('<int:id>/', GetJobSeekerById.as_view(), name='job-seeker-by-id'),
    path('phone/<str:phone_number>/', GetJobSeekerByPhone.as_view(), name='job-seeker-by-phone'),
    path('email/<str:email>/', GetJobSeekerByEmail.as_view(), name='job-seeker-by-email'),
    path('status/<str:status_value>/', GetJobSeekersByStatus.as_view(), name='job-seekers-by-status'),
    path('update/<int:id>/', UpdateJobSeeker.as_view(), name='update-job-seeker'),
    path('delete/<int:id>/', DeleteJobSeeker.as_view(), name='delete-job-seeker'),
    path('created-by-user/', GetJobSeekersCreatedByUser.as_view(), name='job-seekers-created-by-user'),
]
