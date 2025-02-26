
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('userApp.urls')),
    path('job_offer/', include('job_offer_app.urls')),
    path('job_seeker/', include('job_seeker.urls')),
    path('category/', include('jobCategoryApp.urls')),
    path('advertisement/', include('advertisementApp.urls')),
]
