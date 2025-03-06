from rest_framework import status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import Advertisement
from .serializers import AdvertisementSerializer
from django.core.exceptions import ObjectDoesNotExist

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_advertisements(request):
    print(f"[INFO] Attempting to fetch all advertisements...")
    try:
        ads = Advertisement.objects.all()
        print(f"[INFO] Successfully retrieved {ads.count()} advertisements")
        serializer = AdvertisementSerializer(ads, many=True, context={'request': request})
        print(f"[INFO] Serialized all advertisements data")
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        print(f"[ERROR] Error fetching advertisements: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({'message': 'An error occurred while fetching advertisements'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_advertisement_by_id(request, pk):
    print(f"[INFO] Attempting to fetch advertisement with ID: {pk}")
    try:
        ad = Advertisement.objects.get(pk=pk)
        print(f"[INFO] Successfully retrieved advertisement with ID: {pk}")
        serializer = AdvertisementSerializer(ad, context={'request': request})
        print(f"[INFO] Serialized advertisement data")
        return Response(serializer.data, status=status.HTTP_200_OK)
    except ObjectDoesNotExist:
        print(f"[WARNING] Advertisement with ID {pk} not found")
        return Response({'message': 'Advertisement not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"[ERROR] Error fetching advertisement: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({'message': 'An error occurred'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_advertisement(request):
    print(f"[INFO] Attempting to create new advertisement by user: {request.user.id}")
    try:
        # Basic user check - cannot be removed from backend
        if not request.user.is_active:
            print(f"[WARNING] User {request.user.id} is not active. Create advertisement denied.")
            return Response({'message': 'Your account is not active'}, status=status.HTTP_403_FORBIDDEN)
        
        print(f"[INFO] Validating advertisement data...")
        serializer = AdvertisementSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            print(f"[INFO] Advertisement data valid. Creating advertisement...")
            ad = serializer.save()
            print(f"[INFO] Successfully created advertisement with ID: {ad.id}")
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        print(f"[WARNING] Invalid advertisement data: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        print(f"[ERROR] Error creating advertisement: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({'message': 'An error occurred while creating the advertisement'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_advertisement(request, pk):
    print(f"[INFO] Attempting to update advertisement with ID: {pk}")
    try:
        print(f"[INFO] Checking if advertisement with ID {pk} exists...")
        ad = Advertisement.objects.get(pk=pk)
        print(f"[INFO] Advertisement found. Validating update data...")
        serializer = AdvertisementSerializer(ad, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            print(f"[INFO] Update data valid. Saving changes...")
            updated_ad = serializer.save()
            print(f"[INFO] Successfully updated advertisement with ID: {pk}")
            return Response(serializer.data, status=status.HTTP_200_OK)
        
        print(f"[WARNING] Invalid update data: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except ObjectDoesNotExist:
        print(f"[WARNING] Advertisement with ID {pk} not found")
        return Response({'message': 'Advertisement not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"[ERROR] Error updating advertisement: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({'message': 'An error occurred while updating the advertisement'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_advertisement(request, pk):
    print(f"[INFO] Attempting to delete advertisement with ID: {pk}")
    try:
        print(f"[INFO] Checking if advertisement with ID {pk} exists...")
        ad = Advertisement.objects.get(pk=pk)
        print(f"[INFO] Advertisement found. Proceeding with deletion...")
        ad.delete()
        print(f"[INFO] Successfully deleted advertisement with ID: {pk}")
        return Response({'message': 'Advertisement deleted successfully'}, status=status.HTTP_200_OK)
    except ObjectDoesNotExist:
        print(f"[WARNING] Advertisement with ID {pk} not found")
        return Response({'message': 'Advertisement not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        print(f"[ERROR] Error deleting advertisement: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({'message': 'An error occurred while deleting the advertisement'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_advertisements_by_contact(request, contact_info):
    print(f"[INFO] Attempting to fetch advertisements with contact info: {contact_info}")
    try:
        ads = Advertisement.objects.filter(contact_info__iexact=contact_info)
        print(f"[INFO] Successfully retrieved {ads.count()} advertisements with matching contact info")
        serializer = AdvertisementSerializer(ads, many=True, context={'request': request})
        print(f"[INFO] Serialized all matching advertisements data")
        return Response(serializer.data, status=status.HTTP_200_OK)
    except Exception as e:
        print(f"[ERROR] Error fetching advertisements by contact: {str(e)}")
        import traceback
        traceback.print_exc()
        return Response({'message': 'An error occurred while fetching advertisements'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)