from rest_framework import serializers
from .models import Trip, ItineraryDay, ItineraryItem, Place, Route, Expense, AIConversation, SavedTrip


class PlaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Place
        fields = ['id', 'external_place_id', 'name', 'address', 'latitude', 'longitude', 'category', 'rating', 'photo_reference', 'photo_url', 'source', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ItineraryItemSerializer(serializers.ModelSerializer):
    place = PlaceSerializer(read_only=True)

    class Meta:
        model = ItineraryItem
        fields = ['id', 'itinerary_day', 'place', 'activity_name', 'start_time', 'end_time', 'sequence_order', 'estimated_cost', 'travel_time_from_previous', 'notes', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ItineraryDaySerializer(serializers.ModelSerializer):
    items = ItineraryItemSerializer(many=True, read_only=True)

    class Meta:
        model = ItineraryDay
        fields = ['id', 'trip', 'day_number', 'date', 'title', 'items', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class TripSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='pk', read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Trip
        fields = ['id', 'user', 'trip_name', 'source', 'destination', 'start_date', 'end_date', 'number_of_travelers', 'total_budget', 'currency', 'travel_style', 'status', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']

    def validate(self, data):
        if data.get('start_date') and data.get('end_date') and data['start_date'] > data['end_date']:
            raise serializers.ValidationError({'end_date': 'End date must be after start date.'})
        return data


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ['id', 'trip', 'origin', 'destination', 'distance', 'duration', 'transport_mode', 'provider', 'route_data', 'created_at']
        read_only_fields = ['id', 'created_at']


class ExpenseSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='pk', read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Expense
        fields = ['id', 'trip', 'user', 'category', 'description', 'amount', 'currency', 'expense_date', 'source', 'status', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class AIConversationSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='pk', read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = AIConversation
        fields = ['id', 'user', 'trip', 'user_message', 'ai_response', 'action', 'provider', 'model', 'metadata', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class SavedTripSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='pk', read_only=True)
    trip = TripSerializer(read_only=True)

    class Meta:
        model = SavedTrip
        fields = ['id', 'user', 'trip', 'saved_at']
        read_only_fields = ['id', 'user', 'saved_at']
