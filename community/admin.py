from django.contrib import admin
from .models import DestinationReview, TripBlog

@admin.register(DestinationReview)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ['user', 'destination_name', 'rating', 'helpful_count', 'created_at']

@admin.register(TripBlog)
class BlogAdmin(admin.ModelAdmin):
    list_display = ['user', 'title', 'destination', 'likes', 'views', 'published', 'created_at']
    list_filter = ['published']
