from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import JobOffer
from .serializers import JobOfferSerializer
from jobCategoryApp.models import JobType, JobCategory



def check_duplicate_job_offer(user, title, job_type, job_category):
    """
    Check if user has an active or draft job offer with same title, type and category
    Returns (bool, str): (is_duplicate, error_message)
    """
    existing_offer = JobOffer.objects.filter(
        created_by=user,
        title__iexact=title,  # Case-insensitive title comparison
        job_type=job_type,
        job_category=job_category,
        status__in=['active', 'draft']  # Only check active and draft jobs
    ).first()
    
    if existing_offer:
        return True, f"You already have an active job offer '{title}' with the same job type and category. Wait until it expires or closes before creating a similar one."
    return False, ""




def validate_job_type_category(job_type_id, job_category_id):
    """
    Validate that job type and category exist in database
    Returns (bool, str): (is_valid, error_message)
    """
    try:
        job_type = JobType.objects.get(id=job_type_id)
        job_category = JobCategory.objects.get(id=job_category_id)
        return True, ""
    except JobType.DoesNotExist:
        return False, f"Job type with ID {job_type_id} does not exist."
    except JobCategory.DoesNotExist:
        return False, f"Job category with ID {job_category_id} does not exist."
    





@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_job_offer(request):
    # First validate the job type and category exist
    job_type_id = request.data.get('job_type_id')
    job_category_id = request.data.get('job_category_id')
    
    is_valid, error_message = validate_job_type_category(job_type_id, job_category_id)
    if not is_valid:
        return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)
    
    # Check for duplicate job offers
    title = request.data.get('title')
    job_type = JobType.objects.get(id=job_type_id)
    job_category = JobCategory.objects.get(id=job_category_id)
    
    is_duplicate, error_message = check_duplicate_job_offer(
        request.user, 
        title, 
        job_type, 
        job_category
    )
    if is_duplicate:
        return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)
    
    # If all validations pass, create the job offer
    serializer = JobOfferSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)






@api_view(['GET'])
def get_job_offer_by_id(request, job_id):
    job_offer = JobOffer.objects.filter(id=job_id)
    serializer = JobOfferSerializer(job_offer)
    return Response(serializer.data)





@api_view(['GET'])
@permission_classes([AllowAny])
def get_all_job_offers(request):
    job_offers = JobOffer.objects.all()
    serializer = JobOfferSerializer(job_offers, many=True)
    return Response(serializer.data)




@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_job_offer(request, job_id):
    job_offer = get_object_or_404(JobOffer, id=job_id)
    
    # Check if user is the creator or admin
    if request.user != job_offer.created_by and request.user.role != 'admin':
        return Response(
            {"error": "You don't have permission to update this job offer."}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    # If job type or category is being updated, validate they exist
    if 'job_type_id' in request.data or 'job_category_id' in request.data:
        job_type_id = request.data.get('job_type_id', job_offer.job_type.id)
        job_category_id = request.data.get('job_category_id', job_offer.job_category.id)
        
        is_valid, error_message = validate_job_type_category(job_type_id, job_category_id)
        if not is_valid:
            return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)
    
    # If title is being updated, check for duplicates
    if 'title' in request.data:
        title = request.data.get('title')
        job_type = JobType.objects.get(id=job_type_id)
        job_category = JobCategory.objects.get(id=job_category_id)
        
        # Exclude current job offer from duplicate check
        is_duplicate, error_message = check_duplicate_job_offer(
            request.user, 
            title, 
            job_type, 
            job_category
        )
        if is_duplicate and job_offer.title.lower() != title.lower():
            return Response({"error": error_message}, status=status.HTTP_400_BAD_REQUEST)
    
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






@api_view(['GET'])
def get_job_offers_by_category(request):
    category_name = request.data.get('category_name')
    job_offers = JobOffer.objects.filter(job_category__name__iexact=category_name)
    serializer = JobOfferSerializer(job_offers, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)






@api_view(['GET'])
def get_job_offers_by_job_type(request):
    job_type_name = request.data.get('type_name')
    job_offers = JobOffer.objects.filter(job_type__name__iexact=job_type_name)
    serializer = JobOfferSerializer(job_offers, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)






@api_view(['GET'])
def get_job_offers_by_category_and_job_type(request):
    category_name = request.data.get('category_name')
    job_type_name = request.data.get('job_type_name')
    job_offers = JobOffer.objects.filter(
        job_category__name__iexact=category_name,
        job_type__name__iexact=job_type_name
    )
    serializer = JobOfferSerializer(job_offers, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)






