from django.urls import path
from . import views

urlpatterns = [
    path('recommendations/', views.get_recommendations, name='get_recommendations'),
    path('destination/<int:recommendation_id>/', views.get_destination_detail, name='get_destination_detail'),
    path('autocomplete/', views.location_autocomplete, name='location_autocomplete'),
    path('search/', views.real_place_search, name='real_place_search'),
    path('place-details/', views.real_place_details, name='real_place_details'),
    path('route/', views.real_route_summary, name='real_route_summary'),
    path('weather/', views.real_weather_summary, name='real_weather_summary'),
    path('parse-trip/', views.parse_trip_request, name='parse_trip_request'),
    path('budget/', views.trip_budget_summary, name='trip_budget_summary'),
    path('chat/', views.ai_chat, name='ai_chat'),
    path('health/', views.health_check, name='health_check'),
    path('itinerary/', views.get_itinerary, name='get_itinerary'),
]

