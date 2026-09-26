from django.urls import path
from . import views

urlpatterns = [
    path('reviews/add/', views.add_review, name='add-review'),
    path('reviews/<str:destination_name>/', views.destination_reviews, name='destination-reviews'),
    path('reviews/<int:review_id>/helpful/', views.vote_helpful, name='vote-helpful'),
    path('blogs/', views.blog_list, name='blog-list'),
    path('blogs/create/', views.create_blog, name='create-blog'),
    path('blogs/<int:blog_id>/', views.blog_detail, name='blog-detail'),
    path('blogs/<int:blog_id>/like/', views.like_blog, name='like-blog'),
    path('trending/', views.trending_destinations, name='trending'),
]
