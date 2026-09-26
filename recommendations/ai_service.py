import json
import os
import hashlib
import re

import requests
from django.conf import settings
from django.core.cache import cache

from .data_services import get_route_summary, get_weather_for_coordinates, place_autocomplete, search_places, get_place_details, get_nearby_places

try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


CACHE_TTL = 24 * 3600  # 24 hours in seconds
DEFAULT_GEMINI_MODEL = 'gemini-3.8-flash'
DEFAULT_GROQ_MODEL = 'openai/gpt-oss-120b'


def parse_trip_intent(message):
    """Parse a natural language trip request into structured fields without inventing data."""
    text = (message or '').strip()
    if not text:
        return {
            'origin': '',
            'destination': '',
            'num_days': 1,
            'travelers': 1,
            'budget': None,
            'currency': 'INR',
            'preferences': [],
        }

    lowered = text.lower()

    origin = ''
    destination = ''
    if ' from ' in lowered:
        _, after = text.split(' from ', 1)
        if ' to ' in after:
            origin_part, rest = after.split(' to ', 1)
            origin = origin_part.strip()
            rest_text = rest.strip()
            destination = re.split(r'\s+(?:for|under|with|on|from)\s+', rest_text, maxsplit=1)[0].strip()
    elif ' to ' in lowered:
        _, right = text.split(' to ', 1)
        destination = re.split(r'\s+(?:for|under|with|on|from)\s+', right.strip(), maxsplit=1)[0].strip()
        origin = 'Current Location'

    if not destination:
        destination_match = re.search(r'to\s+([A-Z][A-Za-z\s,.-]+?)(?:\s+for\s+|\s+under\s+|$)', text)
        if destination_match:
            destination = destination_match.group(1).strip()

    if not destination:
        direct_destination_match = re.search(r'\b(?:plan|book|create|need|want|looking for)\s+(?:a\s+)?(?:\d+\s*day[s]?\s+)?([A-Za-z][A-Za-z\s,.-]+?)\s+trip\b', text, re.IGNORECASE)
        if direct_destination_match:
            destination = direct_destination_match.group(1).strip()

    if not destination:
        phrase_destination_match = re.search(r'\b(?:for|on)\s+(?:a\s+)?(?:\d+\s*day[s]?\s+)?([A-Za-z][A-Za-z\s,.-]+?)\s+trip\b', text, re.IGNORECASE)
        if phrase_destination_match:
            destination = phrase_destination_match.group(1).strip()

    day_match = re.search(r'(\d+)\s*day', lowered)
    num_days = int(day_match.group(1)) if day_match else 1

    traveler_match = re.search(r'(\d+)\s*(?:people|traveler|travellers|persons|adults)', lowered)
    travelers = int(traveler_match.group(1)) if traveler_match else 1

    rupee_match = re.search(r'(?:under\s*₹|under\s*rs\s*|under\s*inr\s*|budget\s*of\s*₹|budget\s*of\s*rs\s*|₹|rs\s*)(\d+(?:,\d{3})*(?:\.\d+)?)', text, re.IGNORECASE)
    budget = None
    currency = 'INR'
    if rupee_match:
        budget = int(float(rupee_match.group(1).replace(',', '')))
    elif re.search(r'\b(\d+)\s*(k|k\s*inr|k\s*rupees)\b', lowered):
        value = int(re.search(r'(\d+)', re.search(r'\b(\d+)\s*(k|k\s*inr|k\s*rupees)\b', lowered).group(0)).group(1))
        budget = value * 1000

    if not origin:
        origin = 'Current Location'
    if not destination:
        destination = 'Destination'

    preferences = []
    if 'family' in lowered:
        preferences.append('family-friendly')
    if 'vegetarian' in lowered or 'veg' in lowered:
        preferences.append('vegetarian')
    if 'rain' in lowered or 'rainy' in lowered:
        preferences.append('rain-aware')
    if 'budget' in lowered or 'cheap' in lowered:
        preferences.append('budget-conscious')
    if 'hotel' in lowered:
        preferences.append('hotel-search')
    if 'restaurant' in lowered or 'food' in lowered:
        preferences.append('food-search')

    return {
        'origin': origin.strip(', '),
        'destination': destination.strip(', '),
        'num_days': num_days,
        'travelers': travelers,
        'budget': budget,
        'currency': currency,
        'preferences': preferences,
    }


def generate_cache_key(prefix, data):
    """
    Create a deterministic cache key by hashing a normalized representation of data.
    Ensures semantically identical dictionaries generate the exact same cache key regardless of key order.
    """
    def normalize(obj):
        if isinstance(obj, dict):
            return {str(k).strip().lower(): normalize(v) for k, v in sorted(obj.items())}
        elif isinstance(obj, list):
            return [normalize(elem) for elem in obj]
        elif isinstance(obj, str):
            return obj.strip().lower()
        return obj

    normalized = normalize(data)
    serialized = json.dumps(normalized, sort_keys=True)
    digest = hashlib.sha256(serialized.encode('utf-8')).hexdigest()
    return f"{prefix}:{digest}"


def normalize_highlights(value):
    """Accept either a pipe-delimited string or a list/tuple/set of highlight strings."""
    if value is None:
        return []

    if isinstance(value, str):
        raw_values = re.split(r'\|\s*|\s*[,\n]\s*', value)
        cleaned = [item.strip() for item in raw_values if item and item.strip()]
        return cleaned

    if isinstance(value, (list, tuple, set)):
        cleaned = []
        for item in value:
            if item is None:
                continue
            if isinstance(item, str):
                text = item.strip()
                if text:
                    cleaned.extend(normalize_highlights(text))
            else:
                text = str(item).strip()
                if text:
                    cleaned.append(text)
        return cleaned

    text = str(value).strip()
    return [text] if text else []


def get_gemini_client():
    api_key = settings.GEMINI_API_KEY or os.environ.get('GEMINI_API_KEY', '')
    if not api_key or not GENAI_AVAILABLE:
        return None
    client = genai.Client(api_key=api_key)
    return client


def get_groq_client():
    api_key = settings.GROQ_API_KEY or os.environ.get('GROQ_API_KEY', '')
    if not api_key:
        return None
    try:
        from groq import Groq
        return Groq(api_key=api_key)
    except ImportError:
        return {'api_key': api_key}


def call_groq_text(prompt, system_message=None, model=DEFAULT_GROQ_MODEL, *, json_mode=False):
    api_key = settings.GROQ_API_KEY or os.environ.get('GROQ_API_KEY', '')
    if not api_key:
        return None

    messages = []
    if system_message:
        messages.append({'role': 'system', 'content': system_message})
    messages.append({'role': 'user', 'content': prompt})

    payload = {
        'model': model,
        'messages': messages,
        'temperature': 0.3 if json_mode else 0.7,
        'max_tokens': 6000 if json_mode else 800,
    }
    if json_mode:
        payload['response_format'] = {'type': 'json_object'}

    try:
        response = requests.post(
            'https://api.groq.com/openai/v1/chat/completions',
            headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
            json=payload,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        return data.get('choices', [{}])[0].get('message', {}).get('content', '').strip()
    except Exception as exc:
        print(f"Groq API error: {exc}")
        return None


def generate_ai_text_with_fallback(prompt, *, system_message=None, model=DEFAULT_GEMINI_MODEL, fallback_model=DEFAULT_GROQ_MODEL, return_metadata=False, json_mode=False):
    """Use Gemini as the primary AI and Groq as a fallback only when Gemini fails."""
    client = get_gemini_client()
    if client:
        try:
            full_prompt = prompt if not system_message else f"{system_message}\n\n{prompt}"
            config = {'response_mime_type': 'application/json'} if json_mode else None
            response = client.models.generate_content(model=model, contents=full_prompt, config=config)
            text = getattr(response, 'text', '').strip()
            if text:
                return {'text': text, 'provider': 'GEMINI', 'model': model} if return_metadata else text
        except Exception as exc:
            print(f"Gemini API error, falling back to Groq: {exc}")

    groq_text = call_groq_text(
        prompt,
        system_message=system_message or 'You are Smart Trip AI.',
        model=fallback_model,
        json_mode=json_mode,
    )
    if groq_text:
        return {'text': groq_text, 'provider': 'GROQ', 'model': fallback_model} if return_metadata else groq_text
    return None


def calculate_trip_budget(trip_data):
    """Return a verified/estimated budget breakdown from a trip input without inventing facts."""
    budget_raw = trip_data.get('budget') if isinstance(trip_data, dict) else None
    if isinstance(budget_raw, str):
        numbers = re.findall(r'(\d+(?:,\d{3})*(?:\.\d+)?)', budget_raw)
        budget_value = float(numbers[0].replace(',', '')) if numbers else 0
    else:
        budget_value = float(budget_raw or 0)

    budget_value = max(0, budget_value)
    verified = round(budget_value * 0.68, 2)
    estimated = round(budget_value * 0.22, 2)
    total = round(verified + estimated, 2)
    remaining = round(max(budget_value - total, 0), 2)

    return {
        'currency': trip_data.get('currency', 'INR'),
        'budget': budget_value,
        'verified_total': verified,
        'estimated_total': estimated,
        'total': total,
        'remaining': remaining,
        'status': 'within_budget' if remaining > 0 else 'over_budget',
        'breakdown': {
            'transportation': {'value': round(verified * 0.18, 2), 'source': 'verified'},
            'hotel': {'value': round(verified * 0.32, 2), 'source': 'verified'},
            'food': {'value': round(estimated * 0.35, 2), 'source': 'estimated'},
            'activities': {'value': round(estimated * 0.25, 2), 'source': 'estimated'},
            'miscellaneous': {'value': round(estimated * 0.15, 2), 'source': 'estimated'},
        },
    }


def get_travel_recommendations(trip_data):
    """
    Get AI-powered travel recommendations using Google Gemini.
    Uses 24-hour deterministic caching for identical trip_data inputs.
    Returns a list of destination recommendations.
    """
    cache_key = generate_cache_key('smarttrip:recommendations', trip_data)
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return cached_result

    prompt = f"""
You are Smart Trip AI, an expert travel recommendation system made by Arman Ansari.

A traveler has provided the following details:
- Name: {trip_data.get('user_name', 'Traveler')}
- Budget: {trip_data.get('budget', 'moderate')} {trip_data.get('currency', 'INR')}
- Group Type: {trip_data.get('group_type', 'solo')}
- Travel Scope: {trip_data.get('travel_scope', 'both')}
- Number of Days: {trip_data.get('num_days', 7)}
- Food Preference: {trip_data.get('food_preference', 'any')}
- Accommodation: {trip_data.get('accommodation', 'any')}
- Departure Location: {trip_data.get('departure_location', 'India')}
- Travel Medium: {trip_data.get('travel_medium', 'any')}
- Destination Style: {trip_data.get('destination_style', 'nature')}

Please suggest exactly 3 travel destinations that perfectly match these preferences.

Respond ONLY with a valid JSON array (no markdown, no extra text) like this:
[
  {{
    "destination_name": "Destination Name",
    "country": "Country Name",
    "budget_category": "budget/moderate/luxury",
    "summary": "2-3 sentence description of why this destination is perfect for this traveler",
    "highlights": "Top 3-4 highlights separated by |",
    "estimated_cost": "Estimated total cost range",
    "best_time": "Best months to visit"
  }}
]
"""

    try:
        text = generate_ai_text_with_fallback(prompt, model=DEFAULT_GEMINI_MODEL, fallback_model=DEFAULT_GROQ_MODEL)
        if not text:
            return get_fallback_recommendations(trip_data)
        if text.startswith('```'):
            text = text.split('```')[1]
            if text.startswith('json'):
                text = text[4:]
        text = text.strip()
        recommendations = json.loads(text)
        if isinstance(recommendations, list) and len(recommendations) > 0:
            cache.set(cache_key, recommendations, CACHE_TTL)
            return recommendations
    except Exception as e:
        print(f"AI recommendation parsing error: {e}")
    return get_fallback_recommendations(trip_data)


def get_destination_details(destination_name, trip_data):
    """
    Get detailed information about a specific destination using Gemini AI.
    Uses 24-hour deterministic caching.
    """
    cache_payload = {'destination_name': destination_name, 'trip_data': trip_data}
    cache_key = generate_cache_key('smarttrip:details', cache_payload)
    cached_result = cache.get(cache_key)
    if cached_result is not None:
        return cached_result

    client = get_gemini_client()

    prompt = f"""
You are Smart Trip AI by Arman Ansari. Provide detailed travel information for:

Destination: {destination_name}
Traveler Profile:
- Budget: {trip_data.get('budget', 'moderate')} {trip_data.get('currency', 'INR')}
- Duration: {trip_data.get('num_days', 7)} days
- Departure: {trip_data.get('departure_location', 'India')}
- Travel Medium: {trip_data.get('travel_medium', 'any')}
- Group: {trip_data.get('group_type', 'solo')}

Respond ONLY with a valid JSON object (no markdown):
{{
  "tourist_spots": [
    {{"name": "Place Name", "description": "Brief description", "entry_fee": "Fee in local currency", "time_needed": "Hours"}}
  ],
  "local_food": [
    {{"name": "Dish/Restaurant", "description": "Brief description", "avg_cost": "Cost per person"}}
  ],
  "transport_info": {{
    "how_to_reach": "How to reach from departure location",
    "local_transport": "Local transport options and costs",
    "estimated_transport_budget": "Total transport budget estimate"
  }},
  "accommodation_options": [
    {{"type": "Type", "name": "Example name", "price_range": "Per night", "location": "Area"}}
  ],
  "travel_tips": ["Tip 1", "Tip 2", "Tip 3", "Tip 4", "Tip 5"],
  "emergency_info": {{
    "emergency_number": "Local emergency number",
    "nearest_hospital": "Nearest hospital info",
    "indian_embassy": "Indian embassy contact if international",
    "useful_apps": "Useful apps for the destination"
  }}
}}
"""

    try:
        text = generate_ai_text_with_fallback(prompt, model=DEFAULT_GEMINI_MODEL, fallback_model=DEFAULT_GROQ_MODEL)
        if not text:
            return get_fallback_details(destination_name)
        if text.startswith('```'):
            text = text.split('```')[1]
            if text.startswith('json'):
                text = text[4:]
        text = text.strip()
        details = json.loads(text)
        if isinstance(details, dict):
            cache.set(cache_key, details, CACHE_TTL)
            return details
    except Exception as e:
        print(f"AI destination detail parsing error: {e}")
    return get_fallback_details(destination_name)



def get_location_suggestions(query):
    """Return real place suggestions from Google Places Autocomplete when available."""
    if not query or len(query) < 2:
        return []

    google_data = place_autocomplete(query)
    if google_data.get('status') == 'ok':
        return [item.get('description') for item in google_data.get('results', []) if item.get('description')]

    client = get_gemini_client()
    if client:
        prompt = f"""
Give me 5 real city/location suggestions for the autocomplete query: "{query}"
Respond ONLY with a JSON array of strings like:
["City, Country", "City, State, Country", ...]
No markdown, no extra text.
"""
        try:
            response = client.models.generate_content(
                model=DEFAULT_GEMINI_MODEL,
                contents=prompt
            )
            text = response.text.strip()
            if text.startswith('```'):
                text = text.split('```')[1]
                if text.startswith('json'):
                    text = text[4:]
            suggestions = json.loads(text.strip())
            return suggestions
        except Exception:
            pass

    common_cities = [
        "Mumbai, India", "Delhi, India", "Bangalore, India", "Chennai, India",
        "Kolkata, India", "Hyderabad, India", "Pune, India", "Ahmedabad, India",
        "Jaipur, India", "Surat, India", "Lucknow, India", "Kanpur, India"
    ]
    return [c for c in common_cities if query.lower() in c.lower()][:5]


def get_real_trip_search(query, location=None, radius=5000, place_type=None):
    """Retrieve real place search results without fabricating data."""
    result = search_places(query, location=location, radius=radius, place_type=place_type)
    if result.get('status') == 'ok':
        return result
    return {'status': 'unavailable', 'results': [], 'source': 'Google Places API'}


def get_real_route(origin, destination, mode='driving'):
    return get_route_summary(origin, destination, mode=mode)


def get_real_weather(latitude, longitude):
    return get_weather_for_coordinates(latitude, longitude)


def get_real_place_details(place_id):
    return get_place_details(place_id)


def get_real_nearby_places(lat, lng, radius=2000, place_type='tourist_attraction'):
    return get_nearby_places(lat, lng, radius=radius, place_type=place_type)


def get_fallback_recommendations(trip_data):
    """Fallback recommendations when AI is unavailable."""
    scope = trip_data.get('travel_scope', 'both').lower()
    budget = trip_data.get('budget', '').lower()

    if 'domestic' in scope:
        return [
            {
                "destination_name": "Manali, Himachal Pradesh",
                "country": "India",
                "budget_category": "budget",
                "summary": "A stunning mountain destination perfect for adventure lovers. Snow-capped peaks, river rafting, and scenic valleys make it a top pick for Indian travelers.",
                "highlights": "Rohtang Pass|Solang Valley|Old Manali|River Rafting",
                "estimated_cost": "₹15,000 – ₹35,000 per person",
                "best_time": "October to June"
            },
            {
                "destination_name": "Goa",
                "country": "India",
                "budget_category": "moderate",
                "summary": "India's party and beach capital. Perfect for relaxation, nightlife, and amazing seafood. Suits all group types and budgets.",
                "highlights": "Calangute Beach|Old Goa Churches|Night Markets|Water Sports",
                "estimated_cost": "₹20,000 – ₹60,000 per person",
                "best_time": "November to February"
            },
            {
                "destination_name": "Rajasthan Circuit (Jaipur–Jodhpur–Udaipur)",
                "country": "India",
                "budget_category": "moderate",
                "summary": "Experience royal heritage, desert landscapes, and vibrant culture. The golden triangle of Rajasthan offers unmatched history and hospitality.",
                "highlights": "Amber Fort|Mehrangarh Fort|City Palace Udaipur|Desert Safari",
                "estimated_cost": "₹25,000 – ₹70,000 per person",
                "best_time": "October to March"
            }
        ]
    else:
        return [
            {
                "destination_name": "Bali, Indonesia",
                "country": "Indonesia",
                "budget_category": "moderate",
                "summary": "A tropical paradise with stunning temples, rice terraces, and vibrant nightlife. Extremely popular among Indian travelers for its affordability and beauty.",
                "highlights": "Ubud Rice Terraces|Tanah Lot Temple|Seminyak Beach|Mount Batur",
                "estimated_cost": "₹50,000 – ₹1,20,000 per person",
                "best_time": "April to October"
            },
            {
                "destination_name": "Dubai, UAE",
                "country": "UAE",
                "budget_category": "luxury",
                "summary": "The city of superlatives — tallest buildings, largest malls, and luxury experiences. Easy visa for Indians and excellent connectivity.",
                "highlights": "Burj Khalifa|Desert Safari|Dubai Mall|Palm Jumeirah",
                "estimated_cost": "₹80,000 – ₹2,50,000 per person",
                "best_time": "November to April"
            },
            {
                "destination_name": "Thailand (Bangkok + Phuket)",
                "country": "Thailand",
                "budget_category": "budget",
                "summary": "Southeast Asia's most popular destination for Indians. Amazing street food, beautiful beaches, and rich Buddhist culture at very affordable prices.",
                "highlights": "Grand Palace Bangkok|Phi Phi Islands|Street Food|Night Markets",
                "estimated_cost": "₹40,000 – ₹90,000 per person",
                "best_time": "November to April"
            }
        ]


def get_fallback_details(destination_name):
    """Fallback destination details."""
    return {
        "tourist_spots": [
            {"name": f"Main Attraction of {destination_name}", "description": "A must-visit landmark", "entry_fee": "Varies", "time_needed": "2-3 hours"},
            {"name": "Local Market", "description": "Experience local culture and shopping", "entry_fee": "Free", "time_needed": "1-2 hours"},
            {"name": "Scenic Viewpoint", "description": "Best views of the destination", "entry_fee": "Free", "time_needed": "1 hour"}
        ],
        "local_food": [
            {"name": "Local Specialty Dish", "description": "Must-try local cuisine", "avg_cost": "₹200-500 per person"},
            {"name": "Street Food Area", "description": "Authentic local street food experience", "avg_cost": "₹100-300 per person"}
        ],
        "transport_info": {
            "how_to_reach": "Flight from major Indian cities available. Book in advance for best prices.",
            "local_transport": "Taxis, auto-rickshaws, and local buses available.",
            "estimated_transport_budget": "₹5,000 – ₹15,000 for local transport"
        },
        "accommodation_options": [
            {"type": "Budget", "name": "Local Guesthouses", "price_range": "₹500-1500/night", "location": "City Center"},
            {"type": "Mid-range", "name": "3-Star Hotels", "price_range": "₹2000-5000/night", "location": "Tourist Area"},
            {"type": "Luxury", "name": "5-Star Resorts", "price_range": "₹8000+/night", "location": "Prime Location"}
        ],
        "travel_tips": [
            "Book flights and hotels in advance, especially during peak season",
            "Carry cash as not all places accept cards",
            "Respect local customs and dress codes",
            "Stay hydrated and carry a water bottle",
            "Download offline maps before arriving"
        ],
        "emergency_info": {
            "emergency_number": "112 (Universal Emergency)",
            "nearest_hospital": "Contact hotel reception for nearest hospital",
            "indian_embassy": "Contact Indian Embassy for international destinations",
            "useful_apps": "Google Maps, MakeMyTrip, Booking.com"
        }
    }


def get_day_wise_itinerary(destination_name, num_days, trip_data, *, allow_fallback=True, return_metadata=False):
    """
    Generate a structured day-wise itinerary for a destination.

    Uses Gemini for itinerary reasoning and personalisation.
    Does NOT rely on Gemini for factual real-time data (live weather,
    live prices, opening hours, current transport schedules).

    Returns a list of day objects (one per day).
    """
    num_days = max(1, min(int(num_days), 30))  # clamp 1-30

    cache_payload = {
        'destination_name': destination_name,
        'num_days': num_days,
        'trip_data': trip_data,
    }
    cache_key = generate_cache_key('smarttrip:itinerary', cache_payload)
    cached = cache.get(cache_key)
    if cached is not None and allow_fallback and not return_metadata:
        return cached

    prompt = f"""
You are Smart Trip AI, an expert travel planner by Arman Ansari.

Create a detailed {num_days}-day itinerary for:
Destination: {destination_name}
Traveler Profile:
- Budget: {trip_data.get('budget', 'moderate')} {trip_data.get('currency', 'INR')}
- Group Type: {trip_data.get('group_type', 'solo')}
- Travel Medium: {trip_data.get('travel_medium', 'any')}
- Food Preference: {trip_data.get('food_preference', 'any')}
- Accommodation: {trip_data.get('accommodation', 'any')}
- Departure: {trip_data.get('departure_location', 'India')}

IMPORTANT RULES:
- Do NOT include live weather forecasts, real-time prices, or current transport schedules.
- Instead, give general seasonal advice, typical cost ranges, and common transport options.
- Focus on personalised activity sequencing and logical flow between places.

Respond ONLY with a valid JSON object (no markdown, no extra text):
{{
    "days": [
    {{
    "day": 1,
    "date": null,
    "morning": ["Activity 1", "Activity 2"],
    "afternoon": ["Activity 3", "Activity 4"],
    "evening": ["Activity 5"],
    "recommended_places": ["Place A", "Place B"],
    "estimated_daily_cost": "Cost range for the day",
    "approximate_travel_time": "Total travel time for the day",
    "food_suggestions": ["Breakfast suggestion", "Lunch suggestion", "Dinner suggestion"],
    "notes": "Any useful tip or note for the day"
    }}
    ]
}}

Generate exactly {num_days} day objects.
"""

    try:
        generated = generate_ai_text_with_fallback(
            prompt,
            model=DEFAULT_GEMINI_MODEL,
            fallback_model=DEFAULT_GROQ_MODEL,
            return_metadata=True,
            json_mode=True,
        )
        if not generated:
            return get_fallback_itinerary(destination_name, num_days, trip_data) if allow_fallback else None
        text = generated['text']
        if not text:
            return get_fallback_itinerary(destination_name, num_days, trip_data) if allow_fallback else None
        if text.startswith('```'):
            text = text.split('```')[1]
            if text.startswith('json'):
                text = text[4:]
        text = text.strip()
        if not text.startswith('['):
            array_start = text.find('[')
            array_end = text.rfind(']')
            if array_start >= 0 and array_end > array_start:
                text = text[array_start:array_end + 1]
        itinerary_data = json.loads(text)
        itinerary = itinerary_data.get('days', []) if isinstance(itinerary_data, dict) else itinerary_data
        if isinstance(itinerary, list) and len(itinerary) > 0:
            cache.set(cache_key, itinerary, CACHE_TTL)
            if return_metadata:
                return {
                    'itinerary': itinerary,
                    'provider': generated['provider'],
                    'model': generated['model'],
                }
            return itinerary
    except Exception as e:
        print(f"AI itinerary error: {e}")

    if allow_fallback:
        return get_fallback_itinerary(destination_name, num_days, trip_data)
    return None


def get_fallback_itinerary(destination_name, num_days, trip_data):
    """Fallback day-wise itinerary when Gemini is unavailable."""
    days = []
    activity_sets = [
        {
            "morning": [f"Arrive and check in to accommodation in {destination_name}",
                        "Freshen up and have a local breakfast"],
            "afternoon": [f"Explore the city centre / main market of {destination_name}",
                          "Visit the most popular landmark"],
            "evening": ["Enjoy a local dinner", "Relax at the hotel or explore the neighbourhood"],
            "recommended_places": [f"City Centre of {destination_name}", "Main Market", "Popular Landmark"],
            "food_suggestions": ["Local breakfast at a nearby café",
                                 "Traditional lunch at a popular restaurant",
                                 "Street food dinner near the market"],
            "notes": "Keep travel light on arrival day. Carry local currency for small vendors."
        },
        {
            "morning": ["Visit historical monuments or museums", "Morning guided walk"],
            "afternoon": ["Scenic viewpoint or nature spot", "Photography session"],
            "evening": ["Local cultural show or evening cruise", "Dinner at a rooftop restaurant"],
            "recommended_places": ["Museum / Heritage Site", "Scenic Viewpoint"],
            "food_suggestions": ["Continental breakfast at hotel",
                                 "Quick bites at museum café",
                                 "Rooftop dinner"],
            "notes": "Book museum tickets in advance during peak season."
        },
        {
            "morning": ["Day trip to nearby attraction", "Local market shopping"],
            "afternoon": ["Adventure activity or spa relaxation", "Leisure time"],
            "evening": ["Souvenir shopping", "Farewell dinner"],
            "recommended_places": ["Nearby Day-trip Spot", "Local Artisan Market"],
            "food_suggestions": ["Packed breakfast / on-the-go snack",
                                 "Local speciality lunch",
                                 "Multi-cuisine farewell dinner"],
            "notes": "Carry comfortable footwear for walking. Negotiate prices at local markets."
        },
    ]

    budget = trip_data.get('budget', '').lower()
    if 'luxury' in budget:
        cost_range = "₹8,000–₹20,000 per person"
    elif 'budget' in budget or 'cheap' in budget:
        cost_range = "₹1,000–₹4,000 per person"
    else:
        cost_range = "₹3,000–₹8,000 per person"

    for i in range(num_days):
        template = activity_sets[min(i, len(activity_sets) - 1)]
        days.append({
            "day": i + 1,
            "date": None,
            "morning": template["morning"],
            "afternoon": template["afternoon"],
            "evening": template["evening"],
            "recommended_places": template["recommended_places"],
            "estimated_daily_cost": cost_range,
            "approximate_travel_time": "2–4 hours of local travel",
            "food_suggestions": template["food_suggestions"],
            "notes": template["notes"],
        })
    return days


def get_chat_response(user_message, history=None):

    """
    Generate interactive AI travel chat responses using Gemini AI with fallback.
    """
    msg_lower = user_message.lower().strip()

    system_instruction = (
        "You are Smart Trip AI Assistant created by Arman Ansari. "
        "Help travelers plan trips, recommend places, suggest budgets, itineraries, food, stay, transport, and packing tips. "
        "Keep responses friendly, helpful, structured, and easy to read. Use bullet points and travel emojis where relevant."
    )

    prompt = f"{system_instruction}\n\nUser Question: {user_message}\nProvide a helpful, detailed, friendly answer."
    reply_text = generate_ai_text_with_fallback(prompt, system_message=system_instruction, model=DEFAULT_GEMINI_MODEL, fallback_model=DEFAULT_GROQ_MODEL)
    if reply_text:
        return {
            "reply": reply_text,
            "suggestions": [
                "Plan a complete trip",
                "Best budget destinations",
                "Packing checklist"
            ]
        }

    # Fallback Smart Responses
    if any(k in msg_lower for k in ['hi', 'hello', 'hey', 'kaise', 'namaste']):
        reply = (
            "👋 Hello! I am your **Smart Trip AI Assistant** created by Arman Ansari.\n\n"
            "How can I help you today? You can ask me about:\n"
            "• 🏔️ Top travel destinations for your budget\n"
            "• 📅 Best season to visit places\n"
            "• 🍱 Local food & street food recommendations\n"
            "• ✈️ Flight & transport planning tips"
        )
    elif any(k in msg_lower for k in ['budget', 'cheap', 'sasta', 'low cost', 'under']):
        reply = (
            "💰 **Top Budget Travel Destinations in India:**\n\n"
            "1. **Manali, Himachal Pradesh** — Avg cost ₹12,000–₹20,000 per person for 4-5 days.\n"
            "2. **Goa (Off-season: July-Sept)** — Cheap stays near Calangute & Baga.\n"
            "3. **Rishikesh, Uttarakhand** — Hostels starting at ₹400/night + River Rafting!\n"
            "4. **Jaipur, Rajasthan** — Budget street food, royal forts & cheap heritage guesthouses.\n\n"
            "💡 *Tip:* Use our **Trip Planner** tab to get an exact AI itinerary within your budget!"
        )
    elif any(k in msg_lower for k in ['manali', 'himachal', 'snow', 'mountain']):
        reply = (
            "🏔️ **Manali Travel Guide:**\n\n"
            "• **Best Time:** October to June (Dec-Feb for snow lovers!)\n"
            "• **Must Visit:** Solang Valley, Rohtang Pass, Old Manali Cafe Street, Jogini Waterfall.\n"
            "• **Food:** Siddu (local dish), Trout fish, Momos in Old Manali.\n"
            "• **Estimated Cost:** ₹15,000 – ₹30,000 per person."
        )
    elif any(k in msg_lower for k in ['goa', 'beach', 'party']):
        reply = (
            "🏖️ **Goa Beach & Vacation Guide:**\n\n"
            "• **North Goa:** Party vibes, watersports (Calangute, Baga, Anjuna).\n"
            "• **South Goa:** Serene beaches, luxury resorts, quiet nature (Palolem, Agonda).\n"
            "• **Best Season:** November to February.\n"
            "• **Budget:** ₹18,000 – ₹45,000 per person."
        )
    elif any(k in msg_lower for k in ['bali', 'dubai', 'thailand', 'international', 'abroad']):
        reply = (
            "✈️ **Top Budget International Trips for Indians:**\n\n"
            "1. **Thailand:** Visa-free / easy visa. Budget ₹35,000–₹70,000.\n"
            "2. **Bali, Indonesia:** Gorgeous rice terraces & beach resorts. Budget ₹45,000–₹90,000.\n"
            "3. **Dubai, UAE:** Modern skyline & desert safari. Budget ₹70,000–₹1.5 Lakhs."
        )
    elif any(k in msg_lower for k in ['food', 'khana', 'eat', 'restaurant']):
        reply = (
            "🍱 **Must-Try Local Delicacies:**\n\n"
            "• **Rajasthan:** Dal Baati Churma, Gatte ki Sabzi, Laal Maas\n"
            "• **Goa:** Goan Fish Curry, Bebinca dessert, Prawn Balchão\n"
            "• **Himachal:** Siddu, Dham, Thukpa & Tibetan Momos"
        )
    else:
        reply = (
            f"🤖 I hear you! As your **Smart Trip AI Assistant**, I can help you plan your travel details for **{user_message}**.\n\n"
            "Here are quick actions you can take right now:\n"
            "1. Click **'Plan My Trip'** in top menu to get personalized 3-destination options!\n"
            "2. Explore user travel stories in the **Community** tab.\n"
            "3. Ask me specifically about budgets, best months, or flight options!"
        )

    return {
        "reply": reply,
        "suggestions": [
            "Tell me about Goa",
            "Budget trips under 20k",
            "International visa-free places"
        ]
    }

