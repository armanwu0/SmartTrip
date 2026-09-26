import pytest
from unittest.mock import patch
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APIClient


@pytest.mark.django_db
class TestTripsAPI:
    def setup_method(self):
        self.client = APIClient()

    def _login(self, username='user1', password='pass1234'):
        user = User.objects.create_user(username=username, password=password)
        self.client.force_authenticate(user=user)
        return user

    def test_create_trip_and_retrieve_own_trip(self):
        user = self._login()
        response = self.client.post('/api/trips/', {
            'trip_name': 'Goa Adventure',
            'source': 'Delhi',
            'destination': 'Goa',
            'start_date': '2026-10-01',
            'end_date': '2026-10-05',
            'number_of_travelers': 4,
            'total_budget': 30000,
            'currency': 'INR',
            'travel_style': 'Beach',
            'status': 'PLANNED',
        }, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        trip_id = response.data['id']
        assert response.data['trip_name'] == 'Goa Adventure'
        assert response.data['user'] == user.id

        get_response = self.client.get(f'/api/trips/{trip_id}/')
        assert get_response.status_code == status.HTTP_200_OK
        assert get_response.data['destination'] == 'Goa'

    def test_cannot_access_another_users_trip(self):
        owner = User.objects.create_user(username='owner', password='pass1234')
        other = User.objects.create_user(username='other', password='pass1234')
        from trips.models import Trip, ItineraryDay, ItineraryItem, Place, Route, Expense, AIConversation
        trip = Trip.objects.create(
            user=owner,
            trip_name='Private Trip',
            source='Delhi',
            destination='Manali',
            start_date='2026-11-01',
            end_date='2026-11-04',
            number_of_travelers=2,
            total_budget=20000,
            currency='INR',
            travel_style='Adventure',
            status='DRAFT',
        )
        day = ItineraryDay.objects.create(trip=trip, day_number=1)
        place = Place.objects.create(name='Private Place', external_place_id='provider:private')
        ItineraryItem.objects.create(itinerary_day=day, place=place, activity_name='Private activity')
        Route.objects.create(trip=trip, origin='A', destination='B')
        Expense.objects.create(user=owner, trip=trip, category='Food', amount=100)
        AIConversation.objects.create(user=owner, trip=trip, user_message='Private message')

        self.client.force_authenticate(user=other)
        response = self.client.get(f'/api/trips/{trip.id}/')
        assert response.status_code in {status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND}
        assert self.client.get(f'/api/trips/{trip.id}/itinerary/').status_code == status.HTTP_404_NOT_FOUND
        assert self.client.get(f'/api/trips/{trip.id}/routes/').status_code == status.HTTP_404_NOT_FOUND
        assert self.client.get(f'/api/trips/{trip.id}/expenses/').status_code == status.HTTP_404_NOT_FOUND
        assert self.client.get('/api/trips/ai/conversations/').data == []
        assert self.client.post('/api/trips/saved-trips/', {'trip_id': trip.id}, format='json').status_code == status.HTTP_404_NOT_FOUND

    @staticmethod
    def _generated_itinerary(num_days):
        return {
            'provider': 'GROQ',
            'model': 'openai/gpt-oss-120b',
            'itinerary': [{
                'day': day,
                'morning': ['Visit Baga Beach'],
                'afternoon': ['Explore the local market'],
                'evening': ['Dinner near the coast'],
                'recommended_places': ['Baga Beach'],
                'estimated_daily_cost': '₹2,000–₹3,000 per person',
            } for day in range(1, num_days + 1)],
        }

    @pytest.mark.django_db
    @patch('recommendations.views.get_day_wise_itinerary')
    @patch('recommendations.views.search_places')
    @patch('recommendations.views.get_route_summary')
    def test_ai_chat_persists_complete_trip_and_saved_relation(self, mock_route, mock_places, mock_itinerary):
        user = self._login()
        mock_itinerary.return_value = self._generated_itinerary(5)
        mock_places.return_value = {
            'status': 'ok',
            'source': 'OpenRouteService Geocoding',
            'results': [{
                'place_id': 'whosonfirst:venue:123',
                'name': 'Baga Beach',
                'address': 'Baga, Goa, India',
                'lat': 15.56,
                'lng': 73.75,
                'source': 'OpenRouteService Geocoding',
            }],
        }
        mock_route.return_value = {
            'status': 'ok',
            'provider': 'OpenRouteService',
            'distance_text': '1.2 km',
            'duration_text': '8 minutes',
            'distance_meters': 1200,
            'duration_seconds': 480,
            'coordinates': [[73.75, 15.56], [73.76, 15.57]],
        }

        response = self.client.post('/api/chat/', {
            'message': 'Plan a 5 day trip from Delhi to Goa for 4 people under ₹30,000.',
            'save_trip': True,
        }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['trip']['destination'] == 'Goa'
        trip_id = response.data['trip']['id']
        from trips.models import Trip, ItineraryDay, ItineraryItem, Place, Route, Expense, AIConversation, SavedTrip
        trip = Trip.objects.get(pk=trip_id, user=user)
        assert ItineraryDay.objects.filter(trip=trip).count() == 5
        assert ItineraryItem.objects.filter(itinerary_day__trip=trip).count() == 15
        assert Place.objects.filter(external_place_id='whosonfirst:venue:123').count() == 1
        place = Place.objects.get(external_place_id='whosonfirst:venue:123')
        assert (place.latitude, place.longitude, place.source) == (15.56, 73.75, 'OpenRouteService Geocoding')
        assert Route.objects.filter(trip=trip, provider='OpenRouteService').count() == 1
        assert Expense.objects.filter(trip=trip, user=user, status='ESTIMATED').count() == 5
        conversation = AIConversation.objects.get(trip=trip, user=user)
        assert conversation.provider == 'GROQ'
        assert conversation.user_message.startswith('Plan a 5 day trip from Delhi to Goa')
        assert SavedTrip.objects.filter(trip=trip, user=user).count() == 1
        assert response.data['saved'] is True

    @pytest.mark.django_db
    @patch('recommendations.views.get_day_wise_itinerary')
    @patch('recommendations.views.search_places')
    @patch('recommendations.views.get_route_summary')
    @patch('recommendations.views.ItineraryItem.objects.create', side_effect=RuntimeError('write failed'))
    def test_ai_trip_rolls_back_when_itinerary_item_persistence_fails(self, _item_create, mock_route, mock_places, mock_itinerary):
        self._login()
        mock_itinerary.return_value = self._generated_itinerary(2)
        mock_places.return_value = {'status': 'ok', 'source': 'ORS', 'results': []}
        mock_route.return_value = {'status': 'no_route', 'routes': []}

        response = self.client.post('/api/chat/', {
            'message': 'Plan a 2 day Goa trip for 2 people under ₹10,000.'
        }, format='json')

        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        from trips.models import Trip, ItineraryDay, AIConversation, Expense, Route, SavedTrip
        assert Trip.objects.count() == 0
        assert ItineraryDay.objects.count() == 0
        assert AIConversation.objects.count() == 0
        assert Expense.objects.count() == 0
        assert Route.objects.count() == 0
        assert SavedTrip.objects.count() == 0

    def test_ai_chat_creates_real_trip_from_natural_language(self):
        from trips.models import Trip
        with patch('recommendations.views.get_day_wise_itinerary', return_value=self._generated_itinerary(5)), \
             patch('recommendations.views.search_places', return_value={'status': 'unavailable', 'results': []}), \
             patch('recommendations.views.get_route_summary', return_value={'status': 'missing_api_key', 'routes': []}):
            user = self._login()
            response = self.client.post('/api/chat/', {
                'message': 'Plan a 5 day Goa trip for 4 people under ₹30,000.'
            }, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        trip = response.data.get('trip')
        assert trip is not None
        assert trip['destination'] == 'Goa'
        assert trip['number_of_travelers'] == 4
        assert trip['total_budget'] == 30000
        assert trip['user'] == user.id
        assert Trip.objects.filter(pk=trip['id'], user=user).exists()
        assert response.data['created'] is True
