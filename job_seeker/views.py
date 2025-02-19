from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.generics import RetrieveAPIView, ListAPIView, UpdateAPIView, DestroyAPIView
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from job_seeker.models import JobSeeker
from job_seeker.serializers import JobSeekerSerializer
from userApp.models import CustomUser
from django.core.validators import validate_email
from django.core.exceptions import ValidationError

class CreateJobSeeker(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        data = request.data

        # Ensure user role is "job_seeker"
        if user.role != 'job_seeker':
            return Response({"error": "Only job seekers can register here"}, status=status.HTTP_403_FORBIDDEN)

        # Prevent duplicate job seeker profiles
        if JobSeeker.objects.filter(user=user).exists():
            return Response({"error": "Job seeker profile already exists"}, status=status.HTTP_400_BAD_REQUEST)

        # Validate required fields
        required_fields = ['first_name', 'last_name', 'gender']
        for field in required_fields:
            if not data.get(field):
                return Response({f"error": f"{field} is required"}, status=status.HTTP_400_BAD_REQUEST)

        # Validate experience
        try:
            experience = int(data.get('experience', 0))
            if experience < 0:
                return Response({"error": "Experience cannot be negative"}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError:
            return Response({"error": "Experience must be a valid number"}, status=status.HTTP_400_BAD_REQUEST)

        # Ensure skills are a list
        skills = data.get('skills', [])
        if not isinstance(skills, list):
            return Response({"error": "Skills must be a list"}, status=status.HTTP_400_BAD_REQUEST)

        # Handle resume file
        resume = request.FILES.get('resume', None)
        if resume:
            allowed_extensions = ['pdf', 'doc', 'docx']
            file_extension = resume.name.split('.')[-1].lower()
            if file_extension not in allowed_extensions:
                return Response({"error": "Resume must be in PDF or DOC format"}, status=status.HTTP_400_BAD_REQUEST)

        job_seeker = JobSeeker.objects.create(
            user=user,
            first_name=data['first_name'],
            middle_name=data['middle_name'],
            last_name=data['last_name'],
            gender=data['gender'],
            skills=skills,
            experience=experience,
            education_level=data.get('education_level', 'none'),
            education_sector=data.get('education_sector', ''),
            resume=resume,
            created_by=user,
            status=False
        )
        serializer = JobSeekerSerializer(job_seeker)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

class GetAllJobSeekers(ListAPIView):
    queryset = JobSeeker.objects.all()
    serializer_class = JobSeekerSerializer

class GetJobSeekerById(RetrieveAPIView):
    queryset = JobSeeker.objects.all()
    serializer_class = JobSeekerSerializer
    lookup_field = 'id'

class GetJobSeekerByPhone(APIView):
    def get(self, request, phone_number):
        user = get_object_or_404(CustomUser, phone_number=phone_number)
        job_seeker = get_object_or_404(JobSeeker, user=user)
        serializer = JobSeekerSerializer(job_seeker)
        return Response(serializer.data)

class GetJobSeekerByEmail(APIView):
    def get(self, request, email):
        try:
            validate_email(email)
        except ValidationError:
            return Response({"error": "Invalid email format"}, status=status.HTTP_400_BAD_REQUEST)

        user = get_object_or_404(CustomUser, email=email)
        job_seeker = get_object_or_404(JobSeeker, user=user)
        serializer = JobSeekerSerializer(job_seeker)
        return Response(serializer.data)

class GetJobSeekersByStatus(APIView):
    def get(self, request, status_value):
        if status_value.lower() not in ['true', 'false']:
            return Response({"error": "Status must be 'true' or 'false'"}, status=status.HTTP_400_BAD_REQUEST)

        job_seekers = JobSeeker.objects.filter(status=status_value.lower() == 'true')
        serializer = JobSeekerSerializer(job_seekers, many=True)
        return Response(serializer.data)

class UpdateJobSeeker(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = JobSeeker.objects.all()
    serializer_class = JobSeekerSerializer
    lookup_field = 'id'

    def update(self, request, *args, **kwargs):
        job_seeker = self.get_object()

        # Ensure only the owner or admin can update the profile
        if request.user != job_seeker.user and not request.user.is_superuser:
            return Response({"error": "You are not authorized to update this profile"}, status=status.HTTP_403_FORBIDDEN)

        return super().update(request, *args, **kwargs)

class DeleteJobSeeker(DestroyAPIView):
    permission_classes = [IsAuthenticated]
    queryset = JobSeeker.objects.all()
    serializer_class = JobSeekerSerializer
    lookup_field = 'id'

    def delete(self, request, *args, **kwargs):
        job_seeker = self.get_object()

        # Ensure only the owner or admin can delete the profile
        if request.user != job_seeker.user and not request.user.is_superuser:
            return Response({"error": "You are not authorized to delete this profile"}, status=status.HTTP_403_FORBIDDEN)

        return super().delete(request, *args, **kwargs)

class GetJobSeekersCreatedByUser(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        job_seekers = JobSeeker.objects.filter(created_by=request.user)
        serializer = JobSeekerSerializer(job_seekers, many=True)
        return Response(serializer.data)
