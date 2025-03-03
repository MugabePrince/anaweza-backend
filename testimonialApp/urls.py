from django.urls import path
from . import views

urlpatterns = [
    path('testimonials/', views.get_all_testimonials, name='get_all_testimonials'),
    path('testimonials/create/', views.create_testimonial, name='create_testimonial'),
    path('testimonials/<int:pk>/', views.get_testimonial_by_id, name='get_testimonial_by_id'),
    path('testimonials/user/', views.get_user_testimonials, name='get_user_testimonials'),
    path('testimonials/<int:pk>/update/', views.update_testimonial, name='update_testimonial'),
    path('testimonials/<int:pk>/delete/', views.delete_testimonial, name='delete_testimonial'),
]