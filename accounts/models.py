from django.db import models
from django.contrib.auth.models import User


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar = models.URLField(blank=True, default='')
    bio = models.TextField(blank=True, default='')
    phone = models.CharField(max_length=20, blank=True, default='')
    location = models.CharField(max_length=200, blank=True, default='')
    preferred_travel_style = models.CharField(max_length=200, blank=True, default='')
    preferred_activities = models.TextField(blank=True, default='')
    preferred_destinations = models.TextField(blank=True, default='')
    budget_preference = models.CharField(max_length=100, blank=True, default='')
    preferred_transport = models.CharField(max_length=100, blank=True, default='')
    food_preferences = models.TextField(blank=True, default='')
    solo_group_preference = models.CharField(max_length=50, blank=True, default='')
    travel_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Profile of {self.user.username}"


class LoginActivity(models.Model):
    SUCCESS = 'SUCCESS'
    FAILURE = 'FAILURE'
    STATUS_CHOICES = [(SUCCESS, 'Success'), (FAILURE, 'Failure')]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='login_activities', db_index=True)
    login_time = models.DateTimeField(auto_now_add=True)
    logout_time = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=SUCCESS)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    class Meta:
        ordering = ['-login_time']

    def __str__(self):
        return f'{self.user.username} - {self.status}'


class SavedTrip(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_trips')
    destination_name = models.CharField(max_length=200)
    country = models.CharField(max_length=100, blank=True)
    summary = models.TextField(blank=True)
    estimated_cost = models.CharField(max_length=100, blank=True)
    best_time = models.CharField(max_length=200, blank=True)
    trip_data = models.JSONField(default=dict)
    notes = models.TextField(blank=True, default='')
    is_completed = models.BooleanField(default=False)
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-saved_at']

    def __str__(self):
        return f"{self.user.username} - {self.destination_name}"


class WishlistItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='wishlist')
    destination_name = models.CharField(max_length=200)
    country = models.CharField(max_length=100, blank=True)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'destination_name']

    def __str__(self):
        return f"{self.user.username} - {self.destination_name}"
