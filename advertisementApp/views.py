# Enhanced views.py
from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .serializers import AdvertisementSerializer
from .models import Advertisement
import logging

# Set up logging
logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_advertisement(request):
    try:
        logger.info(f"Creating advertisement by user {request.user.id}")
        serializer = AdvertisementSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            ad = serializer.save()
            logger.info(f"Advertisement created successfully with ID {ad.id}")
            return Response({
                'message': 'Advertisement created successfully',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        else:
            logger.warning(f"Validation errors in create_advertisement: {serializer.errors}")
            return Response({
                'message': 'Failed to create advertisement',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error in create_advertisement: {str(e)}")
        return Response({
            'message': 'An unexpected error occurred',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_all_advertisements(request):
    try:
        # Add filtering options
        status_filter = request.query_params.get('status', None)
        created_by = request.query_params.get('created_by', None)
        
        ads = Advertisement.objects.all()
        
        if status_filter:
            ads = ads.filter(status=status_filter)
            
        if created_by:
            ads = ads.filter(created_by_id=created_by)
        
        # Check for date range filters
        start_after = request.query_params.get('start_after', None)
        end_before = request.query_params.get('end_before', None)
        
        if start_after:
            ads = ads.filter(start_date__gte=start_after)
            
        if end_before:
            ads = ads.filter(end_date__lte=end_before)
            
        # Filter by active status by default (exclude closed advertisements)
        include_closed = request.query_params.get('include_closed', 'false').lower() == 'true'
        if not include_closed:
            ads = ads.exclude(status='closed')
            
        # Add search functionality
        search_query = request.query_params.get('search', None)
        if search_query:
            ads = ads.filter(
                Q(title__icontains=search_query) |
                Q(description__icontains=search_query)
            )
            
        # Order results
        order_by = request.query_params.get('order_by', '-created_at')  # Default: newest first
        ads = ads.order_by(order_by)
        
        # Basic pagination
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))
        start_index = (page - 1) * page_size
        end_index = start_index + page_size
        
        total_count = ads.count()
        ads = ads[start_index:end_index]
        
        serializer = AdvertisementSerializer(ads, many=True, context={'request': request})
        
        return Response({
            'message': 'Advertisements retrieved successfully',
            'count': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size,
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error in get_all_advertisements: {str(e)}")
        return Response({
            'message': 'Failed to retrieve advertisements',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_advertisement_by_id(request, pk):
    try:
        ad = get_object_or_404(Advertisement, pk=pk)
        serializer = AdvertisementSerializer(ad, context={'request': request})
        return Response({
            'message': 'Advertisement retrieved successfully',
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    except Advertisement.DoesNotExist:
        logger.warning(f"Advertisement with ID {pk} not found")
        return Response({
            'message': 'Advertisement not found',
            'error': f'No advertisement exists with ID {pk}'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error in get_advertisement_by_id: {str(e)}")
        return Response({
            'message': 'Failed to retrieve advertisement',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([AllowAny])
def get_advertisement_by_contact(request, contact_info):
    try:
        if not contact_info:
            return Response({
                'message': 'Contact information is required',
                'error': 'Please provide contact information'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        ads = Advertisement.objects.filter(contact_info=contact_info)
        
        if not ads.exists():
            return Response({
                'message': 'No advertisements found',
                'error': f'No advertisements found with contact info: {contact_info}'
            }, status=status.HTTP_404_NOT_FOUND)
            
        serializer = AdvertisementSerializer(ads, many=True, context={'request': request})
        return Response({
            'message': 'Advertisements retrieved successfully',
            'count': ads.count(),
            'data': serializer.data
        }, status=status.HTTP_200_OK)
    except Exception as e:
        logger.error(f"Error in get_advertisement_by_contact: {str(e)}")
        return Response({
            'message': 'Failed to retrieve advertisements',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_advertisement(request, pk):
    try:
        ad = get_object_or_404(Advertisement, pk=pk)
        
        # Check if the user is the creator of the advertisement
        if request.user != ad.created_by:
            logger.warning(f"Unauthorized update attempt on advertisement {pk} by user {request.user.id}")
            return Response({
                'message': 'Permission denied',
                'error': 'You do not have permission to update this advertisement'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if the advertisement is closed
        if ad.status == 'closed':
            return Response({
                'message': 'Advertisement is closed',
                'error': 'Closed advertisements cannot be modified'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        serializer = AdvertisementSerializer(ad, data=request.data, context={'request': request}, partial=True)
        if serializer.is_valid():
            updated_ad = serializer.save()
            logger.info(f"Advertisement {pk} updated successfully by user {request.user.id}")
            return Response({
                'message': 'Advertisement updated successfully',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        else:
            logger.warning(f"Validation errors in update_advertisement: {serializer.errors}")
            return Response({
                'message': 'Failed to update advertisement',
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
    except Advertisement.DoesNotExist:
        logger.warning(f"Advertisement with ID {pk} not found during update")
        return Response({
            'message': 'Advertisement not found',
            'error': f'No advertisement exists with ID {pk}'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error in update_advertisement: {str(e)}")
        return Response({
            'message': 'Failed to update advertisement',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_advertisement(request, pk):
    try:
        ad = get_object_or_404(Advertisement, pk=pk)
        
        # Check if the user is the creator of the advertisement
        if request.user != ad.created_by:
            logger.warning(f"Unauthorized delete attempt on advertisement {pk} by user {request.user.id}")
            return Response({
                'message': 'Permission denied',
                'error': 'You do not have permission to delete this advertisement'
            }, status=status.HTTP_403_FORBIDDEN)
        
        ad_title = ad.title
        ad.delete()
        logger.info(f"Advertisement {pk} '{ad_title}' deleted successfully by user {request.user.id}")
        return Response({
            'message': f"Advertisement '{ad_title}' deleted successfully"
        }, status=status.HTTP_204_NO_CONTENT)
    except Advertisement.DoesNotExist:
        logger.warning(f"Advertisement with ID {pk} not found during delete")
        return Response({
            'message': 'Advertisement not found',
            'error': f'No advertisement exists with ID {pk}'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        logger.error(f"Error in delete_advertisement: {str(e)}")
        return Response({
            'message': 'Failed to delete advertisement',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)