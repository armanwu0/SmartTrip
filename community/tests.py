import pytest
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from community.models import DestinationReview, TripBlog, ReviewHelpful, BlogLike
from recommendations.models import TripRequest, TripRecommendation


@pytest.mark.django_db
class TestCommunityApp:
    def setup_method(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='arman', password='password123')

    # ---- Reviews Tests ----
    def test_get_reviews_success(self):
        DestinationReview.objects.create(
            user=self.user,
            destination_name='Goa',
            rating=5,
            title='Beach Paradise',
            content='Loved the beaches!'
        )
        res = self.client.get('/api/community/reviews/Goa/')
        assert res.status_code == status.HTTP_200_OK
        assert res.data['success'] is True
        assert res.data['destination'] == 'Goa'
        assert res.data['avg_rating'] == 5.0
        assert len(res.data['reviews']) == 1

    def test_add_review_success_and_validation(self):
        self.client.force_authenticate(user=self.user)
        valid_payload = {
            'destination_name': 'Goa',
            'rating': 4,
            'title': 'Great Trip',
            'content': 'Enjoyed local food.'
        }
        res = self.client.post('/api/community/reviews/add/', valid_payload, format='json')
        assert res.status_code == status.HTTP_201_CREATED
        assert res.data['success'] is True
        assert DestinationReview.objects.filter(user=self.user, destination_name='Goa').exists()

        # Validation failure: invalid rating (out of 1-5 range)
        invalid_payload = {'destination_name': 'Goa', 'rating': 10, 'title': 'No rating'}
        res_invalid = self.client.post('/api/community/reviews/add/', invalid_payload, format='json')
        assert res_invalid.status_code == status.HTTP_400_BAD_REQUEST
        assert 'errors' in res_invalid.data

    def test_vote_helpful_toggle(self):
        review = DestinationReview.objects.create(
            user=self.user,
            destination_name='Paris',
            rating=5,
            title='Romantic City',
            content='Eiffel tower was great.'
        )
        voter = User.objects.create_user(username='voter', password='password123')
        self.client.force_authenticate(user=voter)

        # First vote: helpful_count becomes 1
        res1 = self.client.post(f'/api/community/reviews/{review.id}/helpful/')
        assert res1.status_code == status.HTTP_200_OK
        assert res1.data['voted'] is True
        assert res1.data['helpful_count'] == 1

        # Second vote: toggles off, helpful_count becomes 0
        res2 = self.client.post(f'/api/community/reviews/{review.id}/helpful/')
        assert res2.status_code == status.HTTP_200_OK
        assert res2.data['voted'] is False
        assert res2.data['helpful_count'] == 0

    # ---- Blogs Tests ----
    def test_get_blogs_success(self):
        TripBlog.objects.create(
            user=self.user,
            title='My Bali Trip',
            destination='Bali',
            content='Awesome tropical vacation.',
            published=True
        )
        res = self.client.get('/api/community/blogs/')
        assert res.status_code == status.HTTP_200_OK
        assert res.data['success'] is True
        assert len(res.data['blogs']) == 1

    def test_create_blog_success_and_validation(self):
        self.client.force_authenticate(user=self.user)
        valid_blog = {
            'title': 'Exploring Manali',
            'destination': 'Manali',
            'country': 'India',
            'content': 'Snowy mountains and beautiful valleys.',
            'cover_emoji': '🏔️',
            'tags': 'mountain, snow'
        }
        res = self.client.post('/api/community/blogs/create/', valid_blog, format='json')
        assert res.status_code == status.HTTP_201_CREATED
        assert res.data['success'] is True
        assert TripBlog.objects.filter(title='Exploring Manali').exists()

        # Validation failure: missing content
        invalid_blog = {'title': 'No Content', 'destination': 'Manali'}
        res_invalid = self.client.post('/api/community/blogs/create/', invalid_blog, format='json')
        assert res_invalid.status_code == status.HTTP_400_BAD_REQUEST

    def test_like_blog_toggle(self):
        blog = TripBlog.objects.create(
            user=self.user,
            title='Shimla Trip',
            destination='Shimla',
            content='Great mountain breeze.',
            published=True
        )
        liker = User.objects.create_user(username='liker', password='password123')
        self.client.force_authenticate(user=liker)

        # First like
        res1 = self.client.post(f'/api/community/blogs/{blog.id}/like/')
        assert res1.status_code == status.HTTP_200_OK
        assert res1.data['liked'] is True
        assert res1.data['likes'] == 1

        # Second like: toggle off
        res2 = self.client.post(f'/api/community/blogs/{blog.id}/like/')
        assert res2.status_code == status.HTTP_200_OK
        assert res2.data['liked'] is False
        assert res2.data['likes'] == 0

    # ---- Trending & Pagination Tests ----
    def test_trending_destinations_success(self):
        req = TripRequest.objects.create(
            user_name='tester', budget='medium', group_type='solo',
            travel_scope='domestic', num_days=3, departure_location='City',
            travel_medium='flight', destination_style='culture'
        )
        TripRecommendation.objects.create(trip_request=req, destination_name='Goa', country='India')

        res = self.client.get('/api/community/trending/')
        assert res.status_code == status.HTTP_200_OK
        assert res.data['success'] is True
        assert len(res.data['trending']) >= 1

    def test_community_pagination(self):
        # Create 15 published blogs
        for i in range(15):
            TripBlog.objects.create(
                user=self.user,
                title=f'Story {i}',
                destination=f'Dest {i}',
                content=f'Story content {i}',
                published=True
            )

        res_page1 = self.client.get('/api/community/blogs/?page=1')
        assert res_page1.status_code == status.HTTP_200_OK
        assert res_page1.data['count'] == 15
        assert len(res_page1.data['blogs']) == 10
        assert res_page1.data['next'] is not None

        res_page2 = self.client.get('/api/community/blogs/?page=2')
        assert res_page2.status_code == status.HTTP_200_OK
        assert len(res_page2.data['blogs']) == 5
        assert res_page2.data['next'] is None

    # ---- Authentication / Permission Failures ----
    def test_unauthenticated_permission_failures(self):
        # Unauthenticated add review
        res_review = self.client.post('/api/community/reviews/add/', {'destination_name': 'Goa', 'rating': 5, 'title': 'T', 'content': 'C'}, format='json')
        assert res_review.status_code == status.HTTP_401_UNAUTHORIZED

        # Unauthenticated vote helpful
        res_helpful = self.client.post('/api/community/reviews/1/helpful/')
        assert res_helpful.status_code == status.HTTP_401_UNAUTHORIZED

        # Unauthenticated create blog
        res_blog = self.client.post('/api/community/blogs/create/', {'title': 'T', 'destination': 'D', 'content': 'C'}, format='json')
        assert res_blog.status_code == status.HTTP_401_UNAUTHORIZED

        # Unauthenticated like blog
        res_like = self.client.post('/api/community/blogs/1/like/')
        assert res_like.status_code == status.HTTP_401_UNAUTHORIZED
