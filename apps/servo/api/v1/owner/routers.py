from django.urls import path, include

# THIRD PARTY
from rest_framework.routers import DefaultRouter

# LOCAL
from .listing.views import ListingApiView

# Create a router and register our viewsets with it.
router = DefaultRouter(trailing_slash=True)
router.register('listings', ListingApiView, basename='listing')

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include((router.urls))),
]
