from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator


class DestinationReview(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews')
    destination_name = models.CharField(max_length=200)
    country = models.CharField(max_length=100, blank=True)
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=200)
    content = models.TextField()
    visited_month = models.CharField(max_length=20, blank=True)
    travel_style = models.CharField(max_length=100, blank=True)
    helpful_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'destination_name']

    def __str__(self):
        return f"{self.user.username} - {self.destination_name} ({self.rating}/5)"


class ReviewHelpful(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    review = models.ForeignKey(DestinationReview, on_delete=models.CASCADE, related_name='helpful_votes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['user', 'review']


class TripBlog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='blogs')
    title = models.CharField(max_length=300)
    destination = models.CharField(max_length=200)
    country = models.CharField(max_length=100, blank=True)
    content = models.TextField()
    cover_emoji = models.CharField(max_length=10, default='✈️')
    tags = models.CharField(max_length=300, blank=True)
    likes = models.IntegerField(default=0)
    views = models.IntegerField(default=0)
    published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} by {self.user.username}"


class BlogLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    blog = models.ForeignKey(TripBlog, on_delete=models.CASCADE, related_name='liked_by')

    class Meta:
        unique_together = ['user', 'blog']
