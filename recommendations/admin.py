from django.contrib import admin
from .models import TripRequest, TripRecommendation, DestinationDetail


@admin.register(TripRequest)
class TripRequestAdmin(admin.ModelAdmin):
    list_display = ['user_name', 'departure_location', 'budget', 'num_days', 'created_at']
    list_filter = ['travel_scope', 'group_type', 'currency']
    search_fields = ['user_name', 'departure_location']


@admin.register(TripRecommendation)
class TripRecommendationAdmin(admin.ModelAdmin):
    list_display = ['destination_name', 'country', 'budget_category', 'created_at']
    list_filter = ['budget_category', 'country']
    search_fields = ['destination_name', 'country']


@admin.register(DestinationDetail)
class DestinationDetailAdmin(admin.ModelAdmin):
    list_display = ['recommendation', 'created_at']
