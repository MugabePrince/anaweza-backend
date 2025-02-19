from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import JobOffer
from .serializers import JobOfferSerializer

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_job_offer(request):
    # if request.user.role != 'job_offer':
    #     return Response({"error": "Only job offer accounts can create job offers."}, status=status.HTTP_403_FORBIDDEN)
    
    serializer = JobOfferSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def get_job_offer_by_id(request, job_id):
    job_offer = get_object_or_404(JobOffer, id=job_id)
    serializer = JobOfferSerializer(job_offer)
    return Response(serializer.data)

@api_view(['GET'])
def get_all_job_offers(request):
    job_offers = JobOffer.objects.filter(status='active')
    serializer = JobOfferSerializer(job_offers, many=True)
    return Response(serializer.data)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_job_offer(request, job_id):
    job_offer = get_object_or_404(JobOffer, id=job_id)
    
    # Check if user is the creator or admin
    if request.user != job_offer.created_by and request.user.role != 'admin':
        return Response({"error": "You don't have permission to update this job offer."}, 
                      status=status.HTTP_403_FORBIDDEN)
    
    serializer = JobOfferSerializer(job_offer, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_job_offer(request, job_id):
    job_offer = get_object_or_404(JobOffer, id=job_id)
    
    if request.user != job_offer.created_by and request.user.role != 'admin':
        return Response({"error": "You don't have permission to delete this job offer."}, 
                      status=status.HTTP_403_FORBIDDEN)
    
    job_offer.delete()
    return Response({"message": "Job offer deleted successfully."}, status=status.HTTP_200_OK)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_job_offers(request):
    job_offers = JobOffer.objects.filter(created_by=request.user)
    serializer = JobOfferSerializer(job_offers, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_job_offers_by_phone(request):
    phone_number = request.query_params.get('phone_number')
    if not phone_number:
        return Response({"error": "Phone number is required."}, status=status.HTTP_400_BAD_REQUEST)
    
    job_offers = JobOffer.objects.filter(created_by__phone_number=phone_number)
    serializer = JobOfferSerializer(job_offers, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_job_offers_by_email(request):
    email = request.query_params.get('email')
    if not email:
        return Response({"error": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)
    
    job_offers = JobOffer.objects.filter(created_by__email=email)
    serializer = JobOfferSerializer(job_offers, many=True)
    return Response(serializer.data)