from django.urls import path
from . import views

urlpatterns = [
    path('recommendations/', views.get_recommendations, name='get_recommendations'),
    path('destination/<int:recommendation_id>/', views.get_destination_detail, name='get_destination_detail'),
    path('autocomplete/', views.location_autocomplete, name='location_autocomplete'),
    path('health/', views.health_check, name='health_check'),
]
