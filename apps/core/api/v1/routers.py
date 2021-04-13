from django.urls import path

# LOCAL
from .generator.views import CsrfTokenApiView


# The API URLs are now determined automatically by the router.
urlpatterns = [
    path('csrf/', CsrfTokenApiView.as_view(), name='csrf'),
]
