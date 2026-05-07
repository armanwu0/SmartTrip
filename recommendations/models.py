from django.db import models


class TripRequest(models.Model):
    user_name = models.CharField(max_length=100)
    budget = models.CharField(max_length=50)
    currency = models.CharField(max_length=10, default='INR')
    group_type = models.CharField(max_length=50)
    travel_scope = models.CharField(max_length=50)
    num_days = models.IntegerField()
    food_preference = models.CharField(max_length=100, blank=True)
    accommodation = models.CharField(max_length=100, blank=True)
    departure_location = models.CharField(max_length=200)
    travel_medium = models.CharField(max_length=100)
    destination_style = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user_name} - {self.departure_location} - {self.created_at}"


class TripRecommendation(models.Model):
    trip_request = models.ForeignKey(TripRequest, on_delete=models.CASCADE, related_name='recommendations')
    destination_name = models.CharField(max_length=200)
    country = models.CharField(max_length=100, blank=True)
    budget_category = models.CharField(max_length=50)
    summary = models.TextField()
    highlights = models.TextField(blank=True)
    estimated_cost = models.CharField(max_length=100, blank=True)
    best_time = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.destination_name} for {self.trip_request.user_name}"


class DestinationDetail(models.Model):
    recommendation = models.OneToOneField(TripRecommendation, on_delete=models.CASCADE, related_name='details')
    tourist_spots = models.TextField(blank=True)
    local_food = models.TextField(blank=True)
    transport_info = models.TextField(blank=True)
    accommodation_options = models.TextField(blank=True)
    travel_tips = models.TextField(blank=True)
    emergency_info = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Details for {self.recommendation.destination_name}"
