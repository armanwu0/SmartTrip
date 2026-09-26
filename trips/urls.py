from django.urls import path
from .views import (
    trip_list_create, trip_detail,
    itinerary_list_create, itinerary_item_update_delete,
    trip_expenses, add_expense, expense_update_delete,
    trip_routes, ai_conversations,
    saved_trip_list_create, saved_trip_delete,
    dashboard_summary,
)

urlpatterns = [
    path('', trip_list_create, name='trip-list-create'),
    path('<int:pk>/', trip_detail, name='trip-detail'),
    path('<int:trip_id>/itinerary/', itinerary_list_create, name='trip-itinerary'),
    path('itinerary-items/<int:pk>/', itinerary_item_update_delete, name='itinerary-item-detail'),
    path('<int:trip_id>/expenses/', trip_expenses, name='trip-expenses'),
    path('<int:trip_id>/expenses/add/', add_expense, name='add-expense'),
    path('expenses/<int:pk>/', expense_update_delete, name='expense-detail'),
    path('<int:trip_id>/routes/', trip_routes, name='trip-routes'),
    path('ai/conversations/', ai_conversations, name='ai-conversations'),
    path('saved-trips/', saved_trip_list_create, name='saved-trips'),
    path('saved-trips/<int:pk>/', saved_trip_delete, name='saved-trip-delete'),
    path('dashboard/', dashboard_summary, name='trip-dashboard'),
]
