from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('me/', views.me_view, name='me'),
    path('profile/', views.profile_view, name='profile'),
    path('saved-trips/', views.saved_trips_view, name='saved-trips'),
    path('saved-trips/<int:trip_id>/', views.saved_trip_detail, name='saved-trip-detail'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/<int:item_id>/', views.wishlist_remove, name='wishlist-remove'),
]

