from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.models import User
from django.contrib.auth import login, logout
from rest_framework_simplejwt.tokens import RefreshToken
from .models import UserProfile, SavedTrip, WishlistItem, LoginActivity
from .serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer,
    UserProfileSerializer, UserUpdateSerializer, SavedTripSerializer, WishlistSerializer
)


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    serializer = RegisterSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        tokens = get_tokens_for_user(user)
        return Response({
            'success': True,
            'token': tokens['access'],
            'access': tokens['access'],
            'refresh': tokens['refresh'],
            'tokens': tokens,
            'user': UserSerializer(user).data,
            'message': f'Welcome to Smart Trip AI, {user.first_name or user.username}!'
        }, status=status.HTTP_201_CREATED)
    return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        LoginActivity.objects.create(user=user, status='SUCCESS', ip_address=request.META.get('REMOTE_ADDR'))
        tokens = get_tokens_for_user(user)
        return Response({
            'success': True,
            'token': tokens['access'],
            'access': tokens['access'],
            'refresh': tokens['refresh'],
            'tokens': tokens,
            'user': UserSerializer(user).data
        })
    return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    refresh_token = request.data.get('refresh')
    if refresh_token:
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            pass
    return Response({'success': True, 'message': 'Logged out successfully.'})



@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def profile_view(request):
    user = request.user
    if request.method == 'GET':
        return Response({'success': True, 'user': UserSerializer(user).data})

    # PUT / PATCH - update profile with validated input
    serializer = UserUpdateSerializer(user, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response({'success': True, 'user': UserSerializer(user).data})

    return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_view(request):
    return Response({'success': True, 'user': UserSerializer(request.user).data})


# ---- Saved Trips ----

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def saved_trips_view(request):
    if request.method == 'GET':
        trips = SavedTrip.objects.filter(user=request.user)
        return Response({'success': True, 'trips': SavedTripSerializer(trips, many=True).data})

    # POST - save a new trip
    serializer = SavedTripSerializer(data=request.data)
    if serializer.is_valid():
        trip = serializer.save(user=request.user)
        # Increment travel count
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        profile.travel_count += 1
        profile.save()
        return Response({'success': True, 'trip': SavedTripSerializer(trip).data}, status=status.HTTP_201_CREATED)
    return Response({'success': False, 'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([IsAuthenticated])
def saved_trip_detail(request, trip_id):
    try:
        trip = SavedTrip.objects.get(id=trip_id, user=request.user)
    except SavedTrip.DoesNotExist:
        return Response({'error': 'Trip not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response({'success': True, 'trip': SavedTripSerializer(trip).data})

    if request.method == 'PUT':
        serializer = SavedTripSerializer(trip, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'success': True, 'trip': serializer.data})
        return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    if request.method == 'DELETE':
        trip.delete()
        return Response({'success': True, 'message': 'Trip removed.'})


# ---- Wishlist ----

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def wishlist_view(request):
    if request.method == 'GET':
        items = WishlistItem.objects.filter(user=request.user)
        return Response({'success': True, 'wishlist': WishlistSerializer(items, many=True).data})

    # POST - add to wishlist
    serializer = WishlistSerializer(data=request.data)
    if serializer.is_valid():
        item, created = WishlistItem.objects.get_or_create(
            user=request.user,
            destination_name=serializer.validated_data['destination_name'],
            defaults={'country': serializer.validated_data.get('country', '')}
        )
        return Response({
            'success': True,
            'created': created,
            'item': WishlistSerializer(item).data
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
    return Response({'errors': serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def wishlist_remove(request, item_id):
    try:
        item = WishlistItem.objects.get(id=item_id, user=request.user)
        item.delete()
        return Response({'success': True})
    except WishlistItem.DoesNotExist:
        return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
