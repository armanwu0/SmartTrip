from django.conf import settings
from django.db import models
from django.db.models import Q, F

User = settings.AUTH_USER_MODEL


class Trip(models.Model):
    STATUS_DRAFT = 'DRAFT'
    STATUS_PLANNED = 'PLANNED'
    STATUS_ACTIVE = 'ACTIVE'
    STATUS_COMPLETED = 'COMPLETED'
    STATUS_CANCELLED = 'CANCELLED'

    TRIP_STATUS_CHOICES = [
        (STATUS_DRAFT, 'Draft'),
        (STATUS_PLANNED, 'Planned'),
        (STATUS_ACTIVE, 'Active'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trips', db_index=True)
    trip_name = models.CharField(max_length=200)
    source = models.CharField(max_length=200, blank=True, default='')
    destination = models.CharField(max_length=200)
    start_date = models.DateField()
    end_date = models.DateField()
    number_of_travelers = models.PositiveIntegerField(default=1)
    total_budget = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default='INR')
    travel_style = models.CharField(max_length=100, blank=True, default='')
    status = models.CharField(max_length=20, choices=TRIP_STATUS_CHOICES, default=STATUS_DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['user', 'destination']),
            models.Index(fields=['destination', 'start_date']),
        ]
        constraints = [
            models.CheckConstraint(condition=Q(start_date__lte=F('end_date')), name='trip_start_before_end'),
            models.CheckConstraint(condition=Q(number_of_travelers__gte=1), name='trip_traveler_count_positive'),
        ]

    def __str__(self):
        return self.trip_name or f'{self.destination} trip'


class ItineraryDay(models.Model):
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='itinerary_days', db_index=True)
    day_number = models.PositiveIntegerField(default=1)
    date = models.DateField(null=True, blank=True)
    title = models.CharField(max_length=200, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['day_number']
        unique_together = ('trip', 'day_number')
        indexes = [
            models.Index(fields=['trip', 'day_number']),
        ]

    def __str__(self):
        return f'{self.trip.trip_name} - Day {self.day_number}'


class Place(models.Model):
    CATEGORY_CHOICES = [
        ('hotel', 'Hotel'),
        ('restaurant', 'Restaurant'),
        ('attraction', 'Attraction'),
        ('transport', 'Transport'),
        ('beach', 'Beach'),
        ('nature', 'Nature'),
        ('activity', 'Activity'),
        ('misc', 'Miscellaneous'),
    ]

    external_place_id = models.CharField(max_length=200, blank=True, default='', db_index=True)
    name = models.CharField(max_length=200)
    address = models.CharField(max_length=500, blank=True, default='')
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='misc', blank=True)
    rating = models.FloatField(null=True, blank=True)
    photo_reference = models.CharField(max_length=500, blank=True, default='')
    photo_url = models.URLField(blank=True, default='')
    source = models.CharField(max_length=100, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['external_place_id']),
            models.Index(fields=['name'])
        ]

    def __str__(self):
        return self.name


class ItineraryItem(models.Model):
    itinerary_day = models.ForeignKey(ItineraryDay, on_delete=models.CASCADE, related_name='items', db_index=True)
    place = models.ForeignKey(Place, on_delete=models.SET_NULL, null=True, blank=True, related_name='itinerary_items')
    activity_name = models.CharField(max_length=200)
    start_time = models.CharField(max_length=20, blank=True, default='')
    end_time = models.CharField(max_length=20, blank=True, default='')
    sequence_order = models.PositiveIntegerField(default=1)
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    travel_time_from_previous = models.CharField(max_length=50, blank=True, default='')
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['sequence_order', 'start_time']
        indexes = [
            models.Index(fields=['itinerary_day', 'sequence_order']),
        ]

    def __str__(self):
        return f'{self.activity_name} ({self.itinerary_day})'


class Route(models.Model):
    TRANSPORT_CHOICES = [
        ('driving', 'Driving'),
        ('walking', 'Walking'),
        ('bicycle', 'Bicycle'),
        ('two_wheeler', 'Two Wheeler'),
        ('transit', 'Transit'),
    ]

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='routes', db_index=True)
    origin = models.CharField(max_length=200)
    destination = models.CharField(max_length=200)
    distance = models.CharField(max_length=100, blank=True, default='')
    duration = models.CharField(max_length=100, blank=True, default='')
    transport_mode = models.CharField(max_length=30, choices=TRANSPORT_CHOICES, default='driving')
    provider = models.CharField(max_length=100, blank=True, default='')
    route_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['trip', 'transport_mode']),
        ]

    def __str__(self):
        return f'{self.origin} → {self.destination}'


class Expense(models.Model):
    CATEGORY_TRANSPORT = 'Transport'
    CATEGORY_HOTEL = 'Hotel'
    CATEGORY_FOOD = 'Food'
    CATEGORY_ACTIVITY = 'Activity'
    CATEGORY_ENTRY_FEE = 'Entry Fee'
    CATEGORY_LOCAL_TRANSPORT = 'Local Transport'
    CATEGORY_PARKING = 'Parking'
    CATEGORY_MISCELLANEOUS = 'Miscellaneous'

    EXPENSE_CATEGORIES = [
        (CATEGORY_TRANSPORT, 'Transport'),
        (CATEGORY_HOTEL, 'Hotel'),
        (CATEGORY_FOOD, 'Food'),
        (CATEGORY_ACTIVITY, 'Activity'),
        (CATEGORY_ENTRY_FEE, 'Entry Fee'),
        (CATEGORY_LOCAL_TRANSPORT, 'Local Transport'),
        (CATEGORY_PARKING, 'Parking'),
        (CATEGORY_MISCELLANEOUS, 'Miscellaneous'),
    ]

    STATUS_VERIFIED = 'VERIFIED'
    STATUS_ESTIMATED = 'ESTIMATED'
    STATUS_USER_PROVIDED = 'USER_PROVIDED'

    EXPENSE_STATUS_CHOICES = [
        (STATUS_VERIFIED, 'Verified'),
        (STATUS_ESTIMATED, 'Estimated'),
        (STATUS_USER_PROVIDED, 'User Provided'),
    ]

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='expenses', db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='trip_expenses', db_index=True)
    category = models.CharField(max_length=30, choices=EXPENSE_CATEGORIES, default=CATEGORY_MISCELLANEOUS)
    description = models.CharField(max_length=255, blank=True, default='')
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    currency = models.CharField(max_length=10, default='INR')
    expense_date = models.DateField(null=True, blank=True)
    source = models.CharField(max_length=100, blank=True, default='')
    status = models.CharField(max_length=20, choices=EXPENSE_STATUS_CHOICES, default=STATUS_ESTIMATED)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-expense_date', '-created_at']
        indexes = [
            models.Index(fields=['trip', 'category']),
            models.Index(fields=['user', 'trip']),
        ]

    def __str__(self):
        return f'{self.category} - {self.amount}'


class AIConversation(models.Model):
    PROVIDER_GEMINI = 'GEMINI'
    PROVIDER_GROQ = 'GROQ'
    PROVIDER_CHOICES = [
        (PROVIDER_GEMINI, 'GEMINI'),
        (PROVIDER_GROQ, 'GROQ'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_conversations', db_index=True)
    trip = models.ForeignKey(Trip, on_delete=models.SET_NULL, null=True, blank=True, related_name='ai_conversations', db_index=True)
    user_message = models.TextField()
    ai_response = models.TextField(blank=True, default='')
    action = models.CharField(max_length=80, blank=True, default='')
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES, default=PROVIDER_GEMINI)
    model = models.CharField(max_length=100, blank=True, default='')
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'trip', 'created_at']),
        ]

    def __str__(self):
        return f'{self.user.username} - {self.provider}'


class SavedTrip(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='saved_trips_db', db_index=True)
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name='saved_by_users', db_index=True)
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'trip')
        ordering = ['-saved_at']

    def __str__(self):
        return f'{self.user.username} saved {self.trip.trip_name}'
