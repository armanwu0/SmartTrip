from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import TripRequest, TripRecommendation, DestinationDetail
from .ai_service import get_travel_recommendations, get_destination_details, get_location_suggestions
import json


@api_view(['POST'])
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
            saved_rec = TripRecommendation.objects.create(
                trip_request=trip_request,
                destination_name=rec.get('destination_name', ''),
                country=rec.get('country', ''),
                budget_category=rec.get('budget_category', 'moderate'),
                summary=rec.get('summary', ''),
                highlights=rec.get('highlights', ''),
                estimated_cost=rec.get('estimated_cost', ''),
                best_time=rec.get('best_time', '')
            )
            saved_recommendations.append({
                'id': saved_rec.id,
                'destination_name': saved_rec.destination_name,
                'country': saved_rec.country,
                'budget_category': saved_rec.budget_category,
                'summary': saved_rec.summary,
                'highlights': saved_rec.highlights.split('|') if saved_rec.highlights else [],
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
def health_check(request):
    """Health check endpoint."""
    return Response({
        'status': 'ok',
        'app': 'Smart Trip AI',
        'version': '1.0.0',
        'author': 'Arman Ansari'
    })
