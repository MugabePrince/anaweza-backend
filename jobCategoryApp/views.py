from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import JobCategory, JobType
from .serializers import JobCategorySerializer, JobTypeSerializer
from django.shortcuts import get_object_or_404
from django.db.models import Q

# JobCategory Views
class JobCategoryListCreateView(generics.ListCreateAPIView):
    serializer_class = JobCategorySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return JobCategory.objects.all()
    
    def create(self, request, *args, **kwargs):
        # Check if category with same name already exists
        name = request.data.get('name')
        if JobCategory.objects.filter(name__iexact=name).exists():
            return Response(
                {"error": "A job category with this name already exists."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().create(request, *args, **kwargs)

class JobCategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = JobCategorySerializer
    permission_classes = [IsAuthenticated]
    queryset = JobCategory.objects.all()
    lookup_field = 'id'
    
    def update(self, request, *args, **kwargs):
        # Check if updating to a name that already exists (excluding this instance)
        name = request.data.get('name')
        if name and JobCategory.objects.filter(~Q(id=self.kwargs['id']), name__iexact=name).exists():
            return Response(
                {"error": "A job category with this name already exists."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Check if user is the creator
        if instance.created_by != request.user:
            return Response(
                {"error": "You can only delete job categories you have created."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_job_category_by_name(request):
    name = request.data.get('name', '')
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
    user_id = request.user.id
    job_categories = JobCategory.objects.filter(created_by_id=user_id)
    serializer = JobCategorySerializer(job_categories, many=True, context={'request': request})
    return Response(serializer.data)

# JobType Views
class JobTypeListCreateView(generics.ListCreateAPIView):
    serializer_class = JobTypeSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return JobType.objects.all()
    
    def create(self, request, *args, **kwargs):
        # Check if job type with same name already exists
        name = request.data.get('name')
        if JobType.objects.filter(name__iexact=name).exists():
            return Response(
                {"error": "A job type with this name already exists."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().create(request, *args, **kwargs)

class JobTypeDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = JobTypeSerializer
    permission_classes = [IsAuthenticated]
    queryset = JobType.objects.all()
    lookup_field = 'id'
    
    def update(self, request, *args, **kwargs):
        # Check if updating to a name that already exists (excluding this instance)
        name = request.data.get('name')
        if name and JobType.objects.filter(~Q(id=self.kwargs['id']), name__iexact=name).exists():
            return Response(
                {"error": "A job type with this name already exists."},
                status=status.HTTP_400_BAD_REQUEST
            )
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Check if user is the creator
        if instance.created_by != request.user or request.user.role != 'admin':
            return Response(
                {"error": "You can only delete job types you have created."},
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_job_type_by_name(request):
    name = request.data.get('name', '')
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
    user_id = request.user.id
    job_types = JobType.objects.filter(created_by_id=user_id)
    serializer = JobTypeSerializer(job_types, many=True, context={'request': request})
    return Response(serializer.data)