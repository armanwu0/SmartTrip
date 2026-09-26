from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    # Original API
    path('api/', include('recommendations.urls')),
    path('api/trips/', include('trips.urls')),
    # New APIs
    path('api/auth/', include('accounts.urls')),
    path('api/community/', include('community.urls')),
]
