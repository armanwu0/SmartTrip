import pytest
from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework import status
from accounts.models import UserProfile, SavedTrip, WishlistItem


@pytest.mark.django_db
class TestAccountsApp:
    def setup_method(self):
        self.client = APIClient()
        self.user_data = {
            'username': 'arman',
            'email': 'arman@example.com',
            'first_name': 'Arman',
            'last_name': 'Ansari',
            'password': 'password123',
            'password2': 'password123'
        }

    # ---- Registration Tests ----
    def test_registration_success(self):
        response = self.client.post('/api/auth/register/', self.user_data, format='json')
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['success'] is True
        assert 'access' in response.data
        assert 'refresh' in response.data
        assert response.data['user']['username'] == 'arman'
        assert User.objects.filter(username='arman').exists()

    def test_registration_validation_failure_password_mismatch(self):
        invalid_data = self.user_data.copy()
        invalid_data['password2'] = 'mismatch123'
        response = self.client.post('/api/auth/register/', invalid_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False
        assert 'password' in response.data['errors']

    def test_registration_validation_failure_duplicate_email(self):
        User.objects.create_user(username='other', email='arman@example.com', password='password123')
        response = self.client.post('/api/auth/register/', self.user_data, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False
        assert 'email' in response.data['errors']

    # ---- Login Tests ----
    def test_jwt_login_success(self):
        User.objects.create_user(username='arman', password='password123')
        response = self.client.post('/api/auth/login/', {'username': 'arman', 'password': 'password123'}, format='json')
        assert response.status_code == status.HTTP_200_OK
        assert response.data['success'] is True
        assert 'access' in response.data
        assert 'refresh' in response.data

    def test_invalid_login(self):
        User.objects.create_user(username='arman', password='password123')
        response = self.client.post('/api/auth/login/', {'username': 'arman', 'password': 'wrongpassword'}, format='json')
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data['success'] is False

    # ---- Profile Tests ----
    def test_authenticated_profile_access(self):
        user = User.objects.create_user(username='arman', password='password123', first_name='Arman')
        UserProfile.objects.create(user=user, location='Mumbai')
        self.client.force_authenticate(user=user)

        res_me = self.client.get('/api/auth/me/')
        assert res_me.status_code == status.HTTP_200_OK
        assert res_me.data['user']['username'] == 'arman'

        res_profile = self.client.get('/api/auth/profile/')
        assert res_profile.status_code == status.HTTP_200_OK
        assert res_profile.data['user']['profile']['location'] == 'Mumbai'

    def test_unauthenticated_profile_access(self):
        res_me = self.client.get('/api/auth/me/')
        assert res_me.status_code == status.HTTP_401_UNAUTHORIZED

        res_profile = self.client.get('/api/auth/profile/')
        assert res_profile.status_code == status.HTTP_401_UNAUTHORIZED

    def test_profile_update_validation_success(self):
        user = User.objects.create_user(username='arman', email='arman@example.com', password='password123')
        UserProfile.objects.create(user=user, location='Mumbai')
        self.client.force_authenticate(user=user)

        payload = {
            'first_name': 'NewFirst',
            'last_name': 'NewLast',
            'email': 'new_arman@example.com',
            'profile': {'bio': 'Developer', 'location': 'Delhi'}
        }
        res = self.client.put('/api/auth/profile/', payload, format='json')
        assert res.status_code == status.HTTP_200_OK
        assert res.data['user']['first_name'] == 'NewFirst'
        assert res.data['user']['profile']['location'] == 'Delhi'

    def test_profile_update_duplicate_email_failure(self):
        User.objects.create_user(username='other', email='other@example.com', password='password123')
        user = User.objects.create_user(username='arman', email='arman@example.com', password='password123')
        self.client.force_authenticate(user=user)

        payload = {'email': 'other@example.com'}
        res = self.client.put('/api/auth/profile/', payload, format='json')
        assert res.status_code == status.HTTP_400_BAD_REQUEST
        assert 'email' in res.data['errors']

    def test_profile_update_protected_fields_immutability(self):
        user = User.objects.create_user(username='arman', password='password123')
        profile = UserProfile.objects.create(user=user, travel_count=2)
        self.client.force_authenticate(user=user)

        payload = {
            'username': 'hacked_name',
            'is_superuser': True,
            'is_staff': True,
            'profile': {'travel_count': 9999}
        }
        res = self.client.put('/api/auth/profile/', payload, format='json')
        assert res.status_code == status.HTTP_200_OK

        user.refresh_from_db()
        profile.refresh_from_db()
        assert user.username == 'arman'
        assert user.is_superuser is False
        assert user.is_staff is False
        assert profile.travel_count == 2

    # ---- Saved Trips Tests ----
    def test_saved_trips_get_and_post(self):
        user = User.objects.create_user(username='arman', password='password123')
        self.client.force_authenticate(user=user)

        # GET empty trips list
        res_get = self.client.get('/api/auth/saved-trips/')
        assert res_get.status_code == status.HTTP_200_OK
        assert len(res_get.data['trips']) == 0

        # POST new trip
        trip_payload = {
            'destination_name': 'Manali',
            'country': 'India',
            'summary': 'Mountain trip',
            'estimated_cost': '₹20000',
            'best_time': 'Oct-Jun'
        }
        res_post = self.client.post('/api/auth/saved-trips/', trip_payload, format='json')
        assert res_post.status_code == status.HTTP_201_CREATED
        assert res_post.data['success'] is True
        assert res_post.data['trip']['destination_name'] == 'Manali'
        assert SavedTrip.objects.filter(user=user).count() == 1

    def test_saved_trip_detail_put_and_delete(self):
        user = User.objects.create_user(username='arman', password='password123')
        trip = SavedTrip.objects.create(user=user, destination_name='Goa', country='India')
        self.client.force_authenticate(user=user)

        # PUT update completion
        res_put = self.client.put(f'/api/auth/saved-trips/{trip.id}/', {'is_completed': True}, format='json')
        assert res_put.status_code == status.HTTP_200_OK
        assert res_put.data['trip']['is_completed'] is True

        # DELETE trip
        res_del = self.client.delete(f'/api/auth/saved-trips/{trip.id}/')
        assert res_del.status_code == status.HTTP_200_OK
        assert SavedTrip.objects.filter(id=trip.id).exists() is False

    def test_saved_trips_unauthenticated(self):
        res = self.client.get('/api/auth/saved-trips/')
        assert res.status_code == status.HTTP_401_UNAUTHORIZED

    # ---- Wishlist Tests ----
    def test_wishlist_get_and_post(self):
        user = User.objects.create_user(username='arman', password='password123')
        self.client.force_authenticate(user=user)

        # GET empty wishlist
        res_get = self.client.get('/api/auth/wishlist/')
        assert res_get.status_code == status.HTTP_200_OK
        assert len(res_get.data['wishlist']) == 0

        # POST add to wishlist
        res_post = self.client.post('/api/auth/wishlist/', {'destination_name': 'Bali', 'country': 'Indonesia'}, format='json')
        assert res_post.status_code == status.HTTP_201_CREATED
        assert res_post.data['created'] is True
        assert WishlistItem.objects.filter(user=user, destination_name='Bali').exists()

    def test_wishlist_delete(self):
        user = User.objects.create_user(username='arman', password='password123')
        item = WishlistItem.objects.create(user=user, destination_name='Tokyo', country='Japan')
        self.client.force_authenticate(user=user)

        res_del = self.client.delete(f'/api/auth/wishlist/{item.id}/')
        assert res_del.status_code == status.HTTP_200_OK
        assert WishlistItem.objects.filter(id=item.id).exists() is False

    def test_wishlist_unauthenticated(self):
        res = self.client.get('/api/auth/wishlist/')
        assert res.status_code == status.HTTP_401_UNAUTHORIZED
