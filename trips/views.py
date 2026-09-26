from decimal import Decimal
from django.db import transaction
from django.db.models import Q, Sum, Count, Prefetch
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    Trip, ItineraryDay, ItineraryItem, Place, Route, Expense,
    AIConversation, SavedTrip,
)
from .serializers import (
    TripSerializer, ItineraryDaySerializer, ItineraryItemSerializer,
    RouteSerializer, ExpenseSerializer, AIConversationSerializer,
    SavedTripSerializer,
)


def _trip_for_user(user, trip_id):
    return get_object_or_404(Trip, pk=trip_id, user=user)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def trip_list_create(request):
    if request.method == 'GET':
        trips = Trip.objects.filter(user=request.user).select_related('user').order_by('-created_at')
        serializer = TripSerializer(trips, many=True)
        return Response(serializer.data)

    serializer = TripSerializer(data=request.data)
    if serializer.is_valid():
        trip = serializer.save(user=request.user)
        return Response(TripSerializer(trip).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def trip_detail(request, pk):
    trip = _trip_for_user(request.user, pk)

    if request.method == 'GET':
        return Response(TripSerializer(trip).data)

    if request.method == 'DELETE':
        trip.delete()
        return Response({'success': True, 'message': 'Trip deleted successfully.'})

    serializer = TripSerializer(trip, data=request.data, partial=(request.method == 'PATCH'))
    if serializer.is_valid():
        serializer.save()
        return Response(TripSerializer(trip).data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET','POST'])
@permission_classes([IsAuthenticated])
def itinerary_list_create(request, trip_id):
    trip = _trip_for_user(request.user, trip_id)
    if request.method == 'GET':
        days = ItineraryDay.objects.filter(trip=trip).prefetch_related('items__place').order_by('day_number')
        return Response(ItineraryDaySerializer(days, many=True).data)

    payload = request.data
    day_number = payload.get('day_number', 1)
    day, created = ItineraryDay.objects.get_or_create(trip=trip, day_number=day_number, defaults={'date': payload.get('date'), 'title': payload.get('title', '')})
    if not created and payload.get('title'):
        day.title = payload.get('title')
        day.date = payload.get('date') or day.date
        day.save()

    item_payload = payload.get('item', {})
    if item_payload:
        place = None
        if item_payload.get('place'):
            place_data = item_payload['place']
            place, _ = Place.objects.get_or_create(
                external_place_id=place_data.get('external_place_id', ''),
                defaults={
                    'name': place_data.get('name', ''),
                    'address': place_data.get('address', ''),
                    'latitude': place_data.get('latitude'),
                    'longitude': place_data.get('longitude'),
                    'category': place_data.get('category', 'misc'),
                    'rating': place_data.get('rating'),
                    'photo_url': place_data.get('photo_url', ''),
                    'source': place_data.get('source', ''),
                },
            )
        item = ItineraryItem.objects.create(
            itinerary_day=day,
            place=place,
            activity_name=item_payload.get('activity_name', 'Activity'),
            start_time=item_payload.get('start_time', ''),
            end_time=item_payload.get('end_time', ''),
            sequence_order=item_payload.get('sequence_order', 1),
            estimated_cost=item_payload.get('estimated_cost', 0),
            travel_time_from_previous=item_payload.get('travel_time_from_previous', ''),
            notes=item_payload.get('notes', ''),
        )
        return Response(ItineraryItemSerializer(item).data, status=status.HTTP_201_CREATED)

    return Response(ItineraryDaySerializer(day).data, status=status.HTTP_201_CREATED)


@api_view(['PATCH','DELETE'])
@permission_classes([IsAuthenticated])
def itinerary_item_update_delete(request, pk):
    item = get_object_or_404(ItineraryItem, pk=pk)
    if item.itinerary_day.trip.user != request.user:
        return Response({'detail': 'You do not have permission to modify this itinerary item.'}, status=403)

    if request.method == 'DELETE':
        item.delete()
        return Response({'success': True, 'message': 'Itinerary item deleted.'})

    serializer = ItineraryItemSerializer(item, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def trip_expenses(request, trip_id):
    trip = _trip_for_user(request.user, trip_id)
    expenses = Expense.objects.filter(trip=trip).order_by('-expense_date', '-created_at')
    return Response(ExpenseSerializer(expenses, many=True).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_expense(request, trip_id):
    trip = _trip_for_user(request.user, trip_id)
    payload = request.data.copy()
    payload['trip'] = trip.id
    payload['user'] = request.user.id
    serializer = ExpenseSerializer(data=payload)
    if serializer.is_valid():
        expense = serializer.save(user=request.user, trip=trip)
        return Response(ExpenseSerializer(expense).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH', 'DELETE'])
@permission_classes([IsAuthenticated])
def expense_update_delete(request, pk):
    expense = get_object_or_404(Expense, pk=pk)
    if expense.trip.user != request.user:
        return Response({'detail': 'Not authorized.'}, status=403)

    if request.method == 'DELETE':
        expense.delete()
        return Response({'success': True, 'message': 'Expense removed.'})

    serializer = ExpenseSerializer(expense, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def trip_routes(request, trip_id):
    trip = _trip_for_user(request.user, trip_id)
    routes = Route.objects.filter(trip=trip).order_by('-created_at')
    return Response(RouteSerializer(routes, many=True).data)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def ai_conversations(request):
    if request.method == 'GET':
        qs = AIConversation.objects.filter(user=request.user).select_related('trip').order_by('-created_at')
        return Response(AIConversationSerializer(qs, many=True).data)

    payload = request.data.copy()
    trip_id = payload.get('trip')
    if trip_id:
        trip = _trip_for_user(request.user, trip_id)
        payload['trip'] = trip.id
    payload['user'] = request.user.id
    serializer = AIConversationSerializer(data=payload)
    if serializer.is_valid():
        convo = serializer.save(user=request.user)
        return Response(AIConversationSerializer(convo).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def saved_trip_list_create(request):
    if request.method == 'GET':
        saved = SavedTrip.objects.filter(user=request.user).select_related('trip').order_by('-saved_at')
        return Response({'results': SavedTripSerializer(saved, many=True).data})

    trip_id = request.data.get('trip_id') or request.data.get('trip')
    trip = _trip_for_user(request.user, trip_id)
    obj, created = SavedTrip.objects.get_or_create(user=request.user, trip=trip)
    return Response({'created': created, 'saved': SavedTripSerializer(obj).data}, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def saved_trip_delete(request, pk):
    obj = get_object_or_404(SavedTrip, pk=pk, user=request.user)
    obj.delete()
    return Response({'success': True, 'message': 'Saved trip removed.'})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_summary(request):
    trips = Trip.objects.filter(user=request.user)
    saved_count = SavedTrip.objects.filter(user=request.user).count()
    total_budget = trips.aggregate(total=Sum('total_budget'))['total'] or Decimal('0')
    return Response({
        'user_name': request.user.first_name or request.user.username,
        'total_trips': trips.count(),
        'active_trips': trips.filter(status='ACTIVE').count(),
        'completed_trips': trips.filter(status='COMPLETED').count(),
        'saved_trips': saved_count,
        'total_planned_budget': float(total_budget),
        'recent_trips': TripSerializer(trips.order_by('-created_at')[:5], many=True).data,
        'recent_conversations': AIConversationSerializer(AIConversation.objects.filter(user=request.user).order_by('-created_at')[:5], many=True).data,
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profile_summary(request):
    from accounts.models import UserProfile
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    return Response({
        'user': request.user.first_name or request.user.username,
        'travel_style': getattr(profile, 'travel_style', ''),
        'preferred_activities': getattr(profile, 'preferred_activities', ''),
    })
