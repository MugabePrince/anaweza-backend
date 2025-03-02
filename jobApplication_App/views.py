from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction, IntegrityError
from django.utils import timezone
import logging

from job_seeker.models import JobSeeker
from job_offer_app.models import JobOffer
from .models import Application
from .serializers import ApplicationSerializer

# Set up logger
logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_application(request):
    """Create a new application for a job offer"""
    try:
        # Log the request
        logger.info(f"Application creation attempt by user {request.user.id}")
        
        # Check if the user has a job seeker profile
        try:
            job_seeker = JobSeeker.objects.get(user=request.user)
        except JobSeeker.DoesNotExist:
            logger.error(f"User {request.user.id} does not have a job seeker profile")
            return Response(
                {'error': 'You must complete your job seeker profile before applying'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate job offer ID - Check both job_offer and job_offer_id fields
        job_offer_id = request.data.get('job_offer') or request.data.get('job_offer_id')
        print(f"\n\n Submitted Job Offer ID: {job_offer_id}\n\n")
        if not job_offer_id:
            logger.error("Missing job offer ID in request data")
            return Response(
                {'error': 'Job offer ID is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Get job offer
        try:
            job_offer = JobOffer.objects.get(id=job_offer_id)
        except JobOffer.DoesNotExist:
            logger.error(f"Job offer with ID {job_offer_id} does not exist")
            return Response(
                {'error': f"Job offer with ID {job_offer_id} does not exist"},
                status=status.HTTP_404_NOT_FOUND
            )
        except ValueError:
            logger.error(f"Invalid job offer ID format: {job_offer_id}")
            return Response(
                {'error': f"Invalid job offer ID format: {job_offer_id}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check job status
        if job_offer.status not in ['active', 'draft']:
            logger.error(f"Cannot apply to job with status '{job_offer.status}'")
            return Response(
                {'error': f"Cannot apply to a job that is {job_offer.status}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check deadline
        current_date = timezone.now().date()
        if job_offer.deadline < current_date:
            days_passed = (current_date - job_offer.deadline).days
            logger.error(f"Application deadline has passed for job offer {job_offer_id} ({days_passed} days ago)")
            return Response(
                {'error': f"The application deadline for this job has passed {days_passed} days ago"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if already applied
        existing_application = Application.objects.filter(user=request.user, job_offer=job_offer).first()
        if existing_application:
            logger.error(f"User {request.user.id} has already applied for job offer {job_offer_id} with status {existing_application.status}")
            return Response(
                {'error': f"You have already applied for this job (Status: {existing_application.status})"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create the application directly without using serializer for validation
        with transaction.atomic():
            # Create application instance directly
            application = Application.objects.create(
                user=request.user,
                job_offer=job_offer,
                job_seeker=job_seeker
            )
            
            # Add optional fields if present
            if 'cover_letter' in request.data:
                application.cover_letter = request.data['cover_letter']
                
            if 'resume' in request.FILES:
                application.resume = request.FILES['resume']
                
            if 'additional_documents' in request.data:
                application.additional_documents = request.data['additional_documents']
            
            # Save the application with all fields
            application.save()
            
            # Use serializer only for output formatting
            serializer = ApplicationSerializer(application)
            
            # Return a detailed success response
            return Response({
                'id': application.id,
                'message': 'Application submitted successfully',
                'job_title': job_offer.title,
                'company': job_offer.company_name or 'Not specified',
                'status': application.status,
                'applied_at': application.applied_at
            }, status=status.HTTP_201_CREATED)
            
                 
    except IntegrityError as e:
        error_msg = str(e)
        logger.error(f"Database integrity error: {error_msg}")
        if "unique constraint" in error_msg.lower() or "duplicate key" in error_msg.lower():
            return Response(
                {'error': "You have already applied for this job"},
                status=status.HTTP_409_CONFLICT
            )
        return Response(
            {'error': "Database error occurred while creating application"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    except Exception as e:
        logger.exception(f"Unexpected error in create_application: {str(e)}")
        return Response(
            {'error': 'An unexpected error occurred'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )





@api_view(['GET'])
@permission_classes([IsAuthenticated, IsAdminUser])
def get_all_applications(request):
    """Get all applications (admin only)"""
    try:
        logger.info(f"Admin user {request.user.id} requesting all applications")

        # Optional filters
        status_filter = request.query_params.get('status')
        job_offer_filter = request.query_params.get('job_offer')
        
        # Start with all applications
        applications = Application.objects.all()
        
        # Apply filters if provided
        if status_filter:
            applications = applications.filter(status=status_filter)
            
        if job_offer_filter:
            applications = applications.filter(job_offer_id=job_offer_filter)
            
        # Order by most recent first
        applications = applications.order_by('-applied_at')
        
        # Serialize the data
        serializer = ApplicationSerializer(applications, many=True)
        
        return Response({
            'count': applications.count(),
            'results': serializer.data
        })

    except Exception as e:
        logger.exception(f"Error retrieving all applications: {str(e)}")
        return Response(
            {'error': 'An error occurred while retrieving applications'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_application(request, pk):
    """Get details of a specific application"""
    try:
        # Get application
        try:
            application = Application.objects.get(id=pk)
        except Application.DoesNotExist:
            logger.error(f"Application with ID {pk} not found")
            return Response(
                {'error': 'Application not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check authorization - only the applicant or job poster can view
        if application.user != request.user and (hasattr(application.job_offer, 'created_by') and application.job_offer.created_by != request.user):
            if not request.user.is_staff:  # Allow admins to access
                logger.warning(f"User {request.user.id} attempted unauthorized access to application {pk}")
                return Response(
                    {'error': 'You do not have permission to view this application'},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Serialize and return the data
        serializer = ApplicationSerializer(application)
        logger.info(f"Application {pk} details retrieved by user {request.user.id}")
        return Response(serializer.data)
        
    except Exception as e:
        logger.exception(f"Error retrieving application: {str(e)}")
        return Response(
            {'error': 'An error occurred while retrieving application details'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_application(request, pk):
    """Update an existing application"""
    try:
        # Get the application
        try:
            application = Application.objects.get(id=pk)
        except Application.DoesNotExist:
            logger.error(f"Application with ID {pk} not found")
            return Response(
                {'error': 'Application not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check authorization - only the applicant can update their application
        if application.user != request.user:
            logger.warning(f"User {request.user.id} attempted to update application {pk} belonging to user {application.user.id}")
            return Response(
                {'error': 'You do not have permission to update this application'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if application can be updated (can't update if not in pending or reviewing status)
        if application.status not in ['pending', 'reviewing']:
            logger.error(f"Cannot update application with status '{application.status}'")
            return Response(
                {'error': f"Cannot update application with status '{application.status}'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Process update
        with transaction.atomic():
            # Create update data dictionary
            update_data = {}
            
            # Add fields that can be updated
            if 'cover_letter' in request.data:
                update_data['cover_letter'] = request.data['cover_letter']
                
            if 'resume' in request.FILES:
                update_data['resume'] = request.FILES['resume']
                
            if 'additional_documents' in request.data:
                update_data['additional_documents'] = request.data['additional_documents']
            
            serializer = ApplicationSerializer(
                application,
                data=update_data,
                partial=True,
                context={'request': request}
            )
            
            if serializer.is_valid():
                updated_application = serializer.save()
                logger.info(f"Application {pk} updated by user {request.user.id}")
                
                return Response({
                    'message': 'Application updated successfully',
                    'status': updated_application.status,
                    'updated_at': updated_application.updated_at
                })
            else:
                # Format validation errors for better readability
                error_details = {}
                for field, errors in serializer.errors.items():
                    if isinstance(errors, list) and errors:
                        error_details[field] = errors[0]
                    else:
                        error_details[field] = str(errors)
                
                error_message = "; ".join([f"{field}: {error}" for field, error in error_details.items()])
                logger.error(f"Application update validation failed: {error_message}")
                
                return Response(
                    {'error': error_message, 'details': serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
    except Exception as e:
        logger.exception(f"Error updating application: {str(e)}")
        return Response(
            {'error': 'An error occurred while updating the application'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_application(request, pk):
    """Delete an application"""
    try:
        # Get the application
        try:
            application = Application.objects.get(id=pk)
        except Application.DoesNotExist:
            logger.error(f"Application with ID {pk} not found")
            return Response(
                {'error': 'Application not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check authorization - only the applicant can delete their application or an admin
        if application.user != request.user and not request.user.is_staff:
            logger.warning(f"User {request.user.id} attempted to delete application {pk} belonging to user {application.user.id}")
            return Response(
                {'error': 'You do not have permission to delete this application'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if application can be deleted (can't delete if not in pending, rejected, or withdrawn status)
        if application.user == request.user and application.status not in ['pending', 'rejected', 'withdrawn']:
            logger.error(f"Cannot delete application with status '{application.status}'")
            return Response(
                {'error': f"Cannot delete application with status '{application.status}'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Delete application
        application.delete()
        logger.info(f"Application {pk} deleted by user {request.user.id}")
        
        return Response({
            'message': 'Application deleted successfully'
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.exception(f"Error deleting application: {str(e)}")
        return Response(
            {'error': 'An error occurred while deleting the application'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_application_status(request, pk):
    """Update application status"""
    try:
        # Get the application
        try:
            application = Application.objects.get(id=pk)
        except Application.DoesNotExist:
            logger.error(f"Application with ID {pk} not found")
            return Response(
                {'error': 'Application not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check authorization - only the job offer creator or admin can update status (except for withdraw)
        job_offer = application.job_offer
        is_job_creator = hasattr(job_offer, 'created_by') and job_offer.created_by == request.user
        
        new_status = request.data.get('status')
        if not new_status:
            logger.error("Missing status in request data")
            return Response(
                {'error': 'Status is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        # Applicants can only withdraw their applications
        if application.user == request.user and new_status != 'withdrawn':
            logger.warning(f"User {request.user.id} attempted to change their application {pk} to status {new_status}")
            return Response(
                {'error': 'You can only withdraw your application, not change its status'},
                status=status.HTTP_403_FORBIDDEN
            )
            
        # Job creators can update to any status except withdrawn
        if not is_job_creator and not request.user.is_staff and application.user != request.user:
            logger.warning(f"User {request.user.id} attempted to update status of application {pk}")
            return Response(
                {'error': 'You do not have permission to update this application status'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Validate the new status
        if new_status not in [choice[0] for choice in Application.STATUS_CHOICES]:
            logger.error(f"Invalid status: {new_status}")
            return Response(
                {'error': f"Invalid status. Must be one of {[choice[0] for choice in Application.STATUS_CHOICES]}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check for specific status transition validations
        if application.status == 'withdrawn' and application.user != request.user:
            logger.error(f"Cannot change status of withdrawn application")
            return Response(
                {'error': 'Cannot change status of withdrawn application'},
                status=status.HTTP_400_BAD_REQUEST
            )
            
        if application.status == 'accepted' and new_status not in ['rejected', 'withdrawn']:
            logger.error(f"Cannot change status from accepted to {new_status}")
            return Response(
                {'error': f"Cannot change status from accepted to {new_status}"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update application status
        with transaction.atomic():
            application.status = new_status
            
            # Record feedback if provided
            if 'feedback' in request.data:
                application.feedback = request.data['feedback']
            
            # Record reviewer info if job creator or admin
            if is_job_creator or request.user.is_staff:
                application.reviewed_by = request.user
                application.reviewed_at = timezone.now()
            
            application.save()
            
        logger.info(f"Application {pk} status updated to {new_status} by user {request.user.id}")
        
        return Response({
            'message': f'Application status updated to {new_status}',
            'status': new_status,
            'updated_at': application.updated_at
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.exception(f"Error updating application status: {str(e)}")
        return Response(
            {'error': 'An error occurred while updating the application status'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def accept_application(request, pk):
    """Accept an application"""
    try:
        # Get the application
        try:
            application = Application.objects.get(id=pk)
        except Application.DoesNotExist:
            logger.error(f"Application with ID {pk} not found")
            return Response(
                {'error': 'Application not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check authorization - only the job offer creator or admin can accept application
        job_offer = application.job_offer
        is_job_creator = hasattr(job_offer, 'created_by') and job_offer.created_by == request.user
        
        if not is_job_creator and not request.user.is_staff:
            logger.warning(f"User {request.user.id} attempted to accept application {pk}")
            return Response(
                {'error': 'You do not have permission to accept this application'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if application can be accepted (can't accept withdrawn applications)
        if application.status == 'withdrawn':
            logger.error(f"Cannot accept withdrawn application")
            return Response(
                {'error': 'Cannot accept withdrawn application'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update application status
        with transaction.atomic():
            application.status = 'accepted'
            
            # Record feedback if provided
            if 'feedback' in request.data:
                application.feedback = request.data['feedback']
            
            # Record reviewer info
            application.reviewed_by = request.user
            application.reviewed_at = timezone.now()
            
            application.save()
            
        logger.info(f"Application {pk} accepted by user {request.user.id}")
        
        return Response({
            'message': 'Application accepted successfully',
            'status': 'accepted',
            'updated_at': application.updated_at
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.exception(f"Error accepting application: {str(e)}")
        return Response(
            {'error': 'An error occurred while accepting the application'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def reject_application(request, pk):
    """Reject an application"""
    try:
        # Get the application
        try:
            application = Application.objects.get(id=pk)
        except Application.DoesNotExist:
            logger.error(f"Application with ID {pk} not found")
            return Response(
                {'error': 'Application not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check authorization - only the job offer creator or admin can reject application
        job_offer = application.job_offer
        is_job_creator = hasattr(job_offer, 'created_by') and job_offer.created_by == request.user
        
        if not is_job_creator and not request.user.is_staff:
            logger.warning(f"User {request.user.id} attempted to reject application {pk}")
            return Response(
                {'error': 'You do not have permission to reject this application'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if application can be rejected (can't reject withdrawn applications)
        if application.status == 'withdrawn':
            logger.error(f"Cannot reject withdrawn application")
            return Response(
                {'error': 'Cannot reject withdrawn application'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update application status
        with transaction.atomic():
            application.status = 'rejected'
            
            # Record feedback if provided
            if 'feedback' in request.data:
                application.feedback = request.data['feedback']
            
            # Record reviewer info
            application.reviewed_by = request.user
            application.reviewed_at = timezone.now()
            
            application.save()
            
        logger.info(f"Application {pk} rejected by user {request.user.id}")
        
        return Response({
            'message': 'Application rejected successfully',
            'status': 'rejected',
            'updated_at': application.updated_at
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.exception(f"Error rejecting application: {str(e)}")
        return Response(
            {'error': 'An error occurred while rejecting the application'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def shortlist_application(request, pk):
    """Shortlist an application"""
    try:
        # Get the application
        try:
            application = Application.objects.get(id=pk)
        except Application.DoesNotExist:
            logger.error(f"Application with ID {pk} not found")
            return Response(
                {'error': 'Application not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check authorization - only the job offer creator or admin can shortlist application
        job_offer = application.job_offer
        is_job_creator = hasattr(job_offer, 'created_by') and job_offer.created_by == request.user
        
        if not is_job_creator and not request.user.is_staff:
            logger.warning(f"User {request.user.id} attempted to shortlist application {pk}")
            return Response(
                {'error': 'You do not have permission to shortlist this application'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if application can be shortlisted (can't shortlist withdrawn or rejected applications)
        if application.status in ['withdrawn', 'rejected']:
            logger.error(f"Cannot shortlist application with status {application.status}")
            return Response(
                {'error': f'Cannot shortlist application with status {application.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update application status
        with transaction.atomic():
            application.status = 'shortlisted'
            
            # Record feedback if provided
            if 'feedback' in request.data:
                application.feedback = request.data['feedback']
            
            # Record reviewer info
            application.reviewed_by = request.user
            application.reviewed_at = timezone.now()
            
            application.save()
            
        logger.info(f"Application {pk} shortlisted by user {request.user.id}")
        
        return Response({
            'message': 'Application shortlisted successfully',
            'status': 'shortlisted',
            'updated_at': application.updated_at
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.exception(f"Error shortlisting application: {str(e)}")
        return Response(
            {'error': 'An error occurred while shortlisting the application'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def withdraw_application(request, pk):
    """Withdraw an application"""
    try:
        # Get the application
        try:
            application = Application.objects.get(id=pk)
        except Application.DoesNotExist:
            logger.error(f"Application with ID {pk} not found")
            return Response(
                {'error': 'Application not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check authorization - only the applicant can withdraw their application
        if application.user != request.user:
            logger.warning(f"User {request.user.id} attempted to withdraw application {pk} belonging to user {application.user.id}")
            return Response(
                {'error': 'You do not have permission to withdraw this application'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Check if application can be withdrawn (can't withdraw if already accepted or rejected)
        if application.status in ['accepted', 'rejected', 'withdrawn']:
            logger.error(f"Cannot withdraw application with status {application.status}")
            return Response(
                {'error': f'Cannot withdraw application with status {application.status}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update application status
        application.status = 'withdrawn'
        application.save()
        
        logger.info(f"Application {pk} withdrawn by user {request.user.id}")
        
        return Response({
            'message': 'Application withdrawn successfully',
            'status': 'withdrawn',
            'updated_at': application.updated_at
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.exception(f"Error withdrawing application: {str(e)}")
        return Response(
            {'error': 'An error occurred while withdrawing the application'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_applications(request):
    """Get all applications for the authenticated user"""
    try:
        # Optional filter by status
        status_filter = request.query_params.get('status')
        
        # Get applications
        applications = Application.objects.filter(user=request.user)
        
        # Apply status filter if provided
        if status_filter and status_filter.lower() != 'all':
            applications = applications.filter(status=status_filter)
        
        # Order by most recent first
        applications = applications.order_by('-applied_at')
        
        # Serialize the data
        serializer = ApplicationSerializer(applications, many=True)
        
        logger.info(f"Retrieved {applications.count()} applications for user {request.user.id}")
        
        return Response({
            'count': applications.count(),
            'results': serializer.data
        })
        
    except Exception as e:
        logger.exception(f"Error retrieving user applications: {str(e)}")
        return Response(
            {'error': 'An error occurred while retrieving your applications'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_job_offer_applications(request):
    """Get all applications for job offers created by the authenticated user"""
    try:
        # Optional filter by status
        status_filter = request.query_params.get('status')
        job_offer_filter = request.query_params.get('job_offer')
        
        # Get job offers created by the user
        job_offers = JobOffer.objects.filter(created_by=request.user)
        
        # Get applications for those job offers
        applications = Application.objects.filter(job_offer__in=job_offers)
        
        # Apply status filter if provided
        if status_filter and status_filter.lower() != 'all':
            applications = applications.filter(status=status_filter)
            
        # Apply job offer filter if provided
        if job_offer_filter:
            applications = applications.filter(job_offer_id=job_offer_filter)
        
        # Order by most recent first
        applications = applications.order_by('-applied_at')
        
        # Serialize the data
        serializer = ApplicationSerializer(applications, many=True)
        
        logger.info(f"Retrieved {applications.count()} applications for job offers created by user {request.user.id}")
        
        return Response({
            'count': applications.count(),
            'results': serializer.data
        })
        
    except Exception as e:
        logger.exception(f"Error retrieving job offer applications: {str(e)}")
        return Response(
            {'error': 'An error occurred while retrieving job offer applications'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_job_offer_applications(request, job_offer_id):
    """Get all applications for a specific job offer"""
    try:
        # Get job offer
        try:
            job_offer = JobOffer.objects.get(id=job_offer_id)
        except JobOffer.DoesNotExist:
            logger.error(f"Job offer with ID {job_offer_id} not found")
            return Response(
                {'error': 'Job offer not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check authorization - only the job offer creator or admin can view applications
        is_job_creator = hasattr(job_offer, 'created_by') and job_offer.created_by == request.user
        
        if not is_job_creator and not request.user.is_staff:
            logger.warning(f"User {request.user.id} attempted to view applications for job offer {job_offer_id}")
            return Response(
                {'error': 'You do not have permission to view applications for this job offer'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Optional filter by status
        status_filter = request.query_params.get('status')
        
        # Get applications
        applications = Application.objects.filter(job_offer=job_offer)
        
        # Apply status filter if provided
        if status_filter and status_filter.lower() != 'all':
            applications = applications.filter(status=status_filter)
        
        # Order by most recent first
        applications = applications.order_by('-applied_at')
        
        # Serialize the data
        serializer = ApplicationSerializer(applications, many=True)
        
        logger.info(f"Retrieved {applications.count()} applications for job offer {job_offer_id}")
        
        return Response({
            'count': applications.count(),
            'results': serializer.data
        })
        
    except Exception as e:
        logger.exception(f"Error retrieving job offer applications: {str(e)}")
        return Response(
            {'error': 'An error occurred while retrieving job offer applications'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
    