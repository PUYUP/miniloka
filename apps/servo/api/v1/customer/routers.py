from django.urls import path, include

# THIRD PARTY
from rest_framework.routers import DefaultRouter

# LOCAL
from .need.views import NeedApiView
from .offer.views import OfferApiView
from .offer_rate.views import OfferRateApiView

# Create a router and register our viewsets with it.
router = DefaultRouter(trailing_slash=True)
router.register('needs', NeedApiView, basename='need')
router.register('offers', OfferApiView, basename='offer')
router.register('offer-rates', OfferRateApiView, basename='offer_rate')

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include((router.urls))),
]
