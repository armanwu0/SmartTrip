from django.contrib import admin
from .models import Trip, ItineraryDay, ItineraryItem, Place, Route, Expense, AIConversation, SavedTrip


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ('trip_name', 'user', 'destination', 'start_date', 'end_date', 'status', 'total_budget')
    list_filter = ('status', 'currency', 'created_at')
    search_fields = ('trip_name', 'destination', 'source', 'user__username', 'user__email')


@admin.register(ItineraryDay)
class ItineraryDayAdmin(admin.ModelAdmin):
    list_display = ('trip', 'day_number', 'date', 'title')
    list_filter = ('trip__destination', 'day_number')
    search_fields = ('title', 'trip__trip_name')


@admin.register(ItineraryItem)
class ItineraryItemAdmin(admin.ModelAdmin):
    list_display = ('activity_name', 'itinerary_day', 'sequence_order', 'estimated_cost')
    list_filter = ('itinerary_day__trip__destination',)
    search_fields = ('activity_name', 'notes', 'place__name')


@admin.register(Place)
class PlaceAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'rating', 'source')
    list_filter = ('category', 'source')
    search_fields = ('name', 'address', 'external_place_id')


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ('trip', 'origin', 'destination', 'transport_mode', 'distance', 'duration')
    list_filter = ('transport_mode', 'provider')
    search_fields = ('origin', 'destination', 'trip__trip_name')


@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('trip', 'category', 'amount', 'currency', 'status', 'expense_date')
    list_filter = ('category', 'status', 'currency')
    search_fields = ('description', 'trip__trip_name')


@admin.register(AIConversation)
class AIConversationAdmin(admin.ModelAdmin):
    list_display = ('user', 'trip', 'provider', 'model', 'created_at')
    list_filter = ('provider', 'model', 'created_at')
    search_fields = ('user_message', 'ai_response', 'trip__trip_name')


@admin.register(SavedTrip)
class SavedTripAdmin(admin.ModelAdmin):
    list_display = ('user', 'trip', 'saved_at')
    search_fields = ('user__username', 'trip__trip_name')
