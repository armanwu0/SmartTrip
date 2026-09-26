from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from .models import UserProfile, SavedTrip, WishlistItem


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    password2 = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password', 'password2']

    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({'password': 'Passwords do not match.'})
        if User.objects.filter(email=data['email']).exists():
            raise serializers.ValidationError({'email': 'Email already registered.'})
        return data

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        UserProfile.objects.create(user=user)
        return user


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data['username'], password=data['password'])
        if not user:
            # Try by email
            try:
                u = User.objects.get(email=data['username'])
                user = authenticate(username=u.username, password=data['password'])
            except User.DoesNotExist:
                pass
        if not user:
            raise serializers.ValidationError('Invalid credentials.')
        if not user.is_active:
            raise serializers.ValidationError('Account disabled.')
        data['user'] = user
        return data


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            'avatar', 'bio', 'phone', 'location',
            'preferred_travel_style', 'preferred_activities', 'preferred_destinations',
            'budget_preference', 'preferred_transport', 'food_preferences',
            'solo_group_preference', 'travel_count'
        ]
        read_only_fields = ['travel_count']


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = [
            'avatar', 'bio', 'phone', 'location',
            'preferred_travel_style', 'preferred_activities', 'preferred_destinations',
            'budget_preference', 'preferred_transport', 'food_preferences',
            'solo_group_preference'
        ]
        extra_kwargs = {
            'avatar': {'required': False, 'allow_blank': True},
            'bio': {'required': False, 'allow_blank': True},
            'phone': {'required': False, 'allow_blank': True},
            'location': {'required': False, 'allow_blank': True},
            'preferred_travel_style': {'required': False, 'allow_blank': True},
            'preferred_activities': {'required': False, 'allow_blank': True},
            'preferred_destinations': {'required': False, 'allow_blank': True},
            'budget_preference': {'required': False, 'allow_blank': True},
            'preferred_transport': {'required': False, 'allow_blank': True},
            'food_preferences': {'required': False, 'allow_blank': True},
            'solo_group_preference': {'required': False, 'allow_blank': True},
        }


class UserUpdateSerializer(serializers.ModelSerializer):
    profile = UserProfileUpdateSerializer(required=False)

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'profile']
        extra_kwargs = {
            'first_name': {'required': False, 'allow_blank': True},
            'last_name': {'required': False, 'allow_blank': True},
            'email': {'required': False, 'allow_blank': True},
        }

    def validate_email(self, value):
        if value:
            user = self.instance
            if User.objects.filter(email__iexact=value).exclude(pk=user.pk if user else None).exists():
                raise serializers.ValidationError('Email is already in use by another account.')
        return value

    def update(self, instance, validated_data):
        profile_data = validated_data.pop('profile', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if profile_data is not None:
            profile, _ = UserProfile.objects.get_or_create(user=instance)
            profile_serializer = UserProfileUpdateSerializer(profile, data=profile_data, partial=True)
            if profile_serializer.is_valid(raise_exception=True):
                profile_serializer.save()

        instance.refresh_from_db()
        return instance



class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    saved_trips_count = serializers.SerializerMethodField()
    wishlist_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile', 'saved_trips_count', 'wishlist_count', 'date_joined']

    def get_saved_trips_count(self, obj):
        return obj.saved_trips.count()

    def get_wishlist_count(self, obj):
        return obj.wishlist.count()


class SavedTripSerializer(serializers.ModelSerializer):
    class Meta:
        model = SavedTrip
        fields = ['id', 'destination_name', 'country', 'summary', 'estimated_cost', 'best_time', 'trip_data', 'notes', 'is_completed', 'saved_at']
        read_only_fields = ['id', 'saved_at']


class WishlistSerializer(serializers.ModelSerializer):
    class Meta:
        model = WishlistItem
        fields = ['id', 'destination_name', 'country', 'added_at']
        read_only_fields = ['id', 'added_at']
