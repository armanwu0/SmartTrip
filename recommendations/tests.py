from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.cache import cache
from rest_framework.test import APIClient
from rest_framework import status
from recommendations.ai_service import get_travel_recommendations, generate_cache_key, parse_trip_intent, get_chat_response
from recommendations.data_services import get_route_summary, search_places
from recommendations.views import _resolve_provider_places


class RecommendationIntentParsingTests(TestCase):
    def test_parse_trip_intent_extracts_key_fields(self):
        parsed = parse_trip_intent('Plan a 5 day trip from Delhi to Manali for 4 people under ₹25,000')

        self.assertEqual(parsed['origin'], 'Delhi')
        self.assertEqual(parsed['destination'], 'Manali')
        self.assertEqual(parsed['num_days'], 5)
        self.assertEqual(parsed['travelers'], 4)
        self.assertEqual(parsed['budget'], 25000)
        self.assertEqual(parsed['currency'], 'INR')


class ExternalTravelDataTests(TestCase):
    @patch('recommendations.data_services.get_google_maps_api_key', return_value='')
    @patch('recommendations.data_services.get_ors_api_key', return_value='ors-key')
    @patch('recommendations.data_services.requests.get')
    def test_ors_place_result_requires_provider_id_and_real_coordinates(self, mock_get, _ors_key, _google_key):
        mock_get.return_value.json.return_value = {
            'features': [{
                'properties': {'gid': 'whosonfirst:venue:123', 'name': 'Baga', 'label': 'Baga, Goa'},
                'geometry': {'coordinates': [73.75, 15.56]},
            }]
        }
        mock_get.return_value.raise_for_status.return_value = None

        result = search_places('Baga Beach, Goa')

        self.assertEqual(result['results'][0]['place_id'], 'whosonfirst:venue:123')
        self.assertEqual(result['results'][0]['lat'], 15.56)
        self.assertEqual(result['results'][0]['lng'], 73.75)
        self.assertIsNone(result['results'][0]['rating'])

    @patch('recommendations.data_services.get_google_maps_api_key', return_value='')
    @patch('recommendations.data_services.get_ors_api_key', return_value='ors-key')
    @patch('recommendations.data_services._ors_geocode')
    @patch('recommendations.data_services.requests.post')
    def test_ors_route_returns_provider_distance_duration_and_geometry(self, mock_post, mock_geocode, _ors_key, _google_key):
        mock_geocode.side_effect = [
            {'status': 'ok', 'result': {'lng': 77.2, 'lat': 28.6}},
            {'status': 'ok', 'result': {'lng': 73.8, 'lat': 15.5}},
        ]
        mock_post.return_value.json.return_value = {
            'features': [{
                'properties': {'summary': {'distance': 1000, 'duration': 600}},
                'geometry': {'coordinates': [[77.2, 28.6], [73.8, 15.5]]},
            }]
        }
        mock_post.return_value.raise_for_status.return_value = None

        route = get_route_summary('Delhi, India', 'Goa, India')

        self.assertEqual(route['status'], 'ok')
        self.assertEqual(route['provider'], 'OpenRouteService')
        self.assertEqual(route['distance_meters'], 1000)
        self.assertEqual(route['coordinates'], [[77.2, 28.6], [73.8, 15.5]])

    @patch('recommendations.views.search_places')
    def test_unrelated_provider_match_is_not_saved_as_a_place(self, mock_search):
        mock_search.return_value = {
            'source': 'OpenRouteService Geocoding',
            'results': [{'place_id': 'whosonfirst:region:123', 'name': 'San Martin', 'lat': 15.5, 'lng': 73.8}],
        }

        result = _resolve_provider_places('Goa', [{
            'recommended_places': ["Martin's Corner in Betalbatim"],
        }])

        self.assertEqual(result, {})


class RecommendationThrottlingTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    @patch('recommendations.views.get_chat_response')
    def test_anonymous_rate_limiting(self, mock_chat):
        mock_chat.return_value = {'reply': 'Hello!', 'suggestions': []}

        # Anonymous limit is 10/hour. First 10 calls should succeed or return 200/400.
        for i in range(10):
            response = self.client.post('/api/chat/', {'message': 'Hello'}, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 11th call should return 429 Too Many Requests
        response = self.client.post('/api/chat/', {'message': 'Hello'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_429_TOO_MANY_REQUESTS)

    def test_non_ai_endpoint_unthrottled(self):
        # Health check endpoint is not throttled
        for i in range(12):
            response = self.client.get('/api/health/')
            self.assertEqual(response.status_code, status.HTTP_200_OK)


class RecommendationCachingTests(TestCase):
    def setUp(self):
        cache.clear()
        self.trip_data = {
            'user_name': 'Arman',
            'budget': 'moderate',
            'currency': 'INR',
            'group_type': 'solo',
            'num_days': 7,
            'departure_location': 'Mumbai'
        }

    def test_cache_key_order_insensitivity(self):
        data1 = {'b': 2, 'a': 1, 'nested': {'y': 'val2', 'x': 'val1'}}
        data2 = {'a': 1, 'b': 2, 'nested': {'x': 'val1', 'y': 'val2'}}
        key1 = generate_cache_key('test', data1)
        key2 = generate_cache_key('test', data2)
        self.assertEqual(key1, key2)

    @patch('recommendations.ai_service.get_gemini_client')
    def test_cache_hit_prevents_duplicate_gemini_call(self, mock_client_func):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.text = '''[
            {
                "destination_name": "Manali",
                "country": "India",
                "budget_category": "budget",
                "summary": "Beautiful mountains",
                "highlights": "Snow|Solang",
                "estimated_cost": "20000",
                "best_time": "Oct-Jun"
            }
        ]'''
        mock_client.models.generate_content.return_value = mock_response
        mock_client_func.return_value = mock_client

        # First call: cache miss, calls Gemini
        res1 = get_travel_recommendations(self.trip_data)
        self.assertEqual(len(res1), 1)
        self.assertEqual(res1[0]['destination_name'], 'Manali')
        self.assertEqual(mock_client.models.generate_content.call_count, 1)

        # Second call with identical input: cache hit, Gemini NOT called again
        res2 = get_travel_recommendations(self.trip_data)
        self.assertEqual(res2, res1)
        self.assertEqual(mock_client.models.generate_content.call_count, 1)

    @patch('recommendations.ai_service.get_gemini_client')
    @patch('recommendations.ai_service.call_groq_text', return_value=None)
    def test_failed_response_not_cached(self, _mock_groq, mock_client_func):
        mock_client = MagicMock()
        mock_client.models.generate_content.side_effect = Exception("API rate limit error")
        mock_client_func.return_value = mock_client

        res = get_travel_recommendations(self.trip_data)
        # Should return fallback
        self.assertEqual(len(res), 3)

        # Cache should remain empty for this trip_data key
        key = generate_cache_key('smarttrip:recommendations', self.trip_data)
        self.assertIsNone(cache.get(key))

    @patch('recommendations.ai_service.get_groq_client')
    @patch('recommendations.ai_service.get_gemini_client', return_value=None)
    def test_chat_uses_groq_when_gemini_unavailable(self, mock_gemini, mock_groq):
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(content='A coastal itinerary works well for a short trip.'))]
        )
        mock_groq.return_value = mock_client

        response = get_chat_response('Plan a coastal trip for 3 days')

        self.assertIn('coastal', response['reply'].lower())
        self.assertTrue(any('trip' in item.lower() for item in response.get('suggestions', [])))

    @patch('recommendations.views.get_travel_recommendations')
    def test_recommendations_handle_list_highlights(self, mock_get_travel_recommendations):
        mock_get_travel_recommendations.return_value = [{
            'destination_name': 'Manali',
            'country': 'India',
            'budget_category': 'budget',
            'summary': 'Beautiful mountains',
            'highlights': ['Snow', 'Solang', 'River Rafting'],
            'estimated_cost': '₹20,000',
            'best_time': 'Oct-Jun'
        }]

        client = APIClient()
        response = client.post('/api/recommendations/', {
            'user_name': 'Arman',
            'budget': '20000',
            'group_type': 'solo',
            'travel_scope': 'domestic',
            'num_days': 7,
            'departure_location': 'Mumbai',
            'travel_medium': 'flight',
            'destination_style': 'nature',
        }, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['recommendations'][0]['highlights'], ['Snow', 'Solang', 'River Rafting'])

