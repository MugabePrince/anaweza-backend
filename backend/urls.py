# urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('userApp.urls')),
    path('job_offer/', include('job_offer_app.urls')),
    path('job_seeker/', include('job_seeker.urls')),
    path('category/', include('jobCategoryApp.urls')),
    path('advertisement/', include('advertisementApp.urls')),
    path('application/', include('jobApplication_App.urls')),
    path('testimony/', include('testimonialApp.urls')),
    path('chat/', include('chatApp.urls')),
]

# This will serve both static and media files in development
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)