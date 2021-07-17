
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .notification.views import NotificationApiView

# Create a router and register our viewsets with it.
router = DefaultRouter(trailing_slash=True)
router.register('notifications', NotificationApiView, basename='notification')

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include((router.urls))),
]
