from rest_framework import serializers
from django.contrib.auth.models import User
from .models import DestinationReview, TripBlog, ReviewHelpful, BlogLike


class ReviewSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    user_avatar = serializers.SerializerMethodField()
    user_has_voted = serializers.SerializerMethodField()

    class Meta:
        model = DestinationReview
        fields = [
            'id', 'username', 'user_avatar', 'destination_name', 'country',
            'rating', 'title', 'content', 'visited_month', 'travel_style',
            'helpful_count', 'user_has_voted', 'created_at'
        ]
        read_only_fields = ['id', 'helpful_count', 'created_at']

    def get_username(self, obj):
        return obj.user.get_full_name() or obj.user.username

    def get_user_avatar(self, obj):
        try:
            return obj.user.profile.avatar or ''
        except Exception:
            return ''

    def get_user_has_voted(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ReviewHelpful.objects.filter(user=request.user, review=obj).exists()
        return False


class TripBlogSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    user_has_liked = serializers.SerializerMethodField()
    tags_list = serializers.SerializerMethodField()

    class Meta:
        model = TripBlog
        fields = [
            'id', 'username', 'title', 'destination', 'country',
            'content', 'cover_emoji', 'tags', 'tags_list',
            'likes', 'views', 'user_has_liked', 'created_at'
        ]
        read_only_fields = ['id', 'likes', 'views', 'created_at']

    def get_username(self, obj):
        return obj.user.get_full_name() or obj.user.username

    def get_user_has_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return BlogLike.objects.filter(user=request.user, blog=obj).exists()
        return False

    def get_tags_list(self, obj):
        if obj.tags:
            return [t.strip() for t in obj.tags.split(',') if t.strip()]
        return []
