# testimonialApp/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Testimonial
from .serializers import TestimonialSerializer

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_testimonial(request):
    """
    Create a new testimonial.
    For non-job seekers, first_name and last_name are required in the request.
    For job seekers, names will be taken from their profile.
    """
    serializer = TestimonialSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_all_testimonials(request):
    """
    Retrieve all testimonials.
    """
    testimonials = Testimonial.objects.all().order_by('-created_at')
    serializer = TestimonialSerializer(testimonials, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_testimonial_by_id(request, pk):
    """
    Retrieve a testimonial by its ID.
    """
    testimonial = get_object_or_404(Testimonial, pk=pk)
    serializer = TestimonialSerializer(testimonial)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_testimonials(request):
    """
    Retrieve all testimonials created by the logged-in user.
    """
    testimonials = Testimonial.objects.filter(created_by=request.user).order_by('-created_at')
    serializer = TestimonialSerializer(testimonials, many=True)
    return Response(serializer.data)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_testimonial(request, pk):
    """
    Update a testimonial by its ID.
    Only the owner of the testimonial can update it.
    """
    testimonial = get_object_or_404(Testimonial, pk=pk)
    
    # Check if the user is the owner of the testimonial
    if testimonial.created_by != request.user:
        return Response(
            {"detail": "You do not have permission to update this testimonial."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = TestimonialSerializer(testimonial, data=request.data, partial=True, context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_testimonial(request, pk):
    """
    Delete a testimonial by its ID.
    Only the owner of the testimonial can delete it.
    """
    testimonial = get_object_or_404(Testimonial, pk=pk)
    
    # Check if the user is the owner of the testimonial
    if testimonial.created_by != request.user:
        return Response(
            {"detail": "You do not have permission to delete this testimonial."},
            status=status.HTTP_403_FORBIDDEN
        )
    
    testimonial.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)
