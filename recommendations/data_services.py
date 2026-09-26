import os
from urllib.parse import urlencode

import requests
from django.conf import settings


GOOGLE_MAPS_BASE = 'https://maps.googleapis.com/maps/api'
OPEN_METEO_BASE = 'https://api.open-meteo.com/v1'
ORS_BASE = 'https://api.openrouteservice.org'


def get_google_maps_api_key():
    return getattr(settings, 'GOOGLE_MAPS_API_KEY', '') or os.environ.get('GOOGLE_MAPS_API_KEY', '')


def get_ors_api_key():
    return getattr(settings, 'ORS_API_KEY', '') or os.environ.get('ORS_API_KEY', '')


def _ors_geocode(query):
    api_key = get_ors_api_key()
    if not api_key:
        return {'status': 'missing_api_key', 'result': None}
    try:
        response = requests.get(
            f'{ORS_BASE}/geocode/search',
            params={'api_key': api_key, 'text': query, 'size': 1},
            timeout=15,
        )
        response.raise_for_status()
        features = response.json().get('features') or []
        if not features:
            return {'status': 'no_results', 'result': None}
        feature = features[0]
        properties = feature.get('properties') or {}
        coordinates = (feature.get('geometry') or {}).get('coordinates') or []
        place_id = properties.get('gid')
        name = properties.get('name')
        if not place_id or not name or len(coordinates) < 2:
            return {'status': 'invalid_result', 'result': None}
        longitude, latitude = coordinates[:2]
        if not (-180 <= longitude <= 180 and -90 <= latitude <= 90):
            return {'status': 'invalid_result', 'result': None}
        return {
            'status': 'ok',
            'result': {
                'place_id': place_id,
                'name': name,
                'address': properties.get('label') or '',
                'lat': latitude,
                'lng': longitude,
                'rating': None,
                'photo_url': '',
                'photo_reference': '',
                'source': 'OpenRouteService Geocoding',
                'data_status': 'verified',
            },
        }
    except (requests.RequestException, ValueError, TypeError):
        return {'status': 'request_error', 'result': None}


def build_google_photo_url(photo_reference, max_width=800):
    key = get_google_maps_api_key()
    if not photo_reference or not key:
        return ''
    params = urlencode({'maxwidth': max_width, 'photo_reference': photo_reference, 'key': key})
    return f'{GOOGLE_MAPS_BASE}/place/photo?{params}'


def normalize_place(result):
    geometry = result.get('geometry', {}) or {}
    location = geometry.get('location', {}) or {}
    photos = result.get('photos', []) or []
    first_photo = photos[0] if photos else {}
    return {
        'place_id': result.get('place_id'),
        'name': result.get('name'),
        'address': result.get('formatted_address') or result.get('vicinity'),
        'lat': location.get('lat'),
        'lng': location.get('lng'),
        'rating': result.get('rating'),
        'photo_reference': first_photo.get('photo_reference', ''),
        'reviews': result.get('user_ratings_total'),
        'types': result.get('types', []),
        'price_level': result.get('price_level'),
        'opening_hours': result.get('opening_hours', {}).get('open_now') if isinstance(result.get('opening_hours'), dict) else None,
        'phone': result.get('formatted_phone_number'),
        'website': result.get('website'),
        'maps_url': result.get('url'),
        'photo_url': build_google_photo_url(first_photo.get('photo_reference')) if first_photo else '',
        'source': 'Google Places API',
        'data_status': 'verified' if result.get('place_id') else 'estimated',
    }


def google_places_request(endpoint, params):
    api_key = get_google_maps_api_key()
    if not api_key:
        return {'status': 'missing_api_key', 'data': []}

    url = f'{GOOGLE_MAPS_BASE}/{endpoint}'
    payload = {'key': api_key, **params}
    try:
        response = requests.get(url, params=payload, timeout=15)
        response.raise_for_status()
        payload_json = response.json()
        result_status = payload_json.get('status')
        if result_status in {'OK', 'ZERO_RESULTS'}:
            return {'status': 'ok', 'data': payload_json}
        return {'status': str(result_status).lower(), 'data': payload_json}
    except requests.RequestException:
        return {'status': 'request_error', 'data': []}


def place_autocomplete(query, location=None, types='establishment'):  # pragma: no cover - integration helper
    if not query or not query.strip():
        return {'status': 'invalid_query', 'results': []}

    params = {
        'input': query.strip(),
        'types': types,
    }
    if location:
        params['location'] = location
        params['radius'] = 25000

    response = google_places_request('place/autocomplete/json', params)
    if response['status'] != 'ok':
        return {'status': response['status'], 'results': []}

    predictions = response['data'].get('predictions', [])
    results = []
    for item in predictions[:8]:
        results.append({
            'place_id': item.get('place_id'),
            'description': item.get('description'),
            'main_text': item.get('structured_formatting', {}).get('main_text'),
            'secondary_text': item.get('structured_formatting', {}).get('secondary_text'),
            'source': 'Google Places Autocomplete',
            'data_status': 'verified',
        })
    return {'status': 'ok', 'results': results}


def search_places(query, location=None, radius=5000, place_type=None):
    if not query or not query.strip():
        return {'status': 'invalid_query', 'results': []}

    if not get_google_maps_api_key():
        result = _ors_geocode(query.strip())
        return {
            'status': result['status'],
            'results': [result['result']] if result.get('result') else [],
            'source': 'OpenRouteService Geocoding',
        }

    params = {'query': query.strip(), 'fields': 'place_id,name,formatted_address,geometry,types,rating,user_ratings_total,photos,opening_hours,website,url,formatted_phone_number,price_level,price_level'}
    if location:
        params['location'] = location
        params['radius'] = radius
    if place_type:
        params['type'] = place_type

    response = google_places_request('place/textsearch/json', params)
    if response['status'] != 'ok':
        return {'status': response['status'], 'results': [], 'source': 'Google Places API'}

    raw_results = response['data'].get('results', [])
    return {
        'status': 'ok',
        'results': [normalize_place(item) for item in raw_results[:10]],
        'source': 'Google Places API',
    }


def get_place_details(place_id):
    if not place_id:
        return {'status': 'missing_place_id', 'result': None}

    params = {
        'place_id': place_id,
        'fields': 'place_id,name,formatted_address,geometry,types,rating,user_ratings_total,opening_hours,formatted_phone_number,website,url,photos,review,price_level',
    }
    response = google_places_request('place/details/json', params)
    if response['status'] != 'ok':
        return {'status': response['status'], 'result': None, 'source': 'Google Places API'}

    result = response['data'].get('result', {})
    return {
        'status': 'ok',
        'result': normalize_place(result),
        'source': 'Google Places API',
    }


def get_nearby_places(lat, lng, radius=2000, place_type='tourist_attraction'):
    if lat is None or lng is None:
        return {'status': 'missing_coordinates', 'results': []}

    params = {
        'location': f'{lat},{lng}',
        'radius': radius,
        'type': place_type,
    }
    response = google_places_request('place/nearbysearch/json', params)
    if response['status'] != 'ok':
        return {'status': response['status'], 'results': [], 'source': 'Google Places API'}

    return {
        'status': 'ok',
        'results': [normalize_place(item) for item in response['data'].get('results', [])[:8]],
        'source': 'Google Places API',
    }


def get_route_summary(origin, destination, mode='driving'):
    api_key = get_google_maps_api_key()
    if not api_key:
        ors_key = get_ors_api_key()
        if not ors_key:
            return {'status': 'missing_api_key', 'routes': []}

        profiles = {
            'driving': 'driving-car',
            'walking': 'foot-walking',
            'bicycle': 'cycling-regular',
            'two_wheeler': 'driving-car',
        }
        profile = profiles.get(mode)
        if not profile:
            return {'status': 'unsupported_mode', 'routes': []}

        origin_result = _ors_geocode(origin)
        destination_result = _ors_geocode(destination)
        if not origin_result.get('result') or not destination_result.get('result'):
            return {'status': 'geocoding_unavailable', 'routes': []}

        start = [origin_result['result']['lng'], origin_result['result']['lat']]
        end = [destination_result['result']['lng'], destination_result['result']['lat']]
        try:
            response = requests.post(
                f'{ORS_BASE}/v2/directions/{profile}/geojson',
                headers={'Authorization': ors_key, 'Content-Type': 'application/json'},
                json={'coordinates': [start, end]},
                timeout=30,
            )
            response.raise_for_status()
            features = response.json().get('features') or []
            if not features:
                return {'status': 'no_route', 'routes': []}
            feature = features[0]
            summary = feature.get('properties', {}).get('summary') or {}
            distance = summary.get('distance')
            duration = summary.get('duration')
            coordinates = feature.get('geometry', {}).get('coordinates') or []
            if distance is None or duration is None or not coordinates:
                return {'status': 'invalid_result', 'routes': []}
            return {
                'status': 'ok',
                'distance_text': f'{distance / 1000:.1f} km',
                'distance_meters': distance,
                'duration_text': f'{duration / 3600:.1f} hours',
                'duration_seconds': duration,
                'coordinates': coordinates,
                'polyline': None,
                'provider': 'OpenRouteService',
                'source': 'OpenRouteService Directions',
                'data_status': 'verified',
            }
        except (requests.RequestException, ValueError, TypeError):
            return {'status': 'request_error', 'routes': []}

    params = {
        'origin': origin,
        'destination': destination,
        'mode': mode,
        'alternatives': 'true',
        'key': api_key,
    }
    url = f'{GOOGLE_MAPS_BASE}/directions/json'
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        routes = data.get('routes') or []
        if not routes:
            return {'status': data.get('status', 'no_route'), 'routes': []}
        leg_route = routes[0]
        summary = {
            'distance_text': leg_route['legs'][0]['distance']['text'],
            'distance_meters': leg_route['legs'][0]['distance']['value'],
            'duration_text': leg_route['legs'][0]['duration']['text'],
            'duration_seconds': leg_route['legs'][0]['duration']['value'],
            'polyline': leg_route.get('overview_polyline', {}).get('points'),
            'legs': leg_route.get('legs', []),
            'status': 'ok',
            'source': 'Google Routes API',
            'provider': 'Google Routes API',
            'data_status': 'verified',
        }
        return summary
    except requests.RequestException:
        return {'status': 'request_error', 'routes': []}


def get_weather_for_coordinates(latitude, longitude):
    if latitude is None or longitude is None:
        return {'status': 'missing_coordinates', 'forecast': {}}

    params = {
        'latitude': latitude,
        'longitude': longitude,
        'current': 'temperature_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m',
        'hourly': 'temperature_2m,precipitation_probability,weather_code',
        'daily': 'weather_code,temperature_2m_max,temperature_2m_min,precipitation_probability_max',
        'timezone': 'auto',
        'forecast_days': 3,
    }
    url = f'{OPEN_METEO_BASE}/forecast'
    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        return {
            'status': 'ok',
            'source': 'Open-Meteo Weather API',
            'data_status': 'verified',
            'current': data.get('current'),
            'hourly': data.get('hourly'),
            'daily': data.get('daily'),
        }
    except requests.RequestException:
        return {'status': 'request_error', 'forecast': {}}
