from django.contrib import admin
from .models import UserProfile, SavedTrip, WishlistItem

@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'location', 'travel_count', 'created_at']

@admin.register(SavedTrip)
class SavedTripAdmin(admin.ModelAdmin):
    list_display = ['user', 'destination_name', 'country', 'is_completed', 'saved_at']
    list_filter = ['is_completed']

@admin.register(WishlistItem)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['user', 'destination_name', 'country', 'added_at']
