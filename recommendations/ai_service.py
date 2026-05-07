import json
import os
from django.conf import settings

try:
    from google import genai
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False


def get_gemini_client():
    api_key = settings.GEMINI_API_KEY or os.environ.get('GEMINI_API_KEY', '')
    if not api_key or not GENAI_AVAILABLE:
        return None
    client = genai.Client(api_key=api_key)
    return client


def get_travel_recommendations(trip_data):
    """
    Get AI-powered travel recommendations using Google Gemini.
    Returns a list of destination recommendations.
    """
    client = get_gemini_client()

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

    if client:
        try:
            response = client.models.generate_content(
                model='gemini-1.5-flash',
                contents=prompt
            )
            text = response.text.strip()
            # Remove markdown code blocks if present
            if text.startswith('```'):
                text = text.split('```')[1]
                if text.startswith('json'):
                    text = text[4:]
            text = text.strip()
            recommendations = json.loads(text)
            return recommendations
        except Exception as e:
            print(f"Gemini API error: {e}")
            return get_fallback_recommendations(trip_data)
    else:
        return get_fallback_recommendations(trip_data)


def get_destination_details(destination_name, trip_data):
    """
    Get detailed information about a specific destination using Gemini AI.
    """
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

    if client:
        try:
            response = client.models.generate_content(
                model='gemini-1.5-flash',
                contents=prompt
            )
            text = response.text.strip()
            if text.startswith('```'):
                text = text.split('```')[1]
                if text.startswith('json'):
                    text = text[4:]
            text = text.strip()
            details = json.loads(text)
            return details
        except Exception as e:
            print(f"Gemini API error for details: {e}")
            return get_fallback_details(destination_name)
    else:
        return get_fallback_details(destination_name)


def get_location_suggestions(query):
    """
    Get location autocomplete suggestions using Gemini.
    """
    client = get_gemini_client()

    if not query or len(query) < 2:
        return []

    prompt = f"""
Give me 5 real city/location suggestions for the autocomplete query: "{query}"
Respond ONLY with a JSON array of strings like:
["City, Country", "City, State, Country", ...]
No markdown, no extra text.
"""

    if client:
        try:
            response = client.models.generate_content(
                model='gemini-1.5-flash',
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

    # Fallback suggestions
    common_cities = [
        "Mumbai, India", "Delhi, India", "Bangalore, India", "Chennai, India",
        "Kolkata, India", "Hyderabad, India", "Pune, India", "Ahmedabad, India",
        "Jaipur, India", "Surat, India", "Lucknow, India", "Kanpur, India"
    ]
    return [c for c in common_cities if query.lower() in c.lower()][:5]


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
