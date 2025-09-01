from rest_framework.decorators import api_view, permission_classes
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from job_seeker.models import JobSeeker
from job_seeker.serializers import JobSeekerSerializer, JobSeekerCreateUpdateSerializer
from userApp.models import CustomUser
from django.core.validators import validate_email
from django.core.exceptions import ValidationError, ObjectDoesNotExist
import json
import re

def parse_skills_from_frontend(skills_data):
    """
    Parse skills data from frontend format to structured format
    Frontend sends: "JavaScript (1-3 years), Python (3-5 years), React (0-1 years)"
    Returns: [{'name': 'JavaScript', 'experience': '1-3'}, ...]
    """
    if not skills_data or not isinstance(skills_data, str):
        return []
    
    skills_list = []
    # Split by comma and process each skill
    skill_items = [item.strip() for item in skills_data.split(',') if item.strip()]
    
    for skill_item in skill_items:
        # Use regex to extract skill name and experience
        # Pattern matches: "Skill Name (X-Y years)" or "Skill Name (X+ years)"
        match = re.match(r'^(.+?)\s*\(([^)]+)\s*years?\)$', skill_item.strip())
        if match:
            skill_name = match.group(1).strip()
            experience_part = match.group(2).strip()
            
            # Extract just the experience range (remove 'years' if present)
            experience = re.sub(r'\s*years?$', '', experience_part)
            
            skills_list.append({
                'name': skill_name,
                'experience': experience
            })
        else:
            # Fallback: if format doesn't match, treat as skill name only
            skill_name = skill_item.strip()
            if skill_name:
                skills_list.append({
                    'name': skill_name,
                    'experience': '0-1'  # Default experience
                })
    
    return skills_list

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_job_seeker(request):
    user = request.user
    data = dict(request.data) # Make a copy to modify
    
    # Print received data for debugging
    print("Received data:", data)
    print("Files:", request.FILES)

    # Duplicate check
    if JobSeeker.objects.filter(user=user).exists():
        return Response({"error": "Job seeker profile already exists"}, status=status.HTTP_400_BAD_REQUEST)

    # Validate required fields
    validation_errors = {}
    required_fields = ['first_name', 'last_name', 'gender', 'salary_range']
    for field in required_fields:
        if not data.get(field):
            validation_errors[field] = f"{field} is required"
    
    # Experience validation
    try:
        if 'experience' in data and data['experience']:
            experience = int(data.get('experience', 0))
            if experience < 0:
                validation_errors['experience'] = "Experience cannot be negative"
        else:
            experience = 0
    except ValueError:
        validation_errors['experience'] = "Experience must be a valid number"

    # Enhanced Skills validation and parsing
    skills_raw = data.get('skills', '')
    skills_with_experience = []
    
    if skills_raw:
        try:
            # Try to parse as JSON first (new format)
            if skills_raw.startswith('[') or skills_raw.startswith('{'):
                skills_with_experience = json.loads(skills_raw)
            else:
                # Parse from frontend string format
                skills_with_experience = parse_skills_from_frontend(skills_raw)
            
            # Validate parsed skills
            if not isinstance(skills_with_experience, list):
                validation_errors['skills'] = "Skills must be a list"
            else:
                for skill in skills_with_experience:
                    if not isinstance(skill, dict) or 'name' not in skill:
                        validation_errors['skills'] = "Invalid skill format"
                        break
                    if not skill['name'].strip():
                        validation_errors['skills'] = "Skill name cannot be empty"
                        break
                        
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error parsing skills: {e}")
            validation_errors['skills'] = "Invalid skills format"

    # Resume validation
    resume = request.FILES.get('resume', None)
    if resume:
        allowed_extensions = ['pdf', 'doc', 'docx']
        file_extension = resume.name.split('.')[-1].lower()
        if file_extension not in allowed_extensions:
            validation_errors['resume'] = "Resume must be in PDF or DOC format"
    
    # Fee validation
    try:
        registration_fee = float(data.get('registration_fee', 0))
        if registration_fee < 0:
            validation_errors['registration_fee'] = "Registration fee cannot be negative"
    except ValueError:
        validation_errors['registration_fee'] = "Registration fee must be a valid number"
        
    try:
        renewal_fee = float(data.get('renewal_fee', 0))
        if renewal_fee < 0:
            validation_errors['renewal_fee'] = "Renewal fee cannot be negative"
    except ValueError:
        validation_errors['renewal_fee'] = "Renewal fee must be a valid number"

    # Return validation errors if any
    if validation_errors:
        return Response(validation_errors, status=status.HTTP_400_BAD_REQUEST)

    # Create job seeker profile
    try:
        job_seeker = JobSeeker.objects.create(
            user=user,
            first_name=data['first_name'],
            middle_name=data.get('middle_name', ''),
            last_name=data['last_name'],
            gender=data['gender'],
            salary_range=data.get('salary_range', ''),
            experience=experience,
            education_level=data.get('education_level', 'none'),
            education_sector=data.get('education_sector', ''),
            resume=resume,
            registration_fee=registration_fee,
            renewal_fee=renewal_fee,
            created_by=user,
            status=True,
            district=data.get('district', ''),
            sector=data.get('sector', '')
        )
        
        # Set skills with experience levels using the new method
        if skills_with_experience:
            job_seeker.set_skills_with_experience(skills_with_experience)
            job_seeker.save()
        
        serializer = JobSeekerSerializer(job_seeker)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    except Exception as e:
        print("Error creating job seeker:", str(e))
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



@api_view(['GET'])
@permission_classes([AllowAny])
def get_all_job_seekers(request):
    job_seekers = JobSeeker.objects.all()
    serializer = JobSeekerSerializer(job_seekers, many=True)
    return Response(serializer.data)

@api_view(['GET'])
def get_job_seeker_by_id(request, id):
    job_seeker = get_object_or_404(JobSeeker, id=id)
    serializer = JobSeekerSerializer(job_seeker)
    return Response(serializer.data)

@api_view(['GET'])
def get_job_seeker_by_phone(request, phone_number):
    user = get_object_or_404(CustomUser, phone_number=phone_number)
    job_seeker = get_object_or_404(JobSeeker, user=user)
    serializer = JobSeekerSerializer(job_seeker)
    return Response(serializer.data)

@api_view(['GET'])
def get_job_seeker_by_email(request, email):
    try:
        validate_email(email)
    except ValidationError:
        return Response({"error": "Invalid email format"}, status=status.HTTP_400_BAD_REQUEST)

    user = get_object_or_404(CustomUser, email=email)
    job_seeker = get_object_or_404(JobSeeker, user=user)
    serializer = JobSeekerSerializer(job_seeker)
    return Response(serializer.data)

@api_view(['GET'])
def get_job_seekers_by_status(request, status_value):
    if status_value.lower() not in ['true', 'false']:
        return Response({"error": "Status must be 'true' or 'false'"}, status=status.HTTP_400_BAD_REQUEST)

    job_seekers = JobSeeker.objects.filter(status=status_value.lower() == 'true')
    serializer = JobSeekerSerializer(job_seekers, many=True)
    return Response(serializer.data)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_job_seeker(request, id):
    job_seeker = get_object_or_404(JobSeeker, id=id)
    
    if request.user != job_seeker.user and not request.user.is_superuser:
        return Response({"error": "You are not authorized to update this profile"}, status=status.HTTP_403_FORBIDDEN)

    data = request.data.copy()
    
    # Handle skills update if present
    if 'skills' in data:
        skills_raw = data['skills']
        if skills_raw:
            try:
                # Try to parse as JSON first (new format)
                if isinstance(skills_raw, str) and (skills_raw.startswith('[') or skills_raw.startswith('{')):
                    skills_with_experience = json.loads(skills_raw)
                elif isinstance(skills_raw, str):
                    # Parse from frontend string format
                    skills_with_experience = parse_skills_from_frontend(skills_raw)
                elif isinstance(skills_raw, list):
                    skills_with_experience = skills_raw
                else:
                    return Response({"error": "Invalid skills format"}, status=status.HTTP_400_BAD_REQUEST)
                
                # Set skills with experience levels
                job_seeker.set_skills_with_experience(skills_with_experience)
                # Remove skills from data to prevent serializer from processing it
                data.pop('skills', None)
                
            except (json.JSONDecodeError, ValueError) as e:
                print(f"Error parsing skills during update: {e}")
                return Response({"error": "Invalid skills format"}, status=status.HTTP_400_BAD_REQUEST)

    # Use the regular serializer for other fields
    serializer = JobSeekerSerializer(job_seeker, data=data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_job_seeker(request, id):
    job_seeker = get_object_or_404(JobSeeker, id=id)
    job_seeker.delete()
    return Response({"message": "Job seeker profile deleted successfully"}, status=status.HTTP_204_NO_CONTENT)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_job_seekers_created_by_user(request):
    job_seekers = JobSeeker.objects.filter(created_by=request.user)
    serializer = JobSeekerSerializer(job_seekers, many=True)
    return Response(serializer.data)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_job_seeker_by_user(request, user_id):
    try:
        # First check if user exists
        user = CustomUser.objects.get(id=user_id)
        print(f"\n\nFound User is: {user.phone_number}\n\n")

        # Then try to get job seeker profile
        job_seeker = JobSeeker.objects.get(user=user)
        
        print(f"\n\n Retrieved job seeker data: {job_seeker}\n\n")
        
        serializer = JobSeekerSerializer(job_seeker)
        return Response(serializer.data)
    
    except CustomUser.DoesNotExist:
        return Response(
            {"error": f"User with id {user_id} does not exist"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except JobSeeker.DoesNotExist:
        return Response(
            {"error": "This user is not registered as a job seeker"}, 
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        print(f"Error in get_job_seeker_by_user: {str(e)}")
        return Response(
            {"error": "An error occurred while fetching job seeker data"}, 
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

# Enhanced user details views
from rest_framework import permissions
from .serializers import CustomUserSerializer

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_user_details(request):
    try:
        # Get the logged-in user's job seeker and custom user details
        user = request.user
        job_seeker = JobSeeker.objects.get(user=user)
        
        # Serialize the data
        custom_user_serializer = CustomUserSerializer(user)
        job_seeker_serializer = JobSeekerSerializer(job_seeker)
        
        print(f"\n\n Retrieved custom user data: {custom_user_serializer.data}\n\n")
        print(f"\n\n Retrieved job seeker data: {job_seeker_serializer.data}\n\n")
        
        # Combine both user and job seeker data in the response
        response_data = {
            'custom_user': custom_user_serializer.data,
            'job_seeker': job_seeker_serializer.data
        }
        return Response(response_data, status=status.HTTP_200_OK)
    except JobSeeker.DoesNotExist:
        return Response({'error': 'Job Seeker account does not exist for this user.'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['PUT'])
@permission_classes([permissions.IsAuthenticated])
def update_user_details(request):
    try:
        user = request.user
        job_seeker = JobSeeker.objects.get(user=user)

        # Get the data from request
        custom_user_data = request.data.get('custom_user', {})
        job_seeker_data = request.data.get('job_seeker', {})
        
        # Log the received data for debugging
        print(f"\n\n Submitted custom user data: {custom_user_data}\n\n")
        print(f"\n\n Submitted job seeker data: {job_seeker_data}\n\n")
        
        # Handle skills update in job_seeker_data
        if 'skills' in job_seeker_data:
            skills_raw = job_seeker_data['skills']
            if skills_raw:
                try:
                    # Try to parse skills with experience
                    if isinstance(skills_raw, str) and (skills_raw.startswith('[') or skills_raw.startswith('{')):
                        skills_with_experience = json.loads(skills_raw)
                    elif isinstance(skills_raw, str):
                        skills_with_experience = parse_skills_from_frontend(skills_raw)
                    elif isinstance(skills_raw, list):
                        skills_with_experience = skills_raw
                    else:
                        return Response({
                            'job_seeker_errors': {'skills': 'Invalid skills format'}
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    # Set skills with experience levels
                    job_seeker.set_skills_with_experience(skills_with_experience)
                    job_seeker.save()
                    # Remove skills from data to prevent serializer from processing it
                    job_seeker_data.pop('skills', None)
                    
                except (json.JSONDecodeError, ValueError) as e:
                    print(f"Error parsing skills during update: {e}")
                    return Response({
                        'job_seeker_errors': {'skills': 'Invalid skills format'}
                    }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create serializers with the data
        custom_user_serializer = CustomUserSerializer(user, data=custom_user_data, partial=True)
        job_seeker_serializer = JobSeekerSerializer(job_seeker, data=job_seeker_data, partial=True)
        
        # Validate the data
        custom_user_valid = custom_user_serializer.is_valid()
        job_seeker_valid = job_seeker_serializer.is_valid()
        
        # Check if both are valid
        if custom_user_valid and job_seeker_valid:
            # Save the changes
            custom_user_serializer.save()
            job_seeker_serializer.save()
            
            # Return the updated data
            return Response({
                'custom_user': CustomUserSerializer(user).data,
                'job_seeker': JobSeekerSerializer(job_seeker).data
            }, status=status.HTTP_200_OK)
        else:
            # Return validation errors
            errors = {}
            if not custom_user_valid:
                errors['custom_user_errors'] = custom_user_serializer.errors
            if not job_seeker_valid:
                errors['job_seeker_errors'] = job_seeker_serializer.errors
                
            return Response(errors, status=status.HTTP_400_BAD_REQUEST)
    
    except JobSeeker.DoesNotExist:
        return Response({'error': 'Job Seeker account does not exist for this user.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        # Log the error and return a 500 response
        print(f"Error updating user details: {str(e)}")
        return Response({'error': 'An unexpected error occurred.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Additional utility views for skills management
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def get_job_seeker_skills(request, job_seeker_id=None):
    """
    Get skills with experience levels for a specific job seeker
    """
    try:
        if job_seeker_id:
            job_seeker = get_object_or_404(JobSeeker, id=job_seeker_id)
        else:
            job_seeker = get_object_or_404(JobSeeker, user=request.user)
        
        skills_data = {
            'skills_with_experience': job_seeker.get_skills_with_experience(),
            'skills_display': job_seeker.get_skills_display(),
            'skills_list': job_seeker.get_skills_list()
        }
        
        return Response(skills_data, status=status.HTTP_200_OK)
        
    except JobSeeker.DoesNotExist:
        return Response({'error': 'Job Seeker not found.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"Error getting job seeker skills: {str(e)}")
        return Response({'error': 'An unexpected error occurred.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def update_job_seeker_skills(request):
    """
    Update skills with experience levels for the authenticated job seeker
    Expected format: {'skills': [{'name': 'Python', 'experience': '3-5'}, ...]}
    """
    try:
        job_seeker = get_object_or_404(JobSeeker, user=request.user)
        skills_data = request.data.get('skills', [])
        
        # Validate skills data
        if not isinstance(skills_data, list):
            return Response({'error': 'Skills must be a list of skill objects'}, status=status.HTTP_400_BAD_REQUEST)
        
        for skill in skills_data:
            if not isinstance(skill, dict) or 'name' not in skill or 'experience' not in skill:
                return Response({
                    'error': 'Each skill must be a dictionary with "name" and "experience" keys'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not skill['name'].strip():
                return Response({'error': 'Skill name cannot be empty'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Update skills
        job_seeker.set_skills_with_experience(skills_data)
        job_seeker.save()
        
        # Return updated skills data
        response_data = {
            'message': 'Skills updated successfully',
            'skills_with_experience': job_seeker.get_skills_with_experience(),
            'skills_display': job_seeker.get_skills_display()
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except JobSeeker.DoesNotExist:
        return Response({'error': 'Job Seeker profile not found.'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"Error updating job seeker skills: {str(e)}")
        return Response({'error': 'An unexpected error occurred.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def search_job_seekers_by_skill(request):
    """
    Search job seekers by skill name
    Query parameter: skill_name
    """
    skill_name = request.GET.get('skill_name', '').strip()
    
    if not skill_name:
        return Response({'error': 'skill_name parameter is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Get all job seekers and filter by skill
        job_seekers = JobSeeker.objects.filter(status=True)
        matching_job_seekers = []
        
        for job_seeker in job_seekers:
            skills = job_seeker.get_skills_list()
            # Case-insensitive search
            if any(skill_name.lower() in skill.lower() for skill in skills):
                matching_job_seekers.append(job_seeker)
        
        serializer = JobSeekerSerializer(matching_job_seekers, many=True)
        return Response({
            'count': len(matching_job_seekers),
            'results': serializer.data
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        print(f"Error searching job seekers by skill: {str(e)}")
        return Response({'error': 'An unexpected error occurred.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)