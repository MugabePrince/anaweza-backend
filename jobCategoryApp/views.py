from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import JobCategory, JobType
from .serializers import JobCategorySerializer, JobTypeSerializer
from django.shortcuts import get_object_or_404
from django.db.models import Q

# Job Category Views
@api_view(['GET'])
def list_job_categories(request):
    job_categories = JobCategory.objects.all()
    serializer = JobCategorySerializer(job_categories, many=True, context={'request': request})
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_job_category(request):
    name = request.data.get('name')
    if JobCategory.objects.filter(name__iexact=name).exists():
        return Response(
            {"error": "A job category with this name already exists."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create a mutable copy of request.data and add the current user
    data = request.data.copy()
    data['created_by'] = request.user.id
    
    serializer = JobCategorySerializer(data=data, context={'request': request})
    if serializer.is_valid():
        serializer.save(created_by=request.user)  # Explicitly set created_by
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_job_category(request, id):
    job_category = get_object_or_404(JobCategory, id=id)
    serializer = JobCategorySerializer(job_category, context={'request': request})
    return Response(serializer.data)

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_job_category(request, id):
    job_category = get_object_or_404(JobCategory, id=id)
    name = request.data.get('name')
    if name and JobCategory.objects.filter(~Q(id=id), name__iexact=name).exists():
        return Response(
            {"error": "A job category with this name already exists."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    serializer = JobCategorySerializer(
        job_category, 
        data=request.data, 
        partial=request.method=='PATCH',
        context={'request': request}
    )
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_job_category(request, id):
    job_category = get_object_or_404(JobCategory, id=id)
    if job_category.created_by != request.user:
        return Response(
            {"error": "You can only delete job categories you have created."},
            status=status.HTTP_403_FORBIDDEN
        )
    job_category.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
def get_job_category_by_name(request):
    name = request.query_params.get('name', '')  # Changed from request.data to query_params
    if not name:
        return Response(
            {"error": "Name parameter is required."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    job_category = get_object_or_404(JobCategory, name__iexact=name)
    serializer = JobCategorySerializer(job_category, context={'request': request})
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_job_categories_by_user(request):
    job_categories = JobCategory.objects.filter(created_by=request.user)
    serializer = JobCategorySerializer(job_categories, many=True, context={'request': request})
    return Response(serializer.data)

# Job Type Views

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_job_type(request):
    name = request.data.get('name')
    if JobType.objects.filter(name__iexact=name).exists():
        return Response(
            {"error": "A job type with this name already exists."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    serializer = JobTypeSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['GET'])
def list_job_types(request):
    job_types = JobType.objects.all()
    serializer = JobTypeSerializer(job_types, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_job_type(request, id):
    job_type = get_object_or_404(JobType, id=id)
    serializer = JobTypeSerializer(job_type, context={'request': request})
    return Response(serializer.data)

@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_job_type(request, id):
    job_type = get_object_or_404(JobType, id=id)
    name = request.data.get('name')
    if name and JobType.objects.filter(~Q(id=id), name__iexact=name).exists():
        return Response(
            {"error": "A job type with this name already exists."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    serializer = JobTypeSerializer(
        job_type, 
        data=request.data, 
        partial=request.method=='PATCH',
        context={'request': request}
    )
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_job_type(request, id):
    job_type = get_object_or_404(JobType, id=id)
    if job_type.created_by != request.user and request.user.role != 'admin':
        return Response(
            {"error": "You can only delete job types you have created."},
            status=status.HTTP_403_FORBIDDEN
        )
    job_type.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
def get_job_type_by_name(request):
    name = request.query_params.get('name', '')  # Changed from request.data to query_params
    if not name:
        return Response(
            {"error": "Name parameter is required."},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    job_type = get_object_or_404(JobType, name__iexact=name)
    serializer = JobTypeSerializer(job_type, context={'request': request})
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_job_types_by_user(request):
    job_types = JobType.objects.filter(created_by=request.user)
    serializer = JobTypeSerializer(job_types, many=True, context={'request': request})
    return Response(serializer.data)