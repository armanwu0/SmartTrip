from datetime import date, timedelta
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor
import re

from django.db import transaction
from rest_framework.decorators import api_view, throttle_classes, permission_classes
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import TripRequest, TripRecommendation, DestinationDetail
from .ai_service import (
    get_travel_recommendations, get_destination_details,
    get_location_suggestions, get_chat_response, get_day_wise_itinerary,
    parse_trip_intent, calculate_trip_budget, normalize_highlights,
)
from .data_services import search_places, get_place_details, get_route_summary, get_weather_for_coordinates
from trips.models import (
    Trip, ItineraryDay, ItineraryItem, Place, Route, Expense,
    AIConversation, SavedTrip,
)
from trips.serializers import (
    TripSerializer, ItineraryDaySerializer, RouteSerializer,
    ExpenseSerializer, SavedTripSerializer,
)
import json


@api_view(['POST'])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def get_recommendations(request):
    """
    Main endpoint: accepts trip preferences, returns AI recommendations.
    """
    try:
        data = request.data

        # Validate required fields
        required_fields = ['user_name', 'budget', 'group_type', 'travel_scope',
                           'num_days', 'departure_location', 'travel_medium', 'destination_style']
        for field in required_fields:
            if field not in data:
                return Response(
                    {'error': f'Missing required field: {field}'},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Save trip request to DB
        trip_request = TripRequest.objects.create(
            user_name=data.get('user_name'),
            budget=data.get('budget'),
            currency=data.get('currency', 'INR'),
            group_type=data.get('group_type'),
            travel_scope=data.get('travel_scope'),
            num_days=int(data.get('num_days', 7)),
            food_preference=data.get('food_preference', ''),
            accommodation=data.get('accommodation', ''),
            departure_location=data.get('departure_location'),
            travel_medium=data.get('travel_medium'),
            destination_style=data.get('destination_style') if isinstance(data.get('destination_style'), str)
                             else ', '.join(data.get('destination_style', []))
        )

        # Get AI recommendations
        ai_recommendations = get_travel_recommendations(data)

        # Save recommendations to DB
        saved_recommendations = []
        for rec in ai_recommendations:
            highlights = normalize_highlights(rec.get('highlights', ''))
            saved_rec = TripRecommendation.objects.create(
                trip_request=trip_request,
                destination_name=rec.get('destination_name', ''),
                country=rec.get('country', ''),
                budget_category=rec.get('budget_category', 'moderate'),
                summary=rec.get('summary', ''),
                highlights=' | '.join(highlights),
                estimated_cost=rec.get('estimated_cost', ''),
                best_time=rec.get('best_time', '')
            )
            saved_recommendations.append({
                'id': saved_rec.id,
                'destination_name': saved_rec.destination_name,
                'country': saved_rec.country,
                'budget_category': saved_rec.budget_category,
                'summary': saved_rec.summary,
                'highlights': highlights,
                'estimated_cost': saved_rec.estimated_cost,
                'best_time': saved_rec.best_time
            })

        return Response({
            'success': True,
            'trip_id': trip_request.id,
            'user_name': trip_request.user_name,
            'recommendations': saved_recommendations
        })

    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def get_destination_detail(request, recommendation_id):
    """
    Get detailed information for a specific recommendation.
    """
    try:
        recommendation = TripRecommendation.objects.get(id=recommendation_id)
        trip_data = {
            'budget': recommendation.trip_request.budget,
            'currency': recommendation.trip_request.currency,
            'num_days': recommendation.trip_request.num_days,
            'departure_location': recommendation.trip_request.departure_location,
            'travel_medium': recommendation.trip_request.travel_medium,
            'group_type': recommendation.trip_request.group_type,
        }

        # Check if details already exist
        try:
            detail = recommendation.details
            detail_data = {
                'tourist_spots': json.loads(detail.tourist_spots) if detail.tourist_spots else [],
                'local_food': json.loads(detail.local_food) if detail.local_food else [],
                'transport_info': json.loads(detail.transport_info) if detail.transport_info else {},
                'accommodation_options': json.loads(detail.accommodation_options) if detail.accommodation_options else [],
                'travel_tips': json.loads(detail.travel_tips) if detail.travel_tips else [],
                'emergency_info': json.loads(detail.emergency_info) if detail.emergency_info else {}
            }
        except DestinationDetail.DoesNotExist:
            # Generate new details
            ai_details = get_destination_details(recommendation.destination_name, trip_data)

            detail = DestinationDetail.objects.create(
                recommendation=recommendation,
                tourist_spots=json.dumps(ai_details.get('tourist_spots', [])),
                local_food=json.dumps(ai_details.get('local_food', [])),
                transport_info=json.dumps(ai_details.get('transport_info', {})),
                accommodation_options=json.dumps(ai_details.get('accommodation_options', [])),
                travel_tips=json.dumps(ai_details.get('travel_tips', [])),
                emergency_info=json.dumps(ai_details.get('emergency_info', {}))
            )
            detail_data = ai_details

        return Response({
            'success': True,
            'destination_name': recommendation.destination_name,
            'country': recommendation.country,
            'summary': recommendation.summary,
            'estimated_cost': recommendation.estimated_cost,
            'best_time': recommendation.best_time,
            'details': detail_data
        })

    except TripRecommendation.DoesNotExist:
        return Response({'error': 'Recommendation not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def location_autocomplete(request):
    """
    Returns location suggestions for autocomplete.
    """
    query = request.GET.get('q', '')
    suggestions = get_location_suggestions(query)
    return Response({'suggestions': suggestions})


@api_view(['GET'])
def real_place_search(request):
    """Search for actual places using the Google Places API."""
    query = request.GET.get('q', '').strip()
    if not query:
        return Response({'success': False, 'error': 'Query is required.'}, status=status.HTTP_400_BAD_REQUEST)

    result = search_places(query, location=request.GET.get('location'), radius=int(request.GET.get('radius', 5000)))
    if result.get('status') == 'missing_api_key':
        return Response({'success': False, 'status': 'missing_api_key', 'error': 'GOOGLE_MAPS_API_KEY is missing. Set it in the environment to enable real Google places search.', 'results': []}, status=status.HTTP_400_BAD_REQUEST)

    return Response({'success': True, 'results': result.get('results', []), 'source': result.get('source', 'Google Places API')})


@api_view(['GET'])
def real_place_details(request):
    """Return real place details from Google Places."""
    place_id = request.GET.get('place_id', '').strip()
    if not place_id:
        return Response({'success': False, 'error': 'place_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

    result = get_place_details(place_id)
    if result.get('status') == 'missing_api_key':
        return Response({'success': False, 'status': 'missing_api_key', 'error': 'GOOGLE_MAPS_API_KEY is missing. Set it in the environment to enable place details.', 'result': None}, status=status.HTTP_400_BAD_REQUEST)

    return Response({'success': True, 'result': result.get('result'), 'source': result.get('source', 'Google Places API')})


@api_view(['GET'])
def real_route_summary(request):
    """Get route summary with distance and duration between two points."""
    origin = request.GET.get('origin', '').strip()
    destination = request.GET.get('destination', '').strip()
    if not origin or not destination:
        return Response({'success': False, 'error': 'origin and destination are required.'}, status=status.HTTP_400_BAD_REQUEST)

    result = get_route_summary(origin, destination, mode=request.GET.get('mode', 'driving'))
    if result.get('status') == 'missing_api_key':
        return Response({'success': False, 'status': 'missing_api_key', 'error': 'GOOGLE_MAPS_API_KEY is missing. Set it in the environment to enable route calculation.', 'routes': []}, status=status.HTTP_400_BAD_REQUEST)

    return Response({'success': True, 'route': result})


@api_view(['GET'])
def real_weather_summary(request):
    """Return live weather data for supplied coordinates."""
    latitude = request.GET.get('latitude')
    longitude = request.GET.get('longitude')
    if latitude is None or longitude is None:
        return Response({'success': False, 'error': 'latitude and longitude are required.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        latitude = float(latitude)
        longitude = float(longitude)
    except (TypeError, ValueError):
        return Response({'success': False, 'error': 'latitude and longitude must be numeric.'}, status=status.HTTP_400_BAD_REQUEST)

    result = get_weather_for_coordinates(latitude, longitude)
    return Response({'success': True, 'weather': result})


@api_view(['POST'])
def parse_trip_request(request):
    """Parse a natural-language trip requirement into structured context."""
    message = request.data.get('message', '')
    parsed = parse_trip_intent(message)
    return Response({'success': True, 'intent': parsed})


@api_view(['POST'])
def trip_budget_summary(request):
    """Return a verified and estimated budget breakdown for a trip."""
    trip_data = request.data or {}
    summary = calculate_trip_budget(trip_data)
    return Response({'success': True, 'budget': summary})


@api_view(['GET'])
def health_check(request):
    """Health check endpoint."""
    return Response({
        'status': 'ok',
        'app': 'Smart Trip AI',
        'version': '1.0.0',
        'author': 'Arman Ansari'
    })


def _parse_trip_creation_request(message):
    """Return a validated Trip payload only when the message clearly describes a trip plan."""
    if not message or not message.strip():
        return None

    intent = parse_trip_intent(message)
    destination = (intent.get('destination') or '').strip()
    num_days = int(intent.get('num_days') or 1)
    travelers = int(intent.get('travelers') or 1)
    budget = intent.get('budget')
    if not destination or destination.lower() in {'destination', 'current location'}:
        return None

    start_date = date.today()
    end_date = start_date + timedelta(days=max(num_days - 1, 0))
    source = (intent.get('origin') or '').strip() or 'Current Location'
    normalized_budget = Decimal(str(budget or 0)).quantize(Decimal('0.01')) if budget is not None else Decimal('0')

    return {
        'trip_name': f'{destination} {num_days}-day trip',
        'source': source,
        'destination': destination,
        'start_date': start_date,
        'end_date': end_date,
        'number_of_travelers': travelers,
        'total_budget': normalized_budget,
        'currency': intent.get('currency') or 'INR',
        'travel_style': 'General',
        'status': 'PLANNED' if normalized_budget > 0 else 'DRAFT',
        'intent': intent,
    }


def _normalized_place_name(value):
    return re.sub(r'[^a-z0-9]+', ' ', str(value or '').lower()).strip()


def _resolve_provider_places(destination, itinerary):
    requested_names = []
    for day in itinerary:
        for name in day.get('recommended_places', []) if isinstance(day, dict) else []:
            if isinstance(name, str) and name.strip() and name.strip() not in requested_names:
                requested_names.append(name.strip())

    if not requested_names:
        return {}

    with ThreadPoolExecutor(max_workers=5) as executor:
        searches = list(executor.map(
            lambda name: search_places(f'{name}, {destination}'),
            requested_names,
        ))

    stop_words = {'the', 'and', 'for', 'with', 'from', 'goa', 'india', 'beach', 'main', 'city', 'centre', 'center', 'popular', 'local', 'market'}
    resolved = {}
    for requested, result in zip(requested_names, searches):
        requested_tokens = set(_normalized_place_name(requested).split()) - stop_words
        for candidate in result.get('results', []) if isinstance(result, dict) else []:
            external_id = candidate.get('place_id') or candidate.get('external_place_id')
            name = candidate.get('name')
            candidate_tokens = set(_normalized_place_name(name).split()) - stop_words
            matching_tokens = requested_tokens.intersection(candidate_tokens)
            required_matches = 1 if len(requested_tokens) <= 1 else 2
            if not external_id or not name or len(matching_tokens) < required_matches:
                continue
            latitude = candidate.get('lat', candidate.get('latitude'))
            longitude = candidate.get('lng', candidate.get('longitude'))
            try:
                latitude = float(latitude) if latitude is not None else None
                longitude = float(longitude) if longitude is not None else None
            except (TypeError, ValueError):
                latitude = longitude = None
            if latitude is not None and longitude is not None and not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
                latitude = longitude = None
            resolved[requested] = {
                'external_place_id': str(external_id),
                'name': str(name)[:200],
                'address': str(candidate.get('address') or '')[:500],
                'latitude': latitude,
                'longitude': longitude,
                'rating': candidate.get('rating'),
                'photo_reference': candidate.get('photo_reference') or '',
                'photo_url': candidate.get('photo_url') or '',
                'source': candidate.get('source') or result.get('source') or '',
            }
            break
    return resolved


def _expense_amount_from_estimate(value, travelers):
    if not value:
        return None
    numbers = re.findall(r'\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?', str(value))
    if not numbers:
        return None
    amounts = [Decimal(number.replace(',', '')) for number in numbers]
    amount = sum(amounts) / len(amounts)
    if 'person' in str(value).lower() or 'traveller' in str(value).lower() or 'traveler' in str(value).lower():
        amount *= travelers
    return amount.quantize(Decimal('0.01'))


def _persist_generated_trip(user, trip_data, itinerary_result, message, history, save_requested=False):
    intent = trip_data['intent']
    itinerary = itinerary_result['itinerary']
    provider = itinerary_result['provider']
    model = itinerary_result['model']
    destination = trip_data['destination']
    real_places = _resolve_provider_places(destination, itinerary)

    route_result = None
    source = trip_data['source']
    if source and source.lower() not in {'current location', 'unknown', 'not specified'}:
        candidate_route = get_route_summary(source, destination, mode='driving')
        if candidate_route.get('status') == 'ok':
            route_result = candidate_route

    reply = (
        f"Generated your {len(itinerary)}-day {destination} itinerary for "
        f"{trip_data['number_of_travelers']} traveler(s). "
        f"Verified places saved: {len(real_places)}. "
        f"{'A provider route was saved.' if route_result else 'A route was not saved because no verified route was available.'}"
    )

    with transaction.atomic():
        trip = Trip.objects.create(
            user=user,
            **{key: value for key, value in trip_data.items() if key != 'intent'},
        )
        place_objects = {}
        for requested, place_data in real_places.items():
            place, _ = Place.objects.get_or_create(
                external_place_id=place_data['external_place_id'],
                defaults={key: value for key, value in place_data.items() if key != 'external_place_id'},
            )
            place_objects[requested] = place

        expenses = []
        for index, day_data in enumerate(itinerary, start=1):
            day_number = int(day_data.get('day') or index)
            if day_number < 1 or day_number > len(itinerary):
                day_number = index
            itinerary_day = ItineraryDay.objects.create(
                trip=trip,
                day_number=day_number,
                date=trip.start_date + timedelta(days=day_number - 1),
                title=str(day_data.get('title') or f'Day {day_number} in {destination}')[:200],
            )
            sequence = 1
            linked_recommendations = set()
            for slot, start_hour in (('morning', 8), ('afternoon', 12), ('evening', 17)):
                activities = day_data.get(slot, [])
                if not isinstance(activities, list):
                    continue
                for activity_index, activity in enumerate(activities):
                    if isinstance(activity, dict):
                        activity_name = activity.get('activity') or activity.get('name') or activity.get('title')
                        activity_start = activity.get('start_time') or f'{start_hour + activity_index:02d}:00'
                        raw_cost = activity.get('estimated_cost') or 0
                    else:
                        activity_name = str(activity)
                        activity_start = f'{start_hour + activity_index:02d}:00'
                        raw_cost = 0
                    activity_name = str(activity_name or '').strip()
                    if not activity_name:
                        continue
                    normalized_activity = _normalized_place_name(activity_name)
                    matched_name = next((
                        name for name in real_places
                        if _normalized_place_name(name) in normalized_activity
                        or normalized_activity in _normalized_place_name(name)
                    ), None)
                    place = place_objects.get(matched_name)
                    if matched_name:
                        linked_recommendations.add(matched_name)
                    try:
                        estimated_cost = Decimal(str(raw_cost)).quantize(Decimal('0.01'))
                    except Exception:
                        estimated_cost = Decimal('0.00')
                    ItineraryItem.objects.create(
                        itinerary_day=itinerary_day,
                        place=place,
                        activity_name=activity_name[:200],
                        start_time=str(activity_start)[:20],
                        sequence_order=sequence,
                        estimated_cost=estimated_cost,
                        travel_time_from_previous=str(day_data.get('approximate_travel_time') or '')[:50] if sequence == 1 else '',
                    )
                    sequence += 1

            recommendations = day_data.get('recommended_places', [])
            if isinstance(recommendations, list):
                for name in recommendations:
                    if not isinstance(name, str) or not name.strip() or name.strip() in linked_recommendations:
                        continue
                    requested_name = name.strip()
                    place = place_objects.get(requested_name)
                    ItineraryItem.objects.create(
                        itinerary_day=itinerary_day,
                        place=place,
                        activity_name=f'Visit {place.name if place else requested_name}'[:200],
                        start_time=f'{min(20, 10 + sequence):02d}:00',
                        sequence_order=sequence,
                    )
                    sequence += 1

            estimated_amount = _expense_amount_from_estimate(
                day_data.get('estimated_daily_cost'),
                trip.number_of_travelers,
            )
            if estimated_amount is not None and estimated_amount > 0:
                expenses.append(Expense.objects.create(
                    trip=trip,
                    user=user,
                    category=Expense.CATEGORY_MISCELLANEOUS,
                    description=f'AI estimated itinerary cost for day {day_number}',
                    amount=estimated_amount,
                    currency=trip.currency,
                    expense_date=itinerary_day.date,
                    source=f'{provider}:{model}',
                    status=Expense.STATUS_ESTIMATED,
                ))

        route = None
        if route_result:
            route = Route.objects.create(
                trip=trip,
                origin=source,
                destination=destination,
                distance=str(route_result.get('distance_text') or ''),
                duration=str(route_result.get('duration_text') or ''),
                transport_mode='driving',
                provider=str(route_result.get('provider') or route_result.get('source') or ''),
                route_data={
                    key: route_result[key]
                    for key in ('coordinates', 'polyline', 'distance_meters', 'duration_seconds')
                    if route_result.get(key) is not None
                },
            )

        saved = None
        if save_requested:
            saved, _ = SavedTrip.objects.get_or_create(user=user, trip=trip)

        AIConversation.objects.create(
            user=user,
            trip=trip,
            user_message=message,
            ai_response=reply,
            action='PLAN_TRIP',
            provider=provider,
            model=model,
            metadata={
                'intent': intent,
                'history': history[-20:] if isinstance(history, list) else [],
                'itinerary_day_count': len(itinerary),
                'real_place_count': len(place_objects),
                'route_saved': route is not None,
            },
        )

    day_rows = ItineraryDay.objects.filter(trip=trip).prefetch_related('items__place').order_by('day_number')
    trip_payload = TripSerializer(trip).data
    try:
        total_budget = float(trip_payload['total_budget'])
        trip_payload['total_budget'] = int(total_budget) if total_budget.is_integer() else total_budget
    except (TypeError, ValueError):
        pass
    return {
        'reply': reply,
        'trip': trip_payload,
        'itinerary': ItineraryDaySerializer(day_rows, many=True).data,
        'routes': RouteSerializer([route] if route else [], many=True).data,
        'expenses': ExpenseSerializer(expenses, many=True).data,
        'saved_trip': SavedTripSerializer(saved).data if saved else None,
    }


@api_view(['POST'])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def ai_chat(request):
    """
    AI Travel Chatbot API Endpoint.
    Supports both generic travel chat and authenticated trip creation from natural-language plans.
    """
    message = request.data.get('message', '')
    history = request.data.get('history', [])
    if not message.strip():
        return Response({'error': 'Message cannot be empty'}, status=status.HTTP_400_BAD_REQUEST)

    if getattr(request.user, 'is_authenticated', False):
        trip_data = _parse_trip_creation_request(message)
        if trip_data:
            num_days = trip_data['intent']['num_days']
            if num_days < 1 or num_days > 30:
                return Response({'success': False, 'error': 'Trip duration must be between 1 and 30 days.'}, status=status.HTTP_400_BAD_REQUEST)

            itinerary_context = {
                'budget': str(trip_data['total_budget']),
                'currency': trip_data['currency'],
                'group_type': request.data.get('group_type', 'travelers'),
                'num_days': num_days,
                'departure_location': trip_data['source'],
                'travel_medium': request.data.get('travel_medium', 'any'),
                'food_preference': request.data.get('food_preference', 'any'),
                'accommodation': request.data.get('accommodation', 'any'),
            }
            itinerary_result = get_day_wise_itinerary(
                trip_data['destination'],
                num_days,
                itinerary_context,
                allow_fallback=False,
                return_metadata=True,
            )
            itinerary = itinerary_result.get('itinerary', []) if itinerary_result else []
            if not itinerary_result or len(itinerary) != num_days or any(not isinstance(day, dict) for day in itinerary):
                return Response({
                    'success': False,
                    'error': 'A verified AI itinerary could not be generated. No trip data was saved; please try again.',
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

            try:
                persisted = _persist_generated_trip(
                    request.user,
                    trip_data,
                    itinerary_result,
                    message,
                    history,
                    save_requested=request.data.get('save_trip') is True,
                )
            except Exception:
                return Response({
                    'success': False,
                    'error': 'The trip could not be completely saved. No partial trip was retained.',
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            return Response({
                'success': True,
                **persisted,
                'created': True,
                'saved': persisted['saved_trip'] is not None,
                'suggestions': ['Open your saved itinerary', 'Review the budget', 'Find nearby places'],
            })

    chat_result = get_chat_response(message, history)
    payload = {
        'success': True,
        'reply': chat_result.get('reply', ''),
        'suggestions': chat_result.get('suggestions', []),
    }
    return Response(payload)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([AnonRateThrottle, UserRateThrottle])
def get_itinerary(request):
    """
    Protected endpoint: generates a structured day-wise itinerary.
    Requires JWT authentication.

    Body (JSON):
        destination_name  str  (required)
        num_days          int  (required, 1-30)
        trip_data         dict (optional, used to personalise output)
    """
    destination_name = request.data.get('destination_name', '').strip()
    num_days_raw = request.data.get('num_days')
    trip_data = request.data.get('trip_data', {})

    # --- Validation ---
    if not destination_name:
        return Response(
            {'error': 'destination_name is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if num_days_raw is None:
        return Response(
            {'error': 'num_days is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        num_days = int(num_days_raw)
        if num_days < 1 or num_days > 30:
            raise ValueError
    except (ValueError, TypeError):
        return Response(
            {'error': 'num_days must be an integer between 1 and 30.'},
            status=status.HTTP_400_BAD_REQUEST
        )

    if not isinstance(trip_data, dict):
        trip_data = {}

    try:
        itinerary = get_day_wise_itinerary(destination_name, num_days, trip_data)
        if not itinerary:
            return Response(
                {'error': 'Could not generate itinerary. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        return Response({
            'success': True,
            'destination_name': destination_name,
            'num_days': num_days,
            'itinerary': itinerary,
        })
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

