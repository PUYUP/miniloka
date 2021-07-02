
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .inquiry.views import InquiryApiView
from .propose.views import ProposeApiView
from .offer.views import OfferApiView
from .listing.views import ListingApiView
from .order.views import OrderApiView
from .product.views import ProductApiView

# Create a router and register our viewsets with it.
router = DefaultRouter(trailing_slash=True)
router.register('inquiries', InquiryApiView, basename='inquiry')
router.register('proposes', ProposeApiView, basename='propose')
router.register('offers', OfferApiView, basename='offer')
router.register('listings', ListingApiView, basename='listing')
router.register('orders', OrderApiView, basename='order')
router.register('products', ProductApiView, basename='product')

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('', include((router.urls))),
]
